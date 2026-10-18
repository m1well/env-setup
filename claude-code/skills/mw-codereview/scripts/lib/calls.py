"""Who calls whom: outbound HTTP and messaging of the backend, HTTP calls of the frontend, matched to the endpoints."""
from __future__ import annotations

import os
import re
from collections import defaultdict

from .core import Hits, balanced, define, is_test_path, profile_kind, strings_in
from .modules import _build_root, _module_of
from .spring import REMOTE_CALL

define('ARCH-REMOTE-IN-LOOP', 'Remote call inside a loop', 'medium', 'resilience',
       'One network round trip per element - latency and load grow with the list. A batch endpoint, one '
       'query up front, or at least a bounded parallel call.', rule='DATA-4')
define('ARCH-NO-RESILIENCE', 'Outbound HTTP calls without retry or circuit breaker anywhere', 'low', 'resilience',
       'Fine for calls the user retries by hand. For background work and chained calls a transient error '
       'becomes a failed job. Spring Framework 7 has @Retryable and @ConcurrencyLimit built in.', rule='WEB-8')
define('ARCH-HARDCODED-URL', 'Service URL written into the code', 'medium', 'config',
       'The target differs per environment. A @ConfigurationProperties value, one per environment.', rule='STR-5')
define('ARCH-CALL-FANOUT', 'One method calls three or more remote operations in a row', 'low', 'resilience',
       'Latency adds up, and a failure in the third call leaves the first two done. Check whether the '
       'caller can live with a half-finished result, or whether this is a saga or an event.')
define('ARCH-SHARED-DB', 'Two applications on the same database', 'medium', 'architecture',
       'Integration over shared tables: a migration in one breaks the other. Check whether the fallback is only '
       'a local default and production gets separate databases.')
define('ARCH-TOPIC-ORPHAN', 'Topic or queue with a producer but no consumer, or the other way round', 'low',
       'dead-code', 'The other side may live in another repository - say which, or that it is gone.')
define('ARCH-API-UNMATCHED', 'Frontend call that matches no backend endpoint', 'low', 'api',
       'A typo, a removed endpoint, or a path built at runtime. Compare with --show endpoints.')

RETRY = re.compile(r'@(Retryable|CircuitBreaker|Retry|Bulkhead|RateLimiter|ConcurrencyLimit|TimeLimiter)\b|'
                   r'\bretryWhen\s*\(|\.retry\s*\(|RetryTemplate|RetryRegistry|CircuitBreakerRegistry|resilience4j|'
                   r'spring-retry|failsafe', re.I)
LOOP = re.compile(r'\b(for|while)\s*\(|\.\s*(forEach|forEachIndexed|map|mapNotNull|mapIndexed|flatMap|onEach|'
                  r'associate\w*|filter|parallelStream|stream\s*\(\s*\)\s*\.\s*map)\s*[({]|\brepeat\s*\(')
HARDCODED = re.compile(r'(?:baseUrl|rootUri|\.uri|\.url|(?:RestClient|WebClient|HttpClient)\s*\.\s*create|getForObject|'
                       r'getForEntity|postForObject|postForEntity|\.exchange|@HttpExchange|FeignClient[^)]*url\s*=)'
                       r'\s*\(?\s*"(https?://[^"]+)"')
NOT_SERVICE = re.compile(r'^https?://(www\.w3\.org|schemas\.|xmlns\.|json-schema\.org|example\.(com|org)|'
                         r'tools\.ietf\.org|purl\.org)')
EXCHANGE = re.compile(r'@(Get|Post|Put|Patch|Delete|Http)(Exchange|Mapping)\b')
FRONT_CALL = re.compile(r'\b(?:this\s*\.\s*)?_?(?:http|httpClient|client)\s*\.\s*(get|post|put|patch|delete|head|request)\s*')
RESOURCE = re.compile(r'\bhttpResource(?:\s*\.\s*\w+)?\s*')


def _loops(bare: str, start: int, end: int) -> list[tuple[int, int]]:
    out = []
    for m in LOOP.finditer(bare, start, end):
        i = m.end() - 1
        if bare[i] == '(':
            close = balanced(bare, i)
            if close < 0:
                continue
            nxt = re.match(r'\s*\{', bare[close + 1:close + 40])
            if m.group(1) in ('for', 'while') and nxt:
                body_end = balanced(bare, close + 1 + nxt.end() - 1, '{', '}')
                out.append((close, body_end if body_end > 0 else end))
            else:
                out.append((i, close))
        else:
            close = balanced(bare, i, '{', '}')
            out.append((i, close if close > 0 else end))
    return out


