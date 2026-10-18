"""Who calls whom: outbound HTTP and messaging of the backend, HTTP calls of the frontend, matched to the endpoints."""
from __future__ import annotations

import os
import re
from collections import defaultdict

from . import spring
from .core import Hits, balanced, define, is_test_path, profile_kind, split_top, strings_in
from .modules import _build_root, _module_of

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
define('ARCH-CALL-PER-REQUEST', 'Remote call on every request', 'medium', 'resilience',
       'A filter or interceptor calls another system for each request: every request waits for it and fails with it. '
       'Cache the result for a short time, skip public paths (shouldNotFilter), and decide what a timeout turns into.',
       rule='WEB-8')
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


MESSAGING = {'kafka', 'rabbit', 'jms', 'stream', 'sqs'}
VALUE = re.compile(r'@Value\s*\(\s*"\\?\$\{([^}:]+)(?::[^}]*)?\}"\s*\)\s*(?:(?:private|protected|internal|public|final|'
                   r'val|var|lateinit|override)\s+)*(?:[\w.<>?]+\s+)?(\w+)')
CACHED = re.compile(r'(?i)cache|caffeine|computeIfAbsent|getIfPresent|memoi')


def _host_of(value: str) -> str | None:
    v = value.strip().strip('"\'')
    fallback = re.fullmatch(r'\$\{[^:}]+:(.+)\}', v)
    v = fallback.group(1) if fallback else v
    m = re.match(r'(?i)[a-z][a-z0-9+.-]*://(?:[^@/\s]*@)?(\[[^\]]+\]|[^/:?#\s$]+)(?::(\d+))?', v)
    return m.group(1).lower() + (':' + m.group(2) if m.group(2) else '') if m else None


