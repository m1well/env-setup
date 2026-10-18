"""Correctness patterns a regex can pin down: time zones, seeds, unused limits, native updates."""
from __future__ import annotations

import datetime as dt
import os
import re
from collections import defaultdict
from functools import lru_cache

from . import jvm
from .core import balanced, define, is_test_path, profile_kind, split_top
from .extract import entity as entity_x

define('SB-DST-DURATION', 'Duration between LocalDateTime values in a zone with daylight saving time', 'medium',
       'correctness',
       'A hit needs LocalDateTime on both sides and a clock or default zone with DST: across the switch the '
       'difference is an hour off (and negative inside the repeated hour). Fine when only the wall-clock '
       'distance matters (nearest day, display); a finding for elapsed time - race or session clock, timeout, '
       'billing. Fix: Instant (or ZonedDateTime) for points in time, LocalDateTime only for display.')
define('SEED-INSERT-ONLY', 'Startup seed inserts a row only when it is missing', 'medium', 'correctness',
       'A runner, startup listener or @PostConstruct does find-or-insert: a corrected value in the seed never '
       'reaches an existing database, and a row deleted in the database comes back on the next start. Fine for '
       'demo data on a dev profile. Fix: an upsert (Flyway repeatable migration with ON CONFLICT ... DO UPDATE) '
       'or update the found row.')
define('SB-LIMIT-UNUSED', 'Limit constant that no code reads', 'low', 'correctness',
       'A MAX/MIN/LIMIT constant read nowhere in main code (annotations included) - the validation it was '
       'written for is missing. Check the request path for the field: missing means a 500 from the database '
       'or unbounded input instead of a field error.')
define('DB-NATIVE-COUNTER-OVERWRITE', 'Bulk counter update on a column the entity writes back', 'high',
       'correctness',
       'An @Modifying update sets x = x + :n past the persistence context and does not bump @Version. An entity '
       'loaded before it writes its stale x back on its next flush - Hibernate updates every updatable column, '
       'val or var. A finding unless the column is @Column(updatable = false), the statement bumps the version, '
       'or the entity is never saved after load.')

TIME = {'LocalDateTime', 'LocalDate', 'LocalTime', 'Instant', 'ZonedDateTime', 'OffsetDateTime', 'Duration',
        'ZoneId', 'Clock', 'OffsetTime', 'Year', 'YearMonth'}
ZONED = {'Instant', 'ZonedDateTime', 'OffsetDateTime'}
CONVERT = {'toLocalDateTime': 'LocalDateTime', 'toInstant': 'Instant', 'toLocalDate': 'LocalDate',
           'toLocalTime': 'LocalTime', 'atZone': 'ZonedDateTime', 'atOffset': 'OffsetDateTime',
           'atDate': 'LocalDateTime', 'toOffsetDateTime': 'OffsetDateTime', 'toZonedDateTime': 'ZonedDateTime'}
FACTORY = re.compile(r'(now|of|parse|ofInstant|from|ofEpoch\w*|MIN|MAX|EPOCH)$')
SAME = re.compile(r'(plus|minus|with|truncatedTo)\w*$')
TIME_UNIT = r'(?:NANOS|MICROS|MILLIS|SECONDS|MINUTES|HOURS|HALF_DAYS)'
DURATION_CALL = re.compile(r'\bDuration\s*\.\s*between\s*\(|\b(?:ChronoUnit\s*\.\s*)?' + TIME_UNIT +
                           r'\s*\.\s*between\s*\(|\.\s*until\s*\(')
ZONE_LIT = re.compile(r'ZoneId\s*\.\s*of\s*\(\s*"([^"]+)"|TimeZone\s*\.\s*getTimeZone\s*\(\s*"([^"]+)"')
ZONE_CONST = re.compile(r'\b(?:val|var)\s+(\w+)\s*(?::\s*ZoneId\??)?\s*=\s*ZoneId\s*\.\s*of\s*\(\s*"([^"]+)"|'
                        r'\bZoneId\s+(\w+)\s*=\s*ZoneId\s*\.\s*of\s*\(\s*"([^"]+)"')
DEFAULT_ZONE = re.compile(r'\bLocalDateTime\s*\.\s*now\s*\(\s*\)|ZoneId\s*\.\s*systemDefault\s*\(|'
                          r'Clock\s*\.\s*systemDefaultZone\s*\(|TimeZone\s*\.\s*getDefault\s*\(')
