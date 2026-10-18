"""Business paths without a test: write endpoints, branchy service logic, security rules, async entry points."""
from __future__ import annotations

import os
import re
from collections import defaultdict

from .calls import _norm, _seg_match
from .core import STRING_LIT, Hits, define, is_test_path

define('TESTGAP-WRITE', 'Write endpoints that no test reaches', 'medium', 'testing',
       'No test names the path, the handler or the service method it delegates to. Open the service: the '
       'more rules it applies, the more this gap costs.', rule='TEST-1')
define('TESTGAP-SECURITY', 'No test proves a request is rejected', 'medium', 'testing',
       'Not one test expects 401 or 403. A security rule nobody tests is one refactoring away from open.',
       rule='TEST-4')
define('TESTGAP-LOGIC', 'Branchy service methods no test calls', 'medium', 'testing',
       'Branches and throws are business rules. Name the rule each untested branch decides.', rule='TEST-1')
define('TESTGAP-ASYNC', 'Scheduled jobs and listeners without a test', 'low', 'testing',
       'Nobody clicks them, so nobody notices when they break.', rule='TEST-6')
define('TESTGAP-QUERY', 'Custom queries without a repository test', 'low', 'testing',
       'A @Query is only checked when it runs - against the real engine, with Testcontainers.', rule='TEST-3')
define('TESTGAP-H2', 'Tests run on H2 while production runs another database', 'medium', 'testing',
       'Migrations, native queries, JSON and locking behave differently. Testcontainers with @ServiceConnection.',
       rule='TEST-3')
define('TESTGAP-MODULE', 'Build module with ten or more classes and no test', 'medium', 'testing', '',
       rule='TEST-1')
define('TESTGAP-E2E-ROUTE', 'Routes no end-to-end test opens', 'low', 'testing',
       'Only routes reached by a goto/visit count - a route reached by clicking through is covered too.')
define('TESTGAP-FRONT-LOGIC', 'Forms with validation and state services without a spec', 'low', 'testing',
       'Validation and state are the frontend\'s business logic.')

REJECTED = re.compile(r'isUnauthorized|isForbidden|UNAUTHORIZED|FORBIDDEN|expectStatus\(\)\s*\.\s*is(Unauthorized|Forbidden)|'
                      r'status\(\)\s*\.\s*is(Unauthorized|Forbidden)|\b40[13]\b')
BRANCH = re.compile(r'\b(if|when|case|catch|for|while)\b|&&|\|\||\?:|\bthrow\b|\brequire(NotNull)?\s*\(|\bcheck\s*\(')
KT_TEMPLATE = re.compile(r'\$([a-zA-Z_]\w*)')


def _paths_in_tests(texts: list[str]) -> list[tuple[str | None, list[str]]]:
    """(HTTP verb or None, path segments) of every path-like literal; the verb comes from the call around it."""
    out = []
    for text in texts:
        for m in STRING_LIT.finditer(text):
            s = m.group(1) if m.group(1) is not None else m.group(2)
            listed = re.match(r'(GET|POST|PUT|PATCH|DELETE)\s+(/\S*)$', s.strip())
            if listed:
                verb, s = listed.groups()
            elif '/' not in s or ' ' in s.strip() or len(s) > 200:
                continue
            else:
                call = re.search(r'\b(get|post|put|patch|delete)\w*\s*(?:\(\s*\)\s*\.\s*uri\s*)?\(\s*$',
                                 text[max(0, m.start() - 40):m.start()], re.I)
                verb = call.group(1).upper() if call else None
            segs = _norm(KT_TEMPLATE.sub(r'${\1}', s))
            if [x for x in segs if x != '*']:
                out.append((verb, segs))
    return out


def _deps_names(jf) -> set[str]:
    cls = jf.cls
    if not cls:
        return set()
    names = {p.name for p in cls.params} if jf.kotlin else set()
    names |= {m.name for m in jf.members if m.kind == 'field' and m.owner is cls}
    return names