class Hosts:
    """Host of an outbound call from a literal, a constant, @Value or a @ConfigurationProperties field - only the host
    of a URL-like config value is ever copied."""

    def __init__(self, ctx):
        self.ctx, self.consts, self.values, self.props = ctx, spring.string_consts(ctx), {}, {}
        for j in ctx.main:
            for c in j.members:
                args = re.search(r'@ConfigurationProperties\s*\(([^)]*)\)', c.anno_code) \
                    if c.has('ConfigurationProperties') else None
                prefix = (strings_in(args.group(1)) or [''])[0] if args else ''
                target = c.name if c.kind == 'class' else re.sub(r'<.*', '', c.returns).strip('? ').split('.')[-1]
                if prefix and target:
                    self.props[target] = prefix
        self.beans = defaultdict(list)
        for j in ctx.main:
            for m in j.methods():
                base = re.search(r'\.\s*(?:baseUrl|rootUri)\s*\(', j.src.bare[m.body[0]:m.body[1]]) if m.body else None
                if m.has('Bean') and base and spring.client_kind(m.returns, set()):
                    host = self._arg(j, m.body[0] + base.end() - 1)
                    if host:
                        self.beans[_type_key(m.returns)].append((m.name, host))
        self.declarative = {}
        for name in spring.graph(ctx)['declarative']:
            j, c = spring.graph(ctx)['classes'][name]
            url = re.search(r'\burl\s*=\s*("(?:\\.|[^"\\])*"|[\w.]+)|@HttpExchange\s*\(\s*("(?:\\.|[^"\\])*")',
                            c.anno_code)
            self.declarative[name] = self.resolve(j, url.group(1) or url.group(2), c.offset) if url else None

    def mail(self, j) -> str | None:
        for v in spring.config_values(self.ctx, 'spring.mail.host', j.rel):
            v = re.sub(r'^\$\{[^:}]+:(.*)\}$', r'\1', v)
            if re.fullmatch(r'[\w.-]+', v):
                return v.lower()
        return None

    def _arg(self, j, open_at: int) -> str | None:
        close = balanced(j.src.bare, open_at)
        args = split_top(j.src.bare[open_at + 1:close]) if close > 0 else []
        a = open_at + 1 + args[0][0] if args else 0
        return self.resolve(j, j.src.code[a:a + len(args[0][1])], open_at) if args else None

    def config(self, j, key: str) -> str | None:
        if spring.SECRET_KEY.search(key.split('.')[-1]):
            return None
        return next((h for h in map(_host_of, spring.config_values(self.ctx, key, j.rel)) if h), None)

    def resolve(self, j, expr: str, at: int, depth: int = 3) -> str | None:
        first = re.split(r'\s\+\s', (expr or '').strip())[0].strip()
        if depth < 0 or not first:
            return None
        lit = re.match(r'"((?:\\.|[^"\\])*)"', first)
        if lit:
            s = lit.group(1)
            placeholder = re.match(r'(\\?)\$\{([\w.\-\[\]]+)(?::([^}]*))?\}', s)
            if placeholder and (placeholder.group(1) or not j.kotlin):
                return self.config(j, placeholder.group(2)) or _host_of(placeholder.group(3) or '')
            template = spring.TEMPLATE_VAR.match(s) if j.kotlin else None
            return _host_of(s) or (self.resolve(j, template.group(1) or template.group(2), at, depth - 1)
                                   if template else None)
        if re.fullmatch(r'(?:\w+\.)*[A-Z][A-Z0-9_]+', first):
            return self.resolve(j, self.consts.get(first.split('.')[-1], ''), at, depth - 1)
        head = re.match(r'(?:this\s*\.\s*)?(\w+)', first)
        if not head:
            return None
        name, rest, segs = head.group(1), first[head.end():], []
        while True:
            seg = re.match(r'\s*[?!]*\.\s*(\w+)\s*(\(\s*\))?', rest)
            if not seg or (not seg.group(2) and rest[seg.end():].lstrip().startswith('(')):
                break
            word = seg.group(1)
            if seg.group(2):
                if not re.match(r'get[A-Z]', word):
                    break
                word = word[3].lower() + word[4:]
            segs.append(word)
            rest = rest[seg.end():]
        bare, code = j.src.bare, j.src.code
        if not segs:
            if j.rel not in self.values:
                self.values[j.rel] = {m.group(2): m.group(1) for m in VALUE.finditer(code)}
            if name in self.values[j.rel]:
                return self.config(j, self.values[j.rel][name])
            init = re.search(r'\b(?:val|var|String|final\s+String)\s+' + re.escape(name) + r'\b[^=\n]*=(?!=)\s*', bare)
            return self.resolve(j, code[init.end():spring.statement_end(bare, init.end())], init.end(), depth - 1) \
                if init else None
        typed = spring.fields(self.ctx, spring.owner_at(j, at)).get(name) or ''
        if not typed:
            found = re.search(r'(?<![\w.])' + re.escape(name) + r'\s*:\s*([\w.]+)', bare) if j.kotlin else \
                re.search(r'([\w.]+)(?:<[^>]*>)?\s+' + re.escape(name) + r'\s*[;,)=]', bare)
            typed = found.group(1) if found else ''
        cls = re.sub(r'<.*', '', typed).strip('?! ').split('.')[-1]
        if cls not in self.props:
            return None
        found = spring.graph(self.ctx)['classes'].get(cls)
        default = next((p.code for p in found[1].params if p.name == segs[0]), '') if found and len(segs) == 1 else ''
        return self.config(j, self.props[cls] + '.' + '.'.join(segs)) or _host_of((strings_in(default) or [''])[0])

    def base(self, j, receiver: str, at: int, seen: tuple = ()) -> str | None:
        recv = spring.receivers(self.ctx, j)
        r = recv.get(receiver) or recv.get(receiver + '()')
        if not r or receiver in seen:
            return None
        if r['kind'] == 'declarative':
            return self.declarative.get(r['type'].split('<')[0].split('.')[-1])
        if r['init']:
            found = re.search(r'\.\s*(?:baseUrl|rootUri)\s*\(', j.src.bare[r['init'][0]:r['init'][1]])
            if found:
                return self._arg(j, r['init'][0] + found.end() - 1)
            return self.base(j, r['from'], r['init'][0], seen + (receiver,)) if r['from'] else None
        beans = self.beans.get(_type_key(r['type']), [])
        named = [h for n, h in beans if n == receiver]
        return named[0] if named else beans[0][1] if len(beans) == 1 else None