JVM_IMAGE = re.compile(r'(?i)jdk|jre|temurin|corretto|zulu|liberica|openjdk|distroless/java|semeru|\.jar\b')
TZ_DOCKER = re.compile(r'(?m)^\s*ENV\s+(?:[\w.-]+=\S+\s+)*TZ[=\s]+"?([\w/+-]+)|/usr/share/zoneinfo/([\w/+-]+)\s+/etc/localtime')
TZ_ENV = re.compile(r'(?m)^\s*-?\s*"?TZ"?\s*[:=]\s*"?([\w/+-]+)|name:\s*"?TZ"?\s*\n\s*value:\s*"?([\w/+-]+)')
USER_TZ = re.compile(r'-Duser\.timezone=([\w/+-]+)')

SEED_IFACE = re.compile(r'\b(ApplicationRunner|CommandLineRunner|InitializingBean|SmartInitializingSingleton|'
                        r'ApplicationListener\s*<\s*(?:[\w.]+\.)?(?:ApplicationReadyEvent|ApplicationStartedEvent|'
                        r'ContextRefreshedEvent)\s*>)')
SEED_ENTRY = {'run', 'onApplicationEvent', 'afterPropertiesSet', 'afterSingletonsInstantiated'}
STARTUP_EVENT = re.compile(r'ApplicationReadyEvent|ApplicationStartedEvent|ContextRefreshedEvent')
LOOKUP = re.compile(r'\b(\w+)\s*(?:\?\.|\.)\s*((?:find|get|exists|count|load|read|search)\w*)\s*\(')
NULL_ADAPTER = re.compile(r'\s*(?:\?\.|\.)\s*(?:orElse\s*\(\s*null\s*\)|orElseNull\s*\(\s*\)|getOrNull\s*\(\s*\)|'
                          r'firstOrNull\s*\(\s*\)|singleOrNull\s*\(\s*\))')
REPO_TYPE = re.compile(r'(Repository|Repo|Dao)$')
LIMIT_NAME = re.compile(r'^(?:[A-Z0-9_]+_)?(?:MAX|MIN|LIMIT)(?:_[A-Z0-9_]+)?$')
KT_CONST = re.compile(r'\bconst\s+val\s+([A-Z][A-Z0-9_]*)\b')
JAVA_CONST = re.compile(r'\bstatic\s+final\s+(?:int|long|short|byte|double|float|Integer|Long|Short|Double|Float)\s+'
                        r'([A-Z][A-Z0-9_]*)\s*=|\bfinal\s+static\s+(?:int|long|short|Integer|Long)\s+([A-Z][A-Z0-9_]*)\s*=')
UPDATE_SQL = re.compile(r'(?is)\bupdate\s+(versioned\s+)?(?:only\s+)?([\w."`]+)(?:\s+(?:as\s+)?(?!set\b)(\w+))?\s+set\s+'
                        r'(.+?)(?=\s+where\b|\s+returning\b|\s+from\b|$)')
STRINGS = re.compile(r'"""([\s\S]*?)"""|"((?:\\.|[^"\\\n])*)"')
SEGMENT = re.compile(r'\s*(\w+)(\s*\()?')
SEPARATOR = re.compile(r'\s*(?:!!)?\s*(\?\.|\.)')


def _base(t: str | None) -> str | None:
    if not t:
        return None
    t = re.sub(r'\s+', '', t).rstrip('?!')
    return re.sub(r'<.*', '', t).split('.')[-1] or None


def _chain(expr: str) -> list[tuple[str, str | None]] | None:
    expr = re.sub(r'^\s*(?:new\s+|this\s*\.\s*)', '', expr.strip())
    segs, i = [], 0
    while True:
        m = SEGMENT.match(expr, i)
        if not m:
            return None
        args, i = None, m.end()
        if m.group(2):
            close = balanced(expr, i - 1)
            if close < 0:
                return None
            args, i = expr[i:close], close + 1
        segs.append((m.group(1), args))
        sep = SEPARATOR.match(expr, i)
        if not sep:
            return segs if not expr[i:].replace('!!', '').strip() else None
        i = sep.end()