def _kind(receiver: str) -> str:
    r = receiver.lower()
    for k in ('kafka', 'rabbit', 'jms', 'stream'):
        if k in r:
            return k
    return 'http'


def backend(ctx) -> list[dict]:
    hits = ctx.hits
    paths = [m['path'] for m in ctx.stack['modules']]
    consts = dict(re.findall(r'\b(?:const\s+val|val|static\s+final\s+String)\s+([A-Z][A-Z0-9_]+)\s*(?::\s*String)?\s*='
                             r'\s*"([^"]+)"', '\n'.join(j.src.code for j in ctx.main)))
    calls = []
    global_retry = bool(RETRY.search(ctx.build) or RETRY.search(ctx.all_main))
    for j in ctx.main:
        bare, code = j.src.bare, j.src.code
        module = _module_of(j.rel, paths)
        for m in j.methods():
            if not m.body:
                continue
            start, end = m.body
            anno = m.anno_text + (m.owner.anno_text if m.owner else '')
            in_tx = 'Transactional' in m.annos or bool(m.owner and m.owner.has('Transactional'))
            retry = bool(RETRY.search(anno))
            loops = _loops(bare, start, end)
            sites = []
            for call in REMOTE_CALL.finditer(bare, start, end):
                receiver, verb = call.group(1), call.group(2)
                if re.search(r'(Repository|Repo|Mapper|Factory|Builder|Converter|Validator)$', receiver):
                    continue
                args_close = balanced(bare, call.end() - 1)
                args = code[call.end():args_close if args_close > 0 else call.end() + 200]
                target = (strings_in(args) or [''])[0]
                if not target:
                    ident = re.match(r'\s*([A-Z][A-Z0-9_]+)\b', args)
                    target = consts.get(ident.group(1), ident.group(1)) if ident else ''
                uri = re.search(r'\.uri\s*\(\s*"([^"]*)"', code[call.start():call.start() + 400])
                kind = _kind(receiver)
                sites.append({'side': 'backend', 'module': module, 'kind': kind, 'receiver': receiver, 'verb': verb,
                              'target': (uri.group(1) if uri else target)[:90], 'file': j.rel,
                              'line': j.src.line_at(call.start()), 'where': f'{j.name}.{m.name}', 'tx': in_tx,
                              'loop': any(a < call.start() < b for a, b in loops), 'retry': retry})
            for s in sites:
                if s['loop'] and s['kind'] == 'http':
                    hits.add('ARCH-REMOTE-IN-LOOP', s['file'], s['line'],
                             f'{s["where"]}: {s["receiver"]}.{s["verb"]}(...) inside a loop')
            http = [s for s in sites if s['kind'] == 'http']
            if len(http) >= 3 and len({s['receiver'] for s in http}) >= 2:
                hits.add('ARCH-CALL-FANOUT', j.rel, m.line,
                         f'{j.name}.{m.name}: {len(http)} remote calls to '
                         + ', '.join(sorted({s["receiver"] for s in http})))
            calls += sites
        for m in EXCHANGE.finditer(bare):
            if m.group(2) == 'Mapping' and j.stereotype != 'client':
                continue
            k = m.end()
            args = ''
            if bare[k:k + 1] == '(':
                close = balanced(bare, k)
                args = code[k + 1:close]
            calls.append({'side': 'backend', 'module': module, 'kind': 'http-client', 'receiver': j.name,
                          'verb': m.group(1).upper(), 'target': ((strings_in(args) or [''])[0])[:90], 'file': j.rel,
                          'line': j.src.line_at(m.start()), 'where': j.name, 'tx': False, 'loop': False,
                          'retry': bool(RETRY.search(j.src.bare))})
        for m in HARDCODED.finditer(code):
            if not NOT_SERVICE.match(m.group(1)):
                hits.add('ARCH-HARDCODED-URL', j.rel, j.src.line_at(m.start()), j.src.line(j.src.line_at(m.start())).strip())
        for m in re.finditer(r'@(KafkaListener|RabbitListener|JmsListener|SqsListener)\s*\(', bare):
            close = balanced(bare, m.end() - 1)
            args = code[m.end():close]
            for name in strings_in(args) or [consts.get(n, n) for n in re.findall(r'\b([A-Z][A-Z0-9_]+)\b', args)]:
                calls.append({'side': 'backend', 'module': module, 'kind': m.group(1).replace('Listener', '').lower(),
                              'receiver': '@' + m.group(1), 'verb': 'consume', 'target': name, 'file': j.rel,
                              'line': j.src.line_at(m.start()), 'where': j.name, 'tx': False, 'loop': False,
                              'retry': False})
    for src, entries in ctx.configs:
        for e in entries:
            b = re.match(r'spring\.cloud\.stream\.bindings\.([\w-]+)-(in|out)-\d+\.destination$', e.key)
            if b and not is_test_path(src.rel):
                calls.append({'side': 'backend', 'module': _module_of(src.rel, paths), 'kind': 'stream',
                              'receiver': b.group(1), 'verb': 'consume' if b.group(2) == 'in' else 'send',
                              'target': e.value, 'file': src.rel, 'line': e.line, 'where': 'config', 'tx': False,
                              'loop': False, 'retry': False})

    http_sites = [c for c in calls if c['kind'] in ('http', 'http-client')]
    if http_sites and not global_retry:
        hits.add('ARCH-NO-RESILIENCE', http_sites[0]['file'], http_sites[0]['line'],
                 f'{len(http_sites)} outbound HTTP call sites in {len({c["file"] for c in http_sites})} files, '
                 'no retry or circuit breaker dependency or annotation')
    produced = {c['target'] for c in calls if c['kind'] != 'http' and c['verb'] != 'consume' and c['target']}
    consumed = {c['target'] for c in calls if c['verb'] == 'consume' and c['target']}
    for c in calls:
        if c['kind'] in ('http', 'http-client') or not c['target'] or not re.fullmatch(r'[\w.\-/]+', c['target']):
            continue
        if c['verb'] == 'consume' and c['target'] not in produced and produced:
            hits.add('ARCH-TOPIC-ORPHAN', c['file'], c['line'], f'{c["where"]} consumes {c["target"]}, no producer here')
        elif c['verb'] != 'consume' and c['target'] not in consumed and consumed:
            hits.add('ARCH-TOPIC-ORPHAN', c['file'], c['line'], f'{c["where"]} sends to {c["target"]}, no consumer here')
    _shared_db(ctx, paths)
    return calls