def _type_key(t: str) -> str:
    t = re.sub(r'\s+', '', t or '').rstrip('?')
    inner = re.fullmatch(r'(?:[\w.]*\.)?(?:ObjectProvider|Provider|Optional|Lazy)<(.+)>', t)
    parts = (inner.group(1) if inner else t).split('<')[0].split('.')
    return '.'.join(parts[-2:]) if parts[-1] == 'Builder' else parts[-1]


def _uri(bare: str, code: str, start: int, end: int) -> str:
    """First argument of the .uri(...) / HttpRequest.newBuilder(...) in a call chain, as code."""
    u = re.search(r'\.\s*uri\s*\(|\bnewBuilder\s*\(\s*(?=[^)\s])', bare[start:end])
    if not u:
        return ''
    open_at = start + u.end() - 1
    close = balanced(bare, open_at)
    args = split_top(bare[open_at + 1:close]) if close > 0 else []
    return code[open_at + 1 + args[0][0]:open_at + 1 + args[0][0] + len(args[0][1])].strip() if args else ''


def backend(ctx) -> list[dict]:
    hits = ctx.hits
    paths = [m['path'] for m in ctx.stack['modules']]
    consts = dict(re.findall(r'\b(?:const\s+val|val|static\s+final\s+String)\s+([A-Z][A-Z0-9_]+)\s*(?::\s*String)?\s*='
                             r'\s*"([^"]+)"', '\n'.join(j.src.code for j in ctx.main)))
    hosts = Hosts(ctx)
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
            for s in spring.remote_sites(ctx, j, start, end):
                at = s['offset'] + len(s['text'])
                args_close = balanced(bare, at - 1)
                args = code[at:args_close if args_close > 0 else at + 200]
                first = split_top(bare[at:args_close]) if args_close > 0 else []
                first = code[at + first[0][0]:at + first[0][0] + len(first[0][1])] if first else ''
                target = '' if s.get('declarative') else (strings_in(args) or [''])[0]
                if not target:
                    ident = re.match(r'\s*([A-Z][A-Z0-9_]+)\b', args)
                    target = consts.get(ident.group(1), ident.group(1)) if ident else ''
                uri, verb = '', s['verb']
                if s['kind'] == 'http':
                    built = verb in ('send', 'sendAsync', 'newCall', 'execute')
                    uri = _uri(bare, code, s['offset'], spring.statement_end(bare, s['offset'])) or \
                        (_uri(bare, code, start, s['offset']) if built else '')
                    if built:
                        method = re.search(r'\.\s*(GET|POST|PUT|DELETE|PATCH|HEAD)\s*\(|\.\s*method\s*\(\s*"(\w+)"',
                                           code[start:s['offset']])
                        verb = (method.group(1) or method.group(2)).lower() if method else verb
                    target = (strings_in(uri) or [uri])[0] if uri else target
                host = hosts.mail(j) if s['kind'] == 'mail' else \
                    (hosts.resolve(j, uri or first, s['offset']) or hosts.resolve(j, f'"{target}"', s['offset']) or
                     hosts.base(j, s['receiver'], s['offset'])) if s['kind'] == 'http' else None
                site = {'side': 'backend', 'module': module, 'kind': s['kind'], 'receiver': s['receiver'],
                        'verb': verb, 'target': ('' if s['kind'] == 'mail' else target)[:90], 'file': j.rel,
                        'line': j.src.line_at(s['offset']), 'where': f'{m.owner.name if m.owner else j.name}.{m.name}',
                        'tx': in_tx,
                        'loop': any(a < s['offset'] < b for a, b in loops), 'retry': retry, 'per_request': False}
                if host:
                    site['host'] = host
                sites.append(site)
            for s in sites:
                if s['loop'] and s['kind'] == 'http':
                    hits.add('ARCH-REMOTE-IN-LOOP', s['file'], s['line'],
                             f'{s["where"]}: {s["receiver"]}.{s["verb"]}(...) inside a loop')
            http = [s for s in sites if s['kind'] == 'http']
            if len(http) >= 3 and len({s['receiver'] for s in http}) >= 2:
                hits.add('ARCH-CALL-FANOUT', j.rel, m.line,
                         f'{http[0]["where"]}: {len(http)} remote calls to '
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
            site = {'side': 'backend', 'module': module, 'kind': 'http-client', 'receiver': j.name,
                    'verb': m.group(1).upper(), 'target': ((strings_in(args) or [''])[0])[:90], 'file': j.rel,
                    'line': j.src.line_at(m.start()), 'where': j.name, 'tx': False, 'loop': False,
                    'retry': bool(RETRY.search(j.src.bare)), 'per_request': False}
            if hosts.declarative.get(j.name):
                site['host'] = hosts.declarative[j.name]
            calls.append(site)
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
                              'retry': False, 'per_request': False})
    for src, entries in ctx.configs:
        for e in entries:
            b = re.match(r'spring\.cloud\.stream\.bindings\.([\w-]+)-(in|out)-\d+\.destination$', e.key)
            if b and not is_test_path(src.rel):
                calls.append({'side': 'backend', 'module': _module_of(src.rel, paths), 'kind': 'stream',
                              'receiver': b.group(1), 'verb': 'consume' if b.group(2) == 'in' else 'send',
                              'target': e.value, 'file': src.rel, 'line': e.line, 'where': 'config', 'tx': False,
                              'loop': False, 'retry': False, 'per_request': False})

    _per_request(ctx, calls)
    http_sites = [c for c in calls if c['kind'] in ('http', 'http-client')]
    if http_sites and not global_retry:
        hits.add('ARCH-NO-RESILIENCE', http_sites[0]['file'], http_sites[0]['line'],
                 f'{len(http_sites)} outbound HTTP call sites in {len({c["file"] for c in http_sites})} files, '
                 'no retry or circuit breaker dependency or annotation')
    produced = {c['target'] for c in calls if c['kind'] in MESSAGING and c['verb'] != 'consume' and c['target']}
    consumed = {c['target'] for c in calls if c['verb'] == 'consume' and c['target']}
    for c in calls:
        if c['kind'] not in MESSAGING or not c['target'] or not re.fullmatch(r'[\w.\-/]+', c['target']):
            continue
        if c['verb'] == 'consume' and c['target'] not in produced and produced:
            hits.add('ARCH-TOPIC-ORPHAN', c['file'], c['line'], f'{c["where"]} consumes {c["target"]}, no producer here')
        elif c['verb'] != 'consume' and c['target'] not in consumed and consumed:
            hits.add('ARCH-TOPIC-ORPHAN', c['file'], c['line'], f'{c["where"]} sends to {c["target"]}, no consumer here')
    _shared_db(ctx, paths)
    return calls


def _per_request(ctx, calls: list[dict]):
    by_site = {(c['file'], c['line']): c for c in calls}
    for jf, m in spring.request_filters(ctx):
        found = [p for p in spring.paths(ctx, jf, m, spring.sites_http, 2)
                 if not any(x.has('Cacheable') or CACHED.search(j2.body_text(x, 'code')) for j2, x, _ in p)]
        for p in found:
            last, _, site = p[-1]
            c = by_site.get((last.rel, last.src.line_at(site['offset'])))
            if c:
                c['per_request'] = True
        if found:
            ctx.hits.add('ARCH-CALL-PER-REQUEST', jf.rel, jf.src.line_at(found[0][0][2]['offset']),
                         f'{jf.name}.{m.name}: {spring.chain_text(found[0], head=False)}, no cache on the way')


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