class Types:
    def __init__(self, ctx):
        self.classes = defaultdict(list)
        for j in ctx.main:
            for c in j.classes:
                self.classes[c.name].append((j, c))
        self._members: dict[str, tuple[dict, dict]] = {}

    def members(self, name: str) -> tuple[dict, dict]:
        if name not in self._members:
            props, methods = {}, {}
            for j, c in self.classes.get(name, []):
                for p in c.params:
                    props[p.name] = (p.type, j, None)
                for m in j.members:
                    if m.owner is not c:
                        continue
                    if m.kind == 'field':
                        init = re.search(r'=\s*(.+)$', m.sig)
                        props[m.name] = (m.returns, j, init.group(1) if init and not m.returns else None)
                    elif m.kind == 'method':
                        expr = j.body_text(m)
                        methods[m.name] = (m.returns, j, expr[1:] if j.kotlin and m.returns == 'Unit'
                                           and expr.startswith('=') else None)
            self._members[name] = (props, methods)
        return self._members[name]

    def _decl(self, decl, depth) -> str | None:
        declared, j, expr = decl
        if expr:
            return self.expr(expr, (j, None, 0), depth + 1)
        return _base(declared)

    def name(self, name: str, scope, depth: int) -> str | None:
        j, method, offset = scope
        if method is not None and method.body:
            before = j.src.bare[method.body[0]:offset]
            local = None
            if j.kotlin:
                for local in re.finditer(r'\b(?:val|var)\s+' + name + r'\s*(?::\s*([\w.<>?, ]+?))?\s*=\s*([^\n;]+)',
                                         before):
                    pass
            else:
                for local in re.finditer(r'(?:^|[;{(\s])([\w.<>\[\]]+)\s+' + name + r'\s*=\s*([^;]+);', before):
                    pass
            if local:
                declared = local.group(1)
                if declared and declared != 'var':
                    return _base(declared)
                return self.expr(local.group(2), scope, depth + 1)
            for p in method.params:
                if p.name == name:
                    return _base(p.type)
        owner = method.owner if method is not None else None
        if owner is not None:
            props, _ = self.members(owner.name)
            if name in props:
                return self._decl(props[name], depth)
        for m in j.members:
            if m.kind == 'field' and m.owner is None and m.name == name:
                init = re.search(r'=\s*(.+)$', m.sig)
                return _base(m.returns) or (self.expr(init.group(1), (j, None, 0), depth + 1) if init else None)
        return name if name in self.classes or name in TIME else None

    def member(self, t: str, name: str, args: str | None, depth: int) -> str | None:
        if t in TIME:
            if name in CONVERT:
                return CONVERT[name]
            if name == 'atStartOfDay':
                return 'LocalDateTime' if not (args or '').strip() else 'ZonedDateTime'
            if name == 'atTime' and t == 'LocalDate':
                return 'LocalDateTime'
            if SAME.match(name) and args is not None:
                return t
            if FACTORY.match(name):
                return t
            return None
        props, methods = self.members(t)
        if args is None and name in props:
            return self._decl(props[name], depth)
        if args is not None and name in methods:
            return self._decl(methods[name], depth)
        getter = re.fullmatch(r'(?:get|is)([A-Z]\w*)', name)
        if args is not None and not args.strip() and getter:
            prop = getter.group(1)[0].lower() + getter.group(1)[1:]
            if prop in props:
                return self._decl(props[prop], depth)
        if args is not None and not args.strip() and name in props:
            return self._decl(props[name], depth)
        return None

    def expr(self, expr: str, scope, depth: int = 0) -> str | None:
        if depth > 5:
            return None
        segs = _chain(expr)
        if not segs:
            return None
        (first, args), rest = segs[0], segs[1:]
        if args is None:
            t = self.name(first, scope, depth)
        elif first in self.classes or first in TIME:
            t = first
        else:
            j, method, _ = scope
            owner = method.owner if method is not None else None
            _, methods = self.members(owner.name) if owner is not None else ({}, {})
            t = self._decl(methods[first], depth) if first in methods else None
        for name, a in rest:
            if t is None:
                return None
            t = self.member(t, name, a, depth)
        return t


def _method_at(j, offset: int):
    inside = [m for m in j.members if m.kind == 'method' and m.body and m.body[0] <= offset <= m.body[1]]
    return max(inside, key=lambda m: m.body[0]) if inside else None


def _receiver(bare: str, dot: int) -> str:
    i = dot
    while i > 0:
        ch = bare[i - 1]
        if ch == ')':
            depth = 0
            while i > 0:
                i -= 1
                depth += {')': 1, '(': -1}.get(bare[i], 0)
                if depth == 0:
                    break
        elif ch.isalnum() or ch in '_.?!':
            i -= 1
        else:
            break
    return bare[i:dot].strip()