def _shared_db(ctx, paths: list[str]):
    repo = ctx.repo
    apps = defaultdict(lambda: {'urls': {}, 'schemas': set()})
    for src, entries in ctx.configs:
        if is_test_path(src.rel):
            continue
        app = _build_root(repo, _module_of(src.rel, paths) or os.path.dirname(src.rel))
        for e in entries:
            if profile_kind(e.profile) == 'dev':
                continue
            fallback = re.fullmatch(r'\$\{[^:}]+:(.+)\}', e.value.strip())
            value = fallback.group(1) if fallback else e.value
            if re.search(r'(flyway|liquibase)\.(schemas|defaultschema)$|hibernate\.defaultschema$', e.norm):
                apps[app]['schemas'] |= {s.strip().lower() for s in value.split(',') if s.strip()}
            elif re.search(r'spring\.(datasource|r2dbc)\.url$', e.norm) and not value.startswith('${') and \
                    re.search(r'//[^/]+/\w', value):
                schema = re.search(r'(?:currentSchema|schema)=([\w,]+)', value)
                if schema:
                    apps[app]['schemas'] |= set(schema.group(1).lower().split(','))
                key = re.sub(r'^(jdbc:|r2dbc:)', '', value).split('?')[0].lower()
                apps[app]['urls'].setdefault(key, (src.rel, e.line))
    shared = defaultdict(list)
    for app, a in apps.items():
        for key, where in a['urls'].items():
            shared[(key, frozenset(a['schemas']))].append((app, where))
    for (key, schemas), group in shared.items():
        if len(group) > 1:
            ctx.hits.add('ARCH-SHARED-DB', group[0][1][0], group[0][1][1],
                         f'{key} used by ' + ', '.join(sorted(a for a, _ in group))
                         + (f', same schema {", ".join(sorted(schemas))}' if schemas else ', no schema separation'))
    owners = {s: app for app, a in apps.items() for s in a['schemas']}
    seen = set()
    for app, a in apps.items():
        prefix = '' if app == '.' else app + '/'
        for rel in repo.files:
            if not (rel.startswith(prefix) and rel.endswith('.sql') and '/db/' in '/' + rel) or is_test_path(rel):
                continue
            src = repo.source(rel)
            for m in re.finditer(r'(?i)\breferences\s+"?(\w+)"?\s*\.\s*"?(\w+)', src.text):
                other = owners.get(m.group(1).lower())
                if other and other != app and (app, other) not in seen:
                    seen.add((app, other))
                    ctx.hits.add('ARCH-SHARED-DB', rel, src.line_at(m.start()),
                                 f'{app} has a foreign key into {m.group(1)}.{m.group(2)}, a schema {other} migrates')