def backend(ctx, modules: list[dict]) -> dict:
    hits = ctx.hits
    tests = [(s.rel, s.code) for s in ctx.tests]
    e2e = [(f, ctx.repo.source(f).code) for f in ctx.repo.files
           if f.endswith(('.ts', '.js', '.http')) and is_test_path(f) and not f.endswith('.spec.ts')]
    test_text = '\n'.join(t for _, t in tests)
    test_paths = _paths_in_tests([t for _, t in tests + e2e])

    def referenced(method: str, owner: str) -> bool:
        call = re.compile(r'(\.|::)\s*' + re.escape(method) + r'\b')
        return any(owner in text and call.search(text) for _, text in tests)

    untested = defaultdict(list)
    writes = [e for e in ctx.endpoints if e['http'] in ('POST', 'PUT', 'PATCH', 'DELETE') and e['_member'] is not None]
    for e in writes:
        segs = _norm(e['path'])
        if any(verb in (None, e['http']) and _seg_match(segs, t) for verb, t in test_paths):
            continue
        jf, m = e['_jf'], e['_member']
        if referenced(m.name, jf.name):
            continue
        deps = _deps_names(jf)
        body = jf.body_text(m, 'code')
        delegated = [(r, meth) for r, meth in re.findall(r'\b(\w+)\s*\??\.\s*(\w+)\s*\(', body) if r in deps]
        types = {p.name: p.type for p in (jf.cls.params if jf.cls and jf.kotlin else [])}
        types |= {f.name: f.returns for f in jf.members if f.kind == 'field'}
        if any(referenced(meth, types.get(r, r).split('<')[0].strip('? ')) for r, meth in delegated):
            continue
        untested[(e['file'], e['controller'])].append(e)
    total_untested = sum(len(v) for v in untested.values())
    for (rel, ctrl), eps in sorted(untested.items(), key=lambda kv: -len(kv[1])):
        hits.add('TESTGAP-WRITE', rel, eps[0]['line'],
                 f'{ctrl}: {len(eps)} write endpoint(s) untested - '
                 + ', '.join(f'{e["http"]} {e["path"]}' for e in eps[:6]) + (' ...' if len(eps) > 6 else ''),
                 names=[f'{e["http"]} {e["path"]}' for e in eps])

    if ctx.chains and ctx.tests and not REJECTED.search(test_text):
        hits.add('TESTGAP-SECURITY', ctx.chains[0]['file'], ctx.chains[0]['line'],
                 f'{len(ctx.chains)} security chain(s), {len(ctx.tests)} test files, none expects 401/403')

    for jf in ctx.main:
        if jf.stereotype not in ('service', 'component'):
            continue
        risky = []
        for m in jf.methods():
            if m.private or not m.body:
                continue
            branches = len(BRANCH.findall(jf.body_text(m)))
            if branches >= 6 and not referenced(m.name, jf.name):
                risky.append((m, branches))
        if risky:
            risky.sort(key=lambda x: -x[1])
            hits.add('TESTGAP-LOGIC', jf.rel, risky[0][0].line,
                     f'{jf.name}: ' + ', '.join(f'{m.name} ({n} branches)' for m, n in risky[:5]),
                     severity='medium' if risky[0][1] >= 10 else 'low')

    async_untested = []
    for jf in ctx.main:
        for m in jf.methods():
            if m.has('Scheduled', 'EventListener', 'TransactionalEventListener', 'ApplicationModuleListener',
                     'KafkaListener', 'RabbitListener', 'JmsListener', 'SqsListener') and jf.name not in test_text:
                async_untested.append((jf, m))
    if async_untested:
        jf, m = async_untested[0]
        hits.add('TESTGAP-ASYNC', jf.rel, m.line, f'{len(async_untested)} entry points: '
                 + ', '.join(f'{j.name}.{x.name}' for j, x in async_untested[:8]),
                 names=[f'{j.name}.{x.name}' for j, x in async_untested])

    queries = []
    for jf in ctx.by['repository']:
        n = sum(1 for m in jf.methods() if m.has('Query', 'NativeQuery', 'Modifying'))
        if n and jf.name not in test_text:
            queries.append((jf, n))
    if queries:
        hits.add('TESTGAP-QUERY', queries[0][0].rel, None,
                 f'{sum(n for _, n in queries)} @Query methods in {len(queries)} repositories no test names: '
                 + ', '.join(f'{j.name} ({n})' for j, n in queries[:8]))

    prod_db = re.search(r'postgresql|mysql|mariadb|mssql-jdbc|ojdbc|r2dbc-postgres', ctx.build, re.I)
    h2 = re.search(r'["\':]com\.h2database:h2|<artifactId>h2</artifactId>|jdbc:h2:', ctx.build + '\n' +
                   '\n'.join(s.text for s, _ in ctx.configs if is_test_path(s.rel)))
    if prod_db and h2 and ctx.tests:
        containers = re.search(r'testcontainers', ctx.build, re.I)
        hits.add('TESTGAP-H2', None, None, f'production driver {prod_db.group(0)}, tests on H2'
                 + (', Testcontainers present as well' if containers else ', no Testcontainers'),
                 severity='low' if containers else None)

    for m in modules:
        if m['types'] >= 10 and m['tests'] == 0:
            hits.add('TESTGAP-MODULE', m['path'], None, f'{m["path"].split("/")[-1]}: {m["types"]} classes, no test file')
    return {'write_endpoints': len(writes), 'untested_writes': total_untested}


VALIDATORS = re.compile(r'\bValidators\s*\.\s*\w+|\b(required|email|pattern|minLength|maxLength|min|max|validate|'
                        r'validateTree|validateAsync|validateHttp)\s*\(\s*\w+\s*\.')


def frontend(w, hits: Hits) -> dict:
    repo = w.repo
    e2e_files = [f for f in w.ts if re.search(r'(^|/)(e2e|cypress|playwright)(/|-)|[\w-]+-e2e/', f)]
    if e2e_files and w.routes:
        text = '\n'.join(repo.source(f).code for f in e2e_files)
        visited = []
        for m in re.finditer(r'\b(goto|visit|navigate\w*)\s*\(\s*(`[^`]*`|\'[^\']*\'|"[^"]*")', text):
            raw = KT_TEMPLATE.sub(r'${\1}', m.group(2)[1:-1])
            visited.append(_norm(raw))
        routes = [r for r in w.routes if not r['redirect'] and r['segment'] != '**' and r['target']]
        missing = [r for r in routes if not any(_seg_match(_norm(r['path']), v) or (_norm(r['path']) == [] and v == [])
                                                for v in visited)]
        if missing and visited:
            hits.add('TESTGAP-E2E-ROUTE', missing[0]['file'], missing[0]['line'],
                     f'{len(missing)} of {len(routes)} routes: ' + ', '.join(r['path'] for r in missing[:12]),
                     names=[r['path'] for r in missing])
    specs = {f for f in w.ts if f.endswith('.spec.ts')}
    missing = {}
    for rel in w.main_ts:
        code = repo.source(rel).code
        logic = VALIDATORS.search(code) or ('@Injectable' in code and re.search(r'[-.](state|store|facade)\.ts$', rel))
        if logic and re.sub(r'\.ts$', '.spec.ts', rel) not in specs:
            missing[rel] = 1
    if missing:
        top = sorted(missing)
        hits.add('TESTGAP-FRONT-LOGIC', top[0], None, f'{len(missing)} files: '
                 + ', '.join(os.path.basename(f) for f in top[:10]), files=top[:40])
    return {'e2e_files': len(e2e_files)}