@lru_cache(maxsize=None)
def _next_switch(zone: str) -> str | None:
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(zone)
    except Exception:
        return None
    start = dt.datetime.combine(dt.date.today(), dt.time(), tzinfo=dt.timezone.utc)
    before = start.astimezone(tz).utcoffset()
    for hour in range(1, 24 * 400):
        t = start + dt.timedelta(hours=hour)
        after = t.astimezone(tz).utcoffset()
        if after != before:
            old, new = t.astimezone(dt.timezone(before)), t.astimezone(tz)
            return f'{old:%Y-%m-%d %H:%M} -> {new:%H:%M}'
    return None


def _roots(ctx) -> list[str]:
    roots = {os.path.dirname(f) for f in ctx.repo.files
             if os.path.basename(f) in ('settings.gradle', 'settings.gradle.kts', 'pom.xml')}
    return sorted(roots, key=len)


def _scope(roots: list[str], rel: str) -> str:
    best = ''
    for r in roots:
        if r and (rel == r or rel.startswith(r + '/')) and (not best or len(r) < len(best)):
            best = r
    return best


def _deploy_zones(ctx, roots) -> dict[str, list[tuple[str, str]]]:
    out = defaultdict(list)
    for rel in ctx.repo.files:
        name = os.path.basename(rel)
        docker = re.match(r'(Dockerfile|Containerfile)', name)
        compose = re.search(r'compose[\w.-]*\.ya?ml$', name)
        other = name.endswith(('.yml', '.yaml', '.gradle', '.kts', '.xml', '.sh', '.env', '.conf')) or \
            name.startswith('.env')
        if not (docker or compose or other) or is_test_path(rel):
            continue
        text = ctx.repo.source(rel).code
        build = name.endswith(('.gradle', '.kts', '.xml'))
        found = [(m.group(1), m.start()) for m in USER_TZ.finditer(text)
                 if not build or re.search(r'jvmFlags?', text[max(0, m.start() - 300):m.start()])]
        if docker and JVM_IMAGE.search(text):
            found += [(m.group(1) or m.group(2), m.start()) for m in TZ_DOCKER.finditer(text)]
        if compose or (other and name.endswith(('.yml', '.yaml'))):
            for m in TZ_ENV.finditer(text):
                block, scope = _service_block(text, m.start()), None
                if compose and not re.search(r'\bbuild\s*:|SPRING_|JAVA_|\.jar\b', block):
                    continue
                if not compose and not re.search(r'kind:\s*(Deployment|StatefulSet|Job|CronJob)', text):
                    continue
                ctxt = re.search(r'\bbuild\s*:\s*(?:\n\s*context\s*:\s*)?["\']?([\w./-]+)', block)
                if ctxt:
                    scope = _scope(roots, os.path.normpath(os.path.join(os.path.dirname(rel), ctxt.group(1))))
                out[scope if scope is not None else _scope(roots, rel)].append(
                    (m.group(1) or m.group(2), f'{rel}:{ctx.repo.source(rel).line_at(m.start())}'))
        for zone, at in found:
            out[_scope(roots, rel)].append((zone, f'{rel}:{ctx.repo.source(rel).line_at(at)}'))
    return out


def _service_block(text: str, at: int) -> str:
    starts = [m.start() for m in re.finditer(r'(?m)^  [\w.-]+\s*:\s*$', text)]
    start = max([s for s in starts if s <= at], default=0)
    end = min([s for s in starts if s > at], default=len(text))
    return text[start:end]