def _norm(path: str) -> list[str]:
    path = re.sub(r'\$\{(?:[^{}]|\{[^{}]*\})*\}', '{x}', path).split('?')[0].split('#')[0]
    segs = [s for s in path.split('/') if s]
    while segs and segs[0] == '{x}':
        segs.pop(0)
    return ['*' if re.fullmatch(r'\{[^}]*\}|:\w+', s) or '{x}' in s else s.lower() for s in segs]


def _seg_score(a: list[str], b: list[str]) -> int:
    """Exactly equal segments when the shorter path is a suffix of the longer one, else 0."""
    if not a or not b:
        return 0
    short, long_ = (a, b) if len(a) <= len(b) else (b, a)
    tail = long_[len(long_) - len(short):]
    if not all(x == y or '*' in (x, y) for x, y in zip(short, tail)):
        return 0
    exact = sum(1 for x, y in zip(short, tail) if x == y and x != '*')
    static = sum(1 for x in short if x != '*')
    return exact if exact >= min(2, static) and (len(short) == len(long_) or len(short) >= 2) else 0


def _seg_match(a: list[str], b: list[str]) -> bool:
    return _seg_score(a, b) > 0


def _first_arg(code: str, bare: str, at: int) -> tuple[str | None, str | None, int]:
    i = at
    while i < len(bare) and bare[i] in ' \t\n':
        i += 1
    if bare[i:i + 1] == '<':
        close = balanced(bare, i, '<', '>')
        i = close + 1 if close > 0 else i
        while i < len(bare) and bare[i] in ' \t\n':
            i += 1
    if bare[i:i + 1] != '(':
        return None, None, i
    close = balanced(bare, i)
    args = code[i + 1:close if close > 0 else i + 400]
    lit = re.match(r'\s*(?:\(\s*\)\s*=>\s*\(?\s*\{?\s*(?:url\s*:\s*)?)?(`[^`]*`|\'[^\']*\'|"[^"]*")', args)
    method = re.search(r'\bmethod\s*:\s*[\'"](\w+)[\'"]', args)
    return (lit.group(1)[1:-1] if lit else None), (method.group(1).upper() if method else None), i


def frontend(w, hits: Hits, endpoints: list[dict] | None) -> list[dict]:
    calls = []
    for rel in w.main_ts:
        src = w.repo.source(rel)
        code, bare = src.code, src.bare
        for rx, resource in ((FRONT_CALL, False), (RESOURCE, True)):
            for m in rx.finditer(bare):
                verb = 'GET' if resource else m.group(1).upper()
                url, method, _ = _first_arg(code, bare, m.end())
                if verb == 'REQUEST' and url is not None:
                    method, verb = url.upper(), None
                    url = None
                if resource and method:
                    verb = method
                if url is None or verb is None:
                    continue
                calls.append({'side': 'frontend', 'app': w.ws['path'], 'kind': 'http', 'verb': verb,
                              'target': url[:120], 'file': rel, 'line': src.line_at(m.start()), 'matched': None})
    if endpoints:
        backend = [(e['http'], _norm(e['path']), e) for e in endpoints]
        for c in calls:
            t = c['target']
            if re.match(r'https?://', t) or '/realms/' in t or re.search(r'(^|/)(assets|i18n)/|\.json$', t):
                c['matched'] = 'external'
                continue
            segs = _norm(t)
            if not [s for s in segs if s != '*']:
                c['matched'] = 'dynamic'
                continue
            scored = [(_seg_score(segs, b), e) for verb, b, e in backend if verb in (c['verb'], 'ANY')]
            match = max((x for x in scored if x[0]), key=lambda x: x[0], default=(0, None))[1]
            if match:
                c['matched'] = f'{match["http"]} {match["path"]}'
            else:
                hits.add('ARCH-API-UNMATCHED', c['file'], c['line'], f'{c["verb"]} {t}')
    return calls