def _code_zones(ctx, roots) -> tuple[dict, set]:
    consts = {}
    for j in ctx.main:
        for m in ZONE_CONST.finditer(j.src.code):
            consts[m.group(1) or m.group(3)] = m.group(2) or m.group(4)

    def zone_of(text: str) -> str | None:
        lit = ZONE_LIT.search(text)
        if lit:
            return lit.group(1) or lit.group(2)
        name = next((n for n in re.findall(r'\b\w+\b', text) if n in consts), None)
        return consts[name] if name else None

    zones, default_used = defaultdict(list), set()
    for j in ctx.main:
        code = j.src.code
        scope = _scope(roots, j.rel)
        if DEFAULT_ZONE.search(j.src.bare):
            default_used.add(scope)
        sources = []
        for m in re.finditer(r'\bClock\s*\.\s*system\s*\(|TimeZone\s*\.\s*setDefault\s*\(|'
                             r'\bLocalDateTime\s*\.\s*(?:now|ofInstant)\s*\(', code):
            close = balanced(j.src.bare, m.end() - 1)
            sources.append((code[m.end():close if close > 0 else m.end() + 200], m.start()))
        for m in re.finditer(r'\.\s*(?:atZone|withZoneSameInstant)\s*\(([^()]*(?:\([^()]*\))?[^()]*)\)\s*'
                             r'(?:\.\s*\w+\s*\([^()]*\)\s*)*?\.\s*toLocalDateTime\s*\(|'
                             r'ZonedDateTime\s*\.\s*now\s*\(([^()]*(?:\([^()]*\))?)\)\s*\.\s*toLocalDateTime', code):
            sources.append((m.group(1) or m.group(2) or '', m.start()))
        for m in j.members:
            if m.kind == 'method' and m.has('Bean') and _base(m.returns) in ('ZoneId', 'Clock', 'TimeZone'):
                sources.append((j.body_text(m, 'code'), m.offset))
        for text, at in sources:
            zone = zone_of(text)
            if zone:
                zones[scope].append((zone, f'{j.rel}:{j.src.line_at(at)}'))
    return zones, default_used


def _zones(ctx) -> tuple[dict[str, list[tuple[str, str, str]]], list[str]]:
    roots = _roots(ctx)
    zones, default_used = _code_zones(ctx, roots)
    for scope, found in _deploy_zones(ctx, roots).items():
        for d in default_used:
            if d == scope or d.startswith(scope + '/') or not scope:
                zones[d] += found
    out = {}
    for scope, found in zones.items():
        seen = []
        for zone, where in found:
            switch = _next_switch(zone)
            if switch and zone not in [z for z, _, _ in seen]:
                seen.append((zone, where, switch))
        if seen:
            out[scope] = seen
    return out, roots


def dst_durations(ctx, types: Types) -> None:
    zones, roots = _zones(ctx)
    if not zones:
        return
    for j in ctx.main:
        bare = j.src.bare
        if not DURATION_CALL.search(bare):
            continue
        scope = _scope(roots, j.rel)
        found = next((z for s, z in zones.items() if s == scope or scope.startswith(s + '/') or not s), None)
        if not found:
            continue
        for m in DURATION_CALL.finditer(bare):
            open_at = m.end() - 1
            close = balanced(bare, open_at)
            if close < 0:
                continue
            args = [a for _, a in split_top(bare[open_at + 1:close])]
            method = _method_at(j, m.start())
            where = (j, method, m.start())
            if m.group().lstrip('.').lstrip().startswith('until'):
                if len(args) != 2 or not re.search(r'\b' + TIME_UNIT + r'\b', args[1]):
                    continue
                args = [_receiver(bare, m.start()), args[0]]
            if len(args) != 2:
                continue
            kinds = [types.expr(a, where) for a in args]
            if 'LocalDateTime' not in kinds or ZONED & set(kinds):
                continue
            zone, src, switch = found[0]
            ctx.hit('SB-DST-DURATION', j, m.start(), zone=zone, note=f'{zone} from {src}, next DST switch {switch}')


def _profile_dev(*anno_codes: str) -> bool:
    for code in anno_codes:
        m = re.search(r'@Profile\s*\(([^)]*)\)', code or '')
        if m:
            names = re.findall(r'"([^"]+)"', m.group(1))
            return bool(names) and all(profile_kind(n) == 'dev' for n in names)
    return False


def _seed_methods(j) -> list:
    out = []
    for c in j.classes:
        methods = j.methods(c)
        entries = []
        if SEED_IFACE.search(c.header):
            entries += [m for m in methods if m.name in SEED_ENTRY]
        for m in methods:
            if m.has('PostConstruct'):
                entries.append(m)
            elif m.has('EventListener') and (STARTUP_EVENT.search(m.anno_code) or
                                             any(STARTUP_EVENT.search(p.type) for p in m.params)):
                entries.append(m)
            elif m.has('Bean') and re.search(r'ApplicationRunner|CommandLineRunner', m.returns + j.body_text(m)[:80]):
                entries.append(m)
        if not entries:
            continue
        names = {m.name: m for m in methods}
        todo, seen = list(entries), {id(m) for m in entries}
        while todo:
            m = todo.pop()
            out.append((c, m, entries))
            for called in re.findall(r'\b(\w+)\s*\(', j.body_text(m)):
                callee = names.get(called)
                if callee is not None and id(callee) not in seen:
                    seen.add(id(callee))
                    todo.append(callee)
    return out


def _block(bare: str, i: int) -> tuple[str, int]:
    i += len(bare[i:]) - len(bare[i:].lstrip())
    if bare[i:i + 1] == '{':
        end = balanced(bare, i, '{', '}')
        end = end if end > 0 else len(bare)
        return bare[i:end + 1], end + 1
    run = re.match(r'(?:\w+\s*\.\s*)?(?:run|let|also|apply)\s*\{', bare[i:])
    if run:
        end = balanced(bare, i + run.end() - 1, '{', '}')
        end = end if end > 0 else len(bare)
        return bare[i:end + 1], end + 1
    end = i
    depth = 0
    while end < len(bare):
        ch = bare[end]
        depth += {'(': 1, '{': 1, ')': -1, '}': -1}.get(ch, 0)
        if depth < 0 or (depth == 0 and ch in ';\n' and not re.match(r'\s*(\.|\?\.)', bare[end + 1:end + 40])):
            break
        end += 1
    return bare[i:end], end


def _saves(text: str, recv: str) -> re.Match | None:
    return re.search(r'\b' + recv + r'\s*(?:\?\.|\.)\s*((?:save|saveAndFlush|saveAll|persist|insert)\w*)\s*\(', text)


def _conditional(bare: str, recv: str, kind: str, if_open: int, subject_end: int, negated: bool,
                 end_of_body: int) -> str | None:
    if_close = balanced(bare, if_open)
    if if_close < 0:
        return None
    test = bare[subject_end:if_close]
    if kind == 'exists':
        missing = negated
    elif kind == 'count':
        missing = bool(re.match(r'\s*(==\s*0L?|<\s*1L?)\b', test))
        if not missing and not re.match(r'\s*(>\s*0L?|!=\s*0L?)\b', test):
            return None
    else:
        missing = bool(re.match(r'\s*(==\s*null|\.\s*isEmpty\b)', test)) or \
            (negated and bool(re.match(r'\s*\.\s*isPresent\b', test)))
        if not missing and not re.match(r'\s*(!=\s*null|\.\s*isPresent\b)', test):
            return None
    then, after = _block(bare, if_close + 1)
    if missing:
        if re.match(r'\s*else\b', bare[after:after + 20]):
            return None
        return 'if missing' if _saves(then, recv) else None
    if re.fullmatch(r'\s*\{?\s*(return(@\w+)?|continue)\s*;?\s*\}?\s*', then):
        return 'if present return' if _saves(bare[after:min(end_of_body, after + 800)], recv) else None
    return None


def _insert_only(bare: str, recv: str, kind: str, call_at: int, close: int, end_of_body: int) -> str | None:
    i = close + 1
    adapter = NULL_ADAPTER.match(bare, i)
    while adapter:
        i = adapter.end()
        adapter = NULL_ADAPTER.match(bare, i)
    tail = bare[i:end_of_body]
    elvis = re.match(r'\s*\?:\s*', tail)
    if elvis and kind != 'exists':
        block, _ = _block(bare, i + elvis.end())
        return '?:' if _saves(block, recv) else None
    orelse = re.match(r'\s*\.\s*(orElseGet|orElse)\s*([({])', tail)
    if orelse and kind != 'exists':
        open_at = i + orelse.end() - 1
        end = balanced(bare, open_at, orelse.group(2), ')' if orelse.group(2) == '(' else '}')
        return orelse.group(1) if _saves(bare[open_at:end + 1], recv) else None
    head = bare[max(0, call_at - 80):call_at]
    cond = re.search(r'\bif\s*\(\s*(!\s*)?$', head)
    if cond:
        return _conditional(bare, recv, kind, call_at - len(head) + head.rfind('(', 0, cond.end()), i,
                            bool(cond.group(1)), end_of_body)
    assign = re.search(r'\b(?:val|var)\s+(\w+)\s*(?::\s*[\w.<>?]+)?\s*=\s*$|[\w>]\s+(\w+)\s*=\s*$', head)
    if not assign or kind == 'count':
        return None
    name = assign.group(1) or assign.group(2)
    if len(re.findall(r'\b' + name + r'\b', tail)) != 1:
        return None
    used = re.search(r'\bif\s*\(\s*(!\s*)?' + name + r'\b', tail)
    if used:
        return _conditional(bare, recv, kind, i + used.start() + used.group().index('('), i + used.end(),
                            bool(used.group(1)), end_of_body)
    elvis = re.search(r'\b' + name + r'\s*\?:\s*', tail)
    if elvis:
        block, _ = _block(bare, i + elvis.end())
        return '?:' if _saves(block, recv) else None
    return None


def seeds(ctx, types: Types) -> None:
    repo_entity = {}
    for j in ctx.main:
        for c in j.classes:
            sup = jvm.REPO_SUPER.search(c.header)
            if sup:
                generic = re.match(r'\s*([\w.]+)', c.header[sup.end():])
                repo_entity[c.name] = generic.group(1).split('.')[-1] if generic else None
    for j in ctx.main:
        found = {}
        for cls, method, entries in _seed_methods(j):
            if not method.body:
                continue
            bare = j.src.bare
            declared = {n: t for n, (t, _, _) in types.members(cls.name)[0].items()}
            declared.update((p.name, p.type) for p in method.params)
            for m in LOOKUP.finditer(bare, method.body[0], method.body[1]):
                recv, call = m.group(1), m.group(2)
                rtype = _base(declared.get(recv))
                if not (rtype and (rtype in repo_entity or REPO_TYPE.search(rtype)) or
                        re.search(r'(?i)(repo|repository|dao)$', recv)):
                    continue
                close = balanced(bare, m.end() - 1)
                if close < 0:
                    continue
                kind = 'exists' if call.startswith('exists') else 'count' if call.startswith('count') else 'find'
                form = _insert_only(bare, recv, kind, m.start(), close, method.body[1])
                if not form:
                    continue
                entity = repo_entity.get(rtype) if rtype else None
                if not entity:
                    saved = re.search(r'\b' + recv + r'\s*(?:\?\.|\.)\s*save\w*\s*\(\s*(?:new\s+)?([A-Z]\w*)\s*\(',
                                      bare[close:method.body[1]])
                    entity = saved.group(1) if saved else None
                found.setdefault(entity or recv, []).append((j.src.line_at(m.start()), m.start(), method, recv, call,
                                                             kind, form, entity, entries, cls))
        for sites in found.values():
            _, at, method, recv, call, kind, form, entity, entries, cls = min(sites, key=lambda s: s[0])
            extra = {'entity': entity} if entity else {}
            if _profile_dev(cls.anno_code, *(e.anno_code for e in entries)):
                extra.update(severity='low', note='seed runs on a dev profile only')
            lookup, save = f'{recv}.{call}(...)', f'{recv}.save(...)'
            test = {'exists': f'!{lookup}', 'count': f'{lookup} == 0'}.get(kind, f'{lookup} == null')
            shape = {'?:': f'{lookup} ?: {save}', 'if missing': f'if ({test}) {save}',
                     'if present return': f'if ({lookup}) return; {save}'}.get(
                form, f'{lookup}.{form} {{ {save} }}')
            ctx.hit('SEED-INSERT-ONLY', j, at, f'{cls.name}.{method.name}: {shape}'
                    + (f' ({len(sites)} sites)' if len(sites) > 1 else ''),
                    lines=sorted(s[0] for s in sites), **extra)


def unused_limits(ctx) -> None:
    decls = defaultdict(list)
    for j in ctx.main:
        for m in KT_CONST.finditer(j.src.bare) if j.kotlin else JAVA_CONST.finditer(j.src.bare):
            if LIMIT_NAME.match(m.group(m.lastindex)):
                decls[m.group(m.lastindex)].append((j, m.start(m.lastindex)))
    if not decls:
        return
    uses = defaultdict(int)
    word = re.compile(r'\b(' + '|'.join(sorted(decls, key=len, reverse=True)) + r')\b')
    for j in ctx.main:
        for name in word.findall(j.src.code):
            uses[name] += 1
    for name, where in decls.items():
        if uses[name] <= len(where):
            for j, at in where:
                ctx.hit('SB-LIMIT-UNUSED', j, at)


def _entity_props(types: Types, name: str, seen=None) -> list[dict]:
    seen = seen or set()
    if name in seen:
        return []
    seen.add(name)
    out = []
    for j, c in types.classes.get(name, []):
        if not (c.has('Entity') or c.has('MappedSuperclass') or c.has('Embeddable')):
            continue
        for p in c.params if j.kotlin else []:
            if re.search(r'\b(val|var)\b', p.text):
                out.append({'name': p.name, 'code': p.code, 'mutable': bool(re.search(r'\bvar\b', p.text)),
                            'annos': p.annos})
        for m in j.members:
            if m.kind == 'field' and m.owner is c and not re.search(r'\b(static|const)\b', m.sig):
                mutable = bool(re.search(r'\bvar\b', m.sig)) if j.kotlin else not re.search(r'\bfinal\b', m.sig)
                out.append({'name': m.name, 'code': m.anno_code + m.sig_code, 'mutable': mutable,
                            'annos': m.annos})
        sup = entity_x.supertypes_of(c.header.split('{')[0]) if j.kotlin else \
            re.findall(r'\bextends\s+(\w+)', c.header)
        for s in sup:
            out += _entity_props(types, s, seen)
    return out


def _column(prop: dict) -> str:
    named = re.search(r'@(?:Column|JoinColumn)\s*\([^)]*?\bname\s*=\s*"([^"]+)"', prop['code'])
    return (named.group(1) if named else entity_x.snake(prop['name'])).lower()


def counter_overwrites(ctx, types: Types, entities: list[dict] | None) -> None:
    mapped = {}
    for e in entities or []:
        mapped[(e.get('table') or '').lower()] = e.get('entity')
    for j in ctx.main:
        for c in j.classes:
            if c.has('Entity'):
                table = re.search(r'@Table\s*\(\s*(?:name\s*=\s*)?"([^"]+)"', c.anno_code)
                mapped.setdefault((table.group(1) if table else entity_x.snake(c.name)).lower(), c.name)
    by_entity_name = {n: n for n in types.classes}
    for j in ctx.main:
        for c in j.classes:
            named = re.search(r'@Entity\s*\(\s*(?:name\s*=\s*)?"(\w+)"', c.anno_code)
            if named:
                by_entity_name[named.group(1)] = c.name
    for j in ctx.main:
        if not re.search(r'(?i)\bupdate\s', j.src.code):
            continue
        sites = []
        for m in j.members:
            if m.kind == 'method' and m.has('Query') and m.has('Modifying'):
                q = re.search(r'@Query\s*\(', m.anno_code)
                close = balanced(m.anno_text, q.end() - 1) if q else -1
                args = m.anno_code[q.end():close] if close > 0 else ''
                sql = ' '.join(a or b for a, b in STRINGS.findall(args))
                native = bool(re.search(r'nativeQuery\s*=\s*true', args))
                sites.append((sql, native, m.anno_offset + q.start() if q else m.offset))
        for sql, native, at in sites:
            stmt = UPDATE_SQL.search(sql)
            if not stmt or stmt.group(1):
                continue
            target = stmt.group(2).strip('"`').split('.')[-1]
            entity = mapped.get(target.lower()) if native else by_entity_name.get(target)
            if not entity:
                continue
            props = _entity_props(types, entity)
            version = next((p for p in props if 'Version' in p['annos']), None)
            dynamic = any(c.has('DynamicUpdate') for _, c in types.classes.get(entity, []))
            counters, bumped = [], False
            for _, part in split_top(stmt.group(4)):
                lhs = re.match(r'\s*(?:\w+\.)?(\w+)\s*=\s*([\s\S]+)', part)
                if not lhs:
                    continue
                col, rhs = lhs.group(1), lhs.group(2)
                key = col.lower() if native else col
                prop = next((p for p in props if (_column(p) if native else p['name']) == key), None)
                if version is not None and prop is version:
                    bumped = True
                    continue
                if not (re.search(r'\b' + re.escape(col) + r'\b', rhs) and re.search(r'[-+]', rhs)):
                    continue
                if prop is None or re.search(r'updatable\s*=\s*false', prop['code']) or \
                        (dynamic and not prop['mutable']):
                    continue
                counters.append(prop)
            if bumped or not counters:
                continue
            extra = {} if version else {'severity': 'medium', 'note': f'{entity} has no @Version - any flush of a '
                                                                       'loaded row overwrites the counter'}
            ctx.hit('DB-NATIVE-COUNTER-OVERWRITE', j, at,
                    f'{"native" if native else "JPQL"} update {target} increments '
                    + ', '.join(f'{entity}.{p["name"]}' for p in counters)
                    + (', version not bumped' if version else ''), entity=entity, **extra)


def run(ctx, entities: list[dict] | None) -> None:
    types = Types(ctx)
    dst_durations(ctx, types)
    seeds(ctx, types)
    unused_limits(ctx)
    counter_overwrites(ctx, types, entities)
