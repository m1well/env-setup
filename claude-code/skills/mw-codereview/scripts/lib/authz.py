"""Authorization model and tenant isolation: which concepts the code uses, and the traps each one has."""
from __future__ import annotations

import re

from . import schema
from .core import balanced, define, is_test_path
from .spring import _anno_args as anno_args, _matches, string_consts, string_values
from .testgaps import _beans, _fields, delegates

define('SB-POSTAUTHORIZE-WRITE', '@PostAuthorize on a method that changes data', 'high', 'authorization',
       'The check runs after the method returned - the write already happened when the caller gets the 403. '
       'Load and check first (@PreAuthorize with a policy bean, or a query that includes the caller), then write.',
       security=True, rule='SEC-1', owasp='A01')
define('SB-POSTFILTER', '@PostFilter on a collection', 'medium', 'performance',
       'Loads every row, then drops what the caller may not see: slow on big tables, and page sizes and totals lie. '
       'Put the caller or the tenant into the query.')
define('SB-PREAUTH-COMPLEX', 'Long authorization expression in an annotation', 'low', 'maintainability',
       'SpEL strings are not refactoring-safe and hard to test. A policy bean '
       '(@PreAuthorize("@projectPolicy.canEdit(#id, authentication)")) keeps the rule in code and in a unit test.')
define('SB-AUTHZ-FAIL-OPEN', 'Authorization check that grants access when it fails', 'high', 'authorization',
       'A timeout or an exception in the permission lookup (Keycloak, database, policy engine) lets the request '
       'through. Deny on error and log it.', security=True, owasp='A01')
define('SB-ISSUER-FROM-TOKEN', 'Token issuer trusted without an allow-list', 'critical', 'authentication',
       'A resolver that builds the decoder from the iss claim of an unverified token accepts any issuer - the '
       'attacker hosts their own JWKS. Map a fixed set: JwtIssuerAuthenticationManagerResolver.fromTrustedIssuers(list).',
       security=True, owasp='A07')
define('SB-TOKEN-RELAY', 'Incoming user token forwarded to another service', 'medium', 'authentication',
       'Fine when the target expects exactly this token and checks its own audience. Otherwise one leaked token opens '
       'every service behind it. Token exchange, or client credentials for calls the user did not make.',
       security=True, owasp='A07')
define('SB-TENANT-THREADLOCAL', 'Tenant or user context in a ThreadLocal that is not reliably cleared', 'high',
       'authorization',
       'Servlet threads are pooled: a context not removed in a finally block serves the next request, possibly of '
       'another tenant. An InheritableThreadLocal is copied into pool threads created later.', security=True,
       owasp='A01')
define('SB-TENANT-CONTEXT-LOST', 'Async or background code in a tenant app without context propagation', 'medium',
       'authorization',
       'A ThreadLocal tenant stays on the calling thread. @Async, CompletableFuture, coroutines, parallel streams, '
       'schedulers and listeners run without it - empty results at best, a stale tenant at worst. TaskDecorator, '
       'asContextElement() for coroutines, or the tenant as an explicit parameter.', security=True, owasp='A01')
define('SB-CACHE-NO-TENANT', 'Cache key without the tenant in a multi-tenant app', 'high', 'authorization',
       'The tenant is implicit (ThreadLocal, RLS, @TenantId), the cache key is not: tenant B gets what tenant A loaded, '
       'and a cache in front of RLS bypasses it. Global reference data (holidays, countries) is fine.',
       security=True, owasp='A01')
define('SB-TENANT-FILTER-BYID', 'Hibernate tenant filter does not cover load by id', 'high', 'authorization',
       '@Filter applies to queries only: findById, getReferenceById and EntityManager.find load rows of every tenant. '
       'Hibernate 6.6+ has @FilterDef(applyToLoadByKey = true); @TenantId covers both.', security=True, owasp='A01')
define('SB-TENANT-NATIVE-SQL', 'Native SQL on a tenant table without the tenant column', 'high', 'authorization',
       '@TenantId and @Filter do not reach native queries, JdbcTemplate or JdbcClient, and the table has no RLS. '
       'Check whether a join to a tenant-scoped parent restricts it.', security=True, owasp='A01')
define('SB-RLS-SESSION-SET', 'Tenant set per session on a pooled connection', 'high', 'authorization',
       'SET without LOCAL, or set_config(..., false), keeps the value on the connection when it goes back to the pool - '
       'the next transaction on it runs as the previous tenant. set_config(..., true) inside the transaction.',
       security=True, owasp='A01')
define('DB-RLS-NO-FORCE', 'Row level security without FORCE', 'medium', 'authorization',
       'The table owner bypasses RLS unless FORCE ROW LEVEL SECURITY is set. If the app connects as the role that ran '
       'the migrations, the policies never apply.', security=True, owasp='A01')
define('DB-TENANT-NO-RLS', 'Tenant table without row level security in an RLS schema', 'high', 'authorization',
       'The other tenant tables have a policy; these depend on every query remembering the tenant. Check each: '
       'cross-tenant by design (platform admin, outbox) or forgotten.', security=True, owasp='A01')
define('DB-TENANT-CONSTRAINT', 'Tenant column nullable, or a unique key without it', 'medium', 'persistence',
       'A nullable tenant column means "global" rows every query has to special-case. A unique key without the tenant '
       'lets one customer block a value for all others and tells them it exists.')
define('TESTGAP-TENANT', 'Multi-tenant app without a cross-tenant test', 'medium', 'testing',
       'No test acts as tenant A and asks for data of tenant B. That test is the only proof the isolation survives '
       'the next refactoring - with RLS, run it against the real database.', rule='TEST-4')

TENANT_COL = re.compile(r'^(tenant|mandant|organi[sz]ation|org)(_?id)?$')
TENANT_TABLE = re.compile(r'^(tenants?|mandant(en)?|organi[sz]ations?|organi[sz]ationen|orgs?)$')
CUSTOMER_COL = re.compile(r'^(kunden?|customer)_?id$')
CUSTOMER_TABLE = re.compile(r'^(kunden?|customers?)$')
CROSS_CUSTOMER_TEST = re.compile(r'(?i)(fremde|andere|zweite)[rnms]?[-_ ]?kunde|(other|foreign|second)[-_ ]?customer|'
                                 r'(kunde|customer)[-_ ]?b\b|(kunde|customer)\w*(isolation|isolierung|leak)')
TENANT_WORD = re.compile(r'(?i)tenant|mandant|organi[sz]ation')
CALLER_WORD = re.compile(r'(?i)tenant|mandant|organi[sz]ation|current_?user|user_?context|security_?context|'
                         r'principal|benutzer|caller')
WRITE_NAME = re.compile(r'(?i)^(save|create|update|delete|remove|add|insert|put|patch|set|change|modify|approve|'
                        r'reject|cancel|assign|move|archive|restore|import|upload|send|publish|submit|book|transfer|'
                        r'grant|revoke|reset|anlegen|aendern|ändern|loeschen|löschen|speichern|erstellen)')
WRITE_MAPPING = re.compile(r'@(Post|Put|Patch|Delete)Mapping\b')
AUTHZ_CLASS = re.compile(r'Permission|Authori[sz]|Access|Policy|Guard|Voter|Evaluator|Berechtigung|Rechte')
FAIL_OPEN = (
    (re.compile(r'\bcatch\s*\([^)]*\)\s*\{[^{}]{0,240}?\b(return\s+)?(true|AuthorizationDecision\s*\(\s*true\s*\)|'
                r'(AccessDecisionVoter\.)?ACCESS_GRANTED)\s*;?\s*\}'), 'high'),
    (re.compile(r'\.getOrDefault\s*\(\s*true\s*\)|\.getOrElse\s*\{\s*(\w+\s*->\s*)?true\s*\}|'
                r'onErrorReturn\s*\(\s*true\s*\)|onErrorReturn\s*\(\s*AuthorizationDecision\s*\(\s*true'), 'high'),
    (re.compile(r'\?:\s*true\b'), 'medium'),
)
BY_ID = re.compile(r'\.(findById|getReferenceById|getById|getOne|findAllById|existsById|deleteById)\s*\(|'
                   r'\b(em|entityManager|session)\s*\.\s*(find|get|getReference|load)\s*\(')
PROPAGATION = re.compile(r'TaskDecorator|DelegatingSecurityContext\w*|asContextElement|ThreadContextElement|'
                         r'MODE_INHERITABLETHREADLOCAL|ContextSnapshot|ContextRegistry|ThreadLocalAccessor')
ASYNC_CALL = re.compile(r'CompletableFuture\s*\.\s*(supplyAsync|runAsync)\s*[({]|\.parallelStream\s*\(\s*\)|'
                        r'\.parallel\s*\(\s*\)|GlobalScope\s*\.\s*(launch|async)\b|withContext\s*\(\s*Dispatchers\.|'
                        r'\b(launch|async)\s*\(\s*Dispatchers\.|\b\w*[Ee]xecutor\w*\s*\.\s*(submit|execute)\s*\(')
BACKGROUND = ('Scheduled', 'KafkaListener', 'RabbitListener', 'JmsListener', 'SqsListener')
NATIVE_API = re.compile(r'nativeQuery\s*=\s*true|createNativeQuery\s*\(|JdbcTemplate|JdbcClient|DSLContext')
SQL_TEXT = re.compile(r'(?is)^\s*(select|update|delete|insert|with)\b.*\b(from|into|set)\b')
SQL_TABLE = re.compile(r'(?i)\b(?:from|join|update|into)\s+([\w."]+)')
STRING = re.compile(r'"""([\s\S]*?)"""|"((?:\\.|[^"\\\n])*)"')
CALLER_TYPE = re.compile(r'Authentication|Principal|\bJwt\b|OidcUser|UserDetails')
CALLER_ANNO = re.compile(r'(?i)principal|user|caller|current|benutzer|tenant|mandant|auth')
DERIVED = re.compile(r'(?:find|get|exists|count|delete|read|query|search|stream|remove)\w*?By([A-Z]\w*)$')
CALLER_PART = re.compile(r'(?:^|_|(?<=[a-z]))(?:Owner|User|Creator|CreatedBy|Author|Member|Besitzer|Ersteller|Benutzer|'
                         r'Kunde|Customer|Tenant|Mandant|Organi[sz]ation|Org|Account|Subject|Principal)'
                         r'(?:Id|name|Name|Sub|Key|Schluessel|Email|Mail)?$')
ID_PART = re.compile(r'(?:^|_|(?<=[a-z]))(?:Id|Uuid|Ref|Slug|Key|Nummer|Number|Code|Token|Kennung|Schluessel)$')
SQL_ID = re.compile(r'(?i)(?<![\w.])(?:(?!(?:owner|user|creator|author|member|kunde|customer|tenant|mandant|org)\w*\.)\w+\.)?'
                    r'(?:id|uuid|unique_?id|ref|slug|nummer|number|code|token)\s*=\s*[:?]')
SQL_CALLER = re.compile(r'(?i)\b(?:owner|user|creator|created_?by|author|member|besitzer|ersteller|benutzer|kunde|customer|'
                        r'tenant|mandant|org|organi[sz]ation|account|subject)\w*(?:\.\w+)?\s*=\s*[:?]')
RETURN_OWNER = re.compile(r'returnObject\s*\.\s*\w*(owner|user|createdBy)')
MEMBER_TABLE = re.compile(r'_(member|members|membership|mitglied|mitglieder)$')
GUARD_CALL = re.compile(r'\b(?:assert(?!NotNull|Null|True|False|Equals|That)[A-Z]\w*|'
                        r'check\w*(?:Access|Permission|Owner|Member|Berechtigung|Zugriff)\w*|'
                        r'require(?!NotNull|Null)[A-Z]\w*)\s*\(|'
                        r'\b\w*(?:[Aa]ccess|[Gg]uard|[Pp]olicy|[Pp]ermissions?|[Bb]erechtigung\w*)\s*[?!]*\.\s*'
                        r'(?:assert|check|require|verify|ensure|can|may|darf|is[A-Z]|has[A-Z]|authori[sz]e)\w*\s*\(')
DENY_THROW = re.compile(r'\bthrow\s+(?:new\s+)?(?:AccessDeniedException|\w*Forbidden\w*)\b|HttpStatus\s*\.\s*FORBIDDEN\b')
INTERCEPTOR = re.compile(r'\b(?:Async)?HandlerInterceptor\b|HandlerInterceptorAdapter|WebRequestInterceptor')
DENY = re.compile(r'AccessDeniedException|HttpStatus\s*\.\s*(FORBIDDEN|UNAUTHORIZED|NOT_FOUND)|SC_(FORBIDDEN|UNAUTHORIZED)|'
                  r'sendError\s*\(|\breturn\s+false\b|ResponseStatusException')
CALLER_SRC = re.compile(r'(?i)SecurityContextHolder|getUserPrincipal|getRemoteUser|current_?user|principal|authentication')
PATH_SRC = re.compile(r'URI_TEMPLATE_VARIABLES_ATTRIBUTE|[pP]athVariables|getRequestURI|requestURI|getServletPath|servletPath')
SINGLE_ROLE = re.compile(r'^\s*"?\s*(?:has(?:Any)?(?:Role|Authority)\s*\(\s*([^,()]+?)\s*\)|\{?\s*"([\w:.-]+)"\s*\}?)\s*"?\s*$')
ADMIN_ROLE = re.compile(r'(?i)admin|manag|operat|staff|support|backoffice|intern|verwalt|super|root|betreib')
CLAIM = r'(?:getClaim\w*\s*\(\s*|claims\s*\[\s*|claims\s*\.\s*get\s*\(\s*)"{}"'
CONCEPTS = (
    ('rbac', re.compile(r'\b(hasRole|hasAnyRole)\s*\(|@Secured\b|@RolesAllowed\b|\bhas(Any)?Authority\s*\(\s*'
                        r'["\'](?!SCOPE_)'), 'role checks'),
    ('groups', re.compile(CLAIM.format('groups')), 'groups claim reads'),
    ('scopes', re.compile(r'SCOPE_\w+|hasScope\s*\('), 'scope checks'),
    ('abac', re.compile(r'\bPermissionEvaluator\b|\bAuthorizationManager\s*<|hasPermission\s*\(|'
                        r'@(Pre|Post)Authorize\s*\(\s*"[^"]*@\w+\.'), 'policy beans and permission evaluators'),
    ('uma', re.compile(r'\bAuthzClient\b|uma-ticket|org\.keycloak\.authorization'), 'Keycloak Authorization Services'),
    ('ownership', None, 'queries that combine an id with the caller'),
    ('rebac', re.compile(r'\bOpenFga\w*|dev\.openfga|com\.authzed|SpiceDb\w*'), 'relationship checks (OpenFGA, SpiceDB)'),
    ('acl', re.compile(r'\b(Mutable)?AclService\b|\bAclPermissionEvaluator\b'), 'Spring ACL'),
    ('policy-engine', re.compile(r'OpenPolicyAgent|\bopa[A-Z]\w*Client|com\.cedarpolicy'), 'external policy engine'),
)
CONVERTER = re.compile(r'realm_access|resource_access|JwtGrantedAuthoritiesConverter|Converter\s*<\s*Jwt\b')
TENANT_CLAIM = re.compile(CLAIM.format(r'(\w*(?:tenant|mandant|org)\w*)'), re.I)
CROSS_TENANT_TEST = re.compile(r'(?i)(tenant|mandant|organi[sz]ation)\w*(isolation|isolierung|leak)|cross[-_ ]?tenant|'
                               r'(other|foreign|second)[-_ ]?tenant|fremde[rnms]?[-_ ]?mandant|andere[rnms]?[-_ ]?mandant|'
                               r'zweite[rnms]?[-_ ]?mandant|(tenant|mandant)[-_ ]?b\b')


def _finally_spans(text: str) -> list[tuple[int, int]]:
    out = []
    for m in re.finditer(r'\bfinally\s*\{', text):
        end = balanced(text, m.end() - 1, '{', '}')
        out.append((m.end(), end if end > 0 else m.end() + 400))
    return out


def _label(j, m) -> str:
    return f'{m.owner.name if m.owner else j.name}.{m.name}'


def _anno_args(m, name: str) -> str | None:
    found = anno_args(m, re.compile(r'@' + name + r'\b'))
    return found[0][2] if found else None


def _tenant_col(t: dict, rx: re.Pattern = TENANT_COL) -> str | None:
    return next((c for c in sorted(t['columns']) if rx.match(c)), None)


def _documented(ctx, where: str | None) -> bool:
    """A comment between the previous statement and the CREATE TABLE that mentions RLS - the author decided."""
    if not where:
        return False
    rel, line = where.rsplit(':', 1)
    lines = ctx.repo.source(rel).lines
    i, block = int(line) - 2, []
    while i >= 0 and not lines[i].rstrip().endswith(';'):
        block.append(lines[i])
        i -= 1
    return any(re.search(r'(?i)\brls\b|row level|polic', l) for l in block if l.strip().startswith('--'))


def _callers(name: str) -> list[str]:
    """The caller criteria of a derived query that also takes an id, e.g. findByIdAndOwnerId -> [OwnerId]."""
    m = DERIVED.match(name)
    parts = re.split(r'And(?=[A-Z])', re.sub(r'(OrderBy|AllIgnoreCase)\w*$', '', m.group(1))) if m else []
    callers = [p for p in parts if CALLER_PART.search(p)]
    return callers if any(p not in callers and ID_PART.search(p) for p in parts) else []


def _queries(ctx) -> dict[str, set[str]]:
    out = {}
    for j in ctx.by['repository']:
        for m in j.methods():
            q = _anno_args(m, 'Query') or _anno_args(m, 'NativeQuery') or ''
            if SQL_ID.search(q) and SQL_CALLER.search(q):
                out.setdefault(m.name, set()).add(m.owner.name if m.owner else j.name)
    return out


def _scoped(j, x, queries: dict[str, set[str]]) -> list[int]:
    """Offsets of the calls and SQL strings in x that look up one row by its id and the caller together."""
    code, fields = j.body_text(x, 'code'), _fields(j, x.owner or j.cls)
    out = [m.start() for m in re.finditer(r'\b(\w+)\s*[?!]*\.\s*(\w+)\s*\(', code)
           if _callers(m.group(2)) or fields.get(m.group(1)) in queries.get(m.group(2), ())]
    for m in STRING.finditer(code):
        text = m.group(1) if m.group(1) is not None else m.group(2)
        if SQL_TEXT.search(text) and SQL_ID.search(text) and SQL_CALLER.search(text):
            out.append(m.start())
    return out


def _member_table(name: str, entity: dict | None, entities: dict) -> str | None:
    if not entity:
        return None
    caller = _callers(name)[0]
    if '_' in caller:
        prop = caller.split('_')[0]
        r = next((r for r in entity['relations'] if r['prop'] == prop[0].lower() + prop[1:]), None)
        if r and r['kind'] in ('OneToMany', 'ManyToMany', 'ElementCollection'):
            return (entities.get(r['target']) or {}).get('table') or r['target']
    return entity['table'] if MEMBER_TABLE.search(entity['table']) else None


def _guards(ctx, entities: dict) -> tuple[list, list]:
    """Membership checks (site, table, class) and owner checks (site) in interceptors and access classes."""
    classes, _ = _beans(ctx)
    members, owned = [], []
    for j in ctx.main:
        for c in j.classes:
            if not c.body or not (INTERCEPTOR.search(c.header) or AUTHZ_CLASS.search(c.name)):
                continue
            fields = _fields(j, c)
            for m in re.finditer(r'\b(\w+)\s*[?!]*\.\s*(\w+)\s*\(', j.src.code[c.body[0]:c.body[1]]):
                if not _callers(m.group(2)):
                    continue
                site = (j.rel, j.src.line_at(c.body[0] + m.start()))
                repo = classes.get(fields.get(m.group(1), ''))
                entity = re.search(r'Repository\s*<\s*(\w+)', repo[1].header) if repo else None
                table = _member_table(m.group(2), entities.get(entity.group(1)) if entity else None, entities)
                if table:
                    members.append((site, table, c.name))
                else:
                    owned.append(site)
    return members, owned


def concepts(ctx, tables: dict, owned: list[tuple[str, int]], members: list) -> list[dict]:
    out = []
    code = [(j, j.src.code) for j in ctx.main]
    for name, rx, label in CONCEPTS:
        where, count = None, 0
        if rx is None:
            count, where = len(owned), f'{owned[0][0]}:{owned[0][1]}' if owned else None
        for j, text in code if rx else []:
            for m in rx.finditer(text):
                count += 1
                where = where or f'{j.rel}:{j.src.line_at(m.start())}'
        if name == 'uma' and re.search(r'keycloak-authz-client', ctx.build):
            count, where = count or 1, where or 'build file: keycloak-authz-client'
        if count:
            entry = {'concept': name, 'where': where, 'count': count, 'signal': label}
            if name == 'rbac':
                conv = next((f'{j.rel}:{j.src.line_at(m.start())}' for j, text in code
                             for m in [CONVERTER.search(text)] if m), None)
                entry['converter'] = conv
            out.append(entry)
    names = list(dict.fromkeys([t for _, t, _ in members] +
                               sorted(n for n, t in tables.items() if MEMBER_TABLE.search(n) and t['fks'])))
    if names:
        (rel, line), table, _ = members[0] if members else ((None, None), None, None)
        out.append({'concept': 'membership', 'where': f'{rel}:{line} ({table})' if table else ', '.join(names[:6]),
                    'count': len(names), 'signal': 'membership tables (simple ReBAC)', 'tables': names,
                    'checked_by': sorted({g for *_, g in members})})
    return out


def _holders(ctx) -> list[dict]:
    out = []
    for j in ctx.main:
        for m in re.finditer(r'(\w+)\s*(?::\s*[^=\n]+)?=\s*(?:new\s+)?(?:Named)?(Inheritable)?ThreadLocal\b', j.src.bare):
            var = m.group(1)
            owner = next((c.name for c in j.classes if c.body and c.body[0] <= m.start() <= c.body[1]), j.name)
            line = j.src.line(j.src.line_at(m.start()))
            if not CALLER_WORD.search(f'{var} {owner} {line} {j.rel.rsplit("/", 1)[-1]}'):
                continue
            remove = re.search(r'\b' + re.escape(var) + r'\s*\??\.\s*remove\s*\(', j.src.bare)
            clear = next((f.name for f in j.methods() if remove and f.body and f.body[0] <= remove.start() <= f.body[1]),
                         None)
            out.append({'jf': j, 'offset': m.start(), 'var': var, 'owner': owner, 'clear': clear,
                        'removed': bool(remove), 'inheritable': bool(m.group(2)),
                        'tenant': bool(TENANT_WORD.search(f'{var} {owner} {line}'))})
    return out


def check_threadlocals(ctx, holders: list[dict]):
    finals = {j.rel: _finally_spans(j.src.bare) for j in ctx.main}
    for h in holders:
        label = f'{h["owner"]}.{h["var"]}'
        if h['inheritable']:
            ctx.hit('SB-TENANT-THREADLOCAL', h['jf'], h['offset'],
                    f'{label}: InheritableThreadLocal - copied into every pool thread created while it is set')
            continue
        if not h['removed']:
            ctx.hit('SB-TENANT-THREADLOCAL', h['jf'], h['offset'], f'{label}: set, never removed')
            continue
        names = [re.escape(h['var']) + r'\s*\??\.\s*remove'] + ([re.escape(h['clear'])] if h['clear'] else [])
        calls = re.compile(r'\b(' + '|'.join(names) + r')\s*\(')
        reliable = False
        for j in ctx.main:
            for m in calls.finditer(j.src.bare):
                in_method = next((f.name for f in j.methods() if f.body and f.body[0] <= m.start() <= f.body[1]), '')
                in_finally = any(a <= m.start() <= b for a, b in finals[j.rel])
                if in_finally or in_method in ('afterCompletion', 'requestDestroyed'):
                    reliable = True
        if not reliable:
            ctx.hit('SB-TENANT-THREADLOCAL', h['jf'], h['offset'], severity='medium',
                    evidence=f'{label}: removed in {h["clear"] or "?"}(), but no call to it sits in a finally block')


def check_context_lost(ctx, holders: list[dict]):
    tenant = [h for h in holders if h['tenant']]
    if not tenant or PROPAGATION.search(ctx.all_main + ctx.config_text):
        return
    names = {h['owner'] for h in tenant}
    holder = re.compile(r'\b(' + '|'.join(map(re.escape, names)) + r')\b')
    for j in ctx.main:
        for m in j.methods():
            if m.has('Async'):
                ctx.hit('SB-TENANT-CONTEXT-LOST', j, m.anno_offset, f'@Async {_label(j, m)} - runs on a pool thread')
                continue
            body = j.src.bare[m.owner.body[0]:m.owner.body[1]] if m.owner and m.owner.body else j.src.bare
            if m.has(*BACKGROUND) and not (holder.search(body) or TENANT_WORD.search(body)):
                anno = next(a for a in m.annos if a in BACKGROUND)
                ctx.hit('SB-TENANT-CONTEXT-LOST', j, m.anno_offset,
                        f'@{anno} {_label(j, m)} - the class never sets or names a tenant')
        for m in ASYNC_CALL.finditer(j.src.bare):
            ctx.hit('SB-TENANT-CONTEXT-LOST', j, m.start())


def check_caches(ctx, implicit: bool):
    if not implicit:
        return
    for j in ctx.main:
        class_cfg = ' '.join(_anno_args(c, 'CacheConfig') or '' for c in j.classes)
        for m in j.methods():
            args = _anno_args(m, 'Cacheable')
            args = args if args is not None else _anno_args(m, 'CachePut')
            if args is None or 'keyGenerator' in args + class_cfg:
                continue
            key = re.search(r'\bkey\s*=\s*"([^"]*)"', args)
            if key and TENANT_WORD.search(key.group(1)):
                continue
            if not key and any(TENANT_WORD.search(f'{p.name} {p.type}') for p in m.params):
                continue
            ctx.hit('SB-CACHE-NO-TENANT', j, m.anno_offset,
                    f'{_label(j, m)}({", ".join(p.name for p in m.params)})  key={key.group(1) if key else "all params"}')


def check_method_security(ctx):
    for j in ctx.main:
        for m in j.methods():
            post = _anno_args(m, 'PostAuthorize')
            if post is not None and (WRITE_NAME.match(m.name) or WRITE_MAPPING.search(m.anno_text)):
                ctx.hit('SB-POSTAUTHORIZE-WRITE', j, m.anno_offset, f'{_label(j, m)}  @PostAuthorize({post[:80]})')
            if m.has('PostFilter'):
                ctx.hit('SB-POSTFILTER', j, m.anno_offset, f'{_label(j, m)} -> {m.returns or "?"}')
            for name in ('PreAuthorize', 'PostAuthorize'):
                expr = _anno_args(m, name)
                operators = len(re.findall(r'\b(and|or)\b|&&|\|\|', expr or ''))
                if operators >= 3 or (operators == 2 and len(expr) > 120):
                    ctx.hit('SB-PREAUTH-COMPLEX', j, m.anno_offset, f'{_label(j, m)}  @{name}({expr[:120]})')


def check_fail_open(ctx):
    for j in ctx.main:
        for c in j.classes:
            if not c.body or not (AUTHZ_CLASS.search(c.name) or
                                  re.search(r'PermissionEvaluator|AuthorizationManager|AccessDecisionVoter', c.header)):
                continue
            body = j.src.bare[c.body[0]:c.body[1]]
            for rx, sev in FAIL_OPEN:
                for m in rx.finditer(body):
                    ctx.hit('SB-AUTHZ-FAIL-OPEN', j, c.body[0] + m.start(), severity=sev)


def check_issuer(ctx):
    for j in ctx.main:
        code = j.src.code
        for m in re.finditer(r'fromTrustedIssuers\s*(\(\s*)?(\{\s*(\w+\s*->\s*)?true\s*\}|\w+\s*->\s*true\b)', code):
            ctx.hit('SB-ISSUER-FROM-TOKEN', j, m.start())
        if not re.search(r'JWTParser\s*\.\s*parse|JwtIssuer(Reactive)?AuthenticationManagerResolver\s*(\(\s*)?\{|'
                         r'AuthenticationManagerResolver\s*<\s*String', code):
            continue
        if re.search(r'(?i)(?<!from)trusted|allowed|allow-?list|whitelist|known\w*issuers|\.containsKey\s*\(|\[\s*issuer\s*\]|'
                     r'\.get\s*\(\s*issuer\s*\)|startsWith\s*\(|\bin\s+\w*issuers', code):
            continue
        for m in re.finditer(r'(fromIssuerLocation|fromOidcIssuerLocation|withIssuerLocation|withJwkSetUri)\s*'
                             r'(<[^>(]*>)?\s*\(\s*(?!")', code):
            ctx.hit('SB-ISSUER-FROM-TOKEN', j, m.start())


def check_token_relay(ctx):
    incoming = re.compile(r'getHeader\s*\(\s*(HttpHeaders\.AUTHORIZATION|"Authorization")|\.tokenValue\b|'
                          r'getTokenValue\s*\(')
    outgoing = re.compile(r'setBearerAuth\s*\(|\.header\s*\(\s*(HttpHeaders\.AUTHORIZATION|"Authorization")|'
                          r'headers?\s*\.\s*(set|add)\s*\(\s*(HttpHeaders\.AUTHORIZATION|"Authorization")')
    for j in ctx.main:
        code = j.src.code
        if not re.search(r'RequestInterceptor|ClientHttpRequestInterceptor|ExchangeFilterFunction|RestTemplate|'
                         r'RestClient|WebClient|RequestTemplate', code):
            continue
        if re.search(r'clientCredentials|OAuth2AuthorizedClientManager|OAuth2ClientHttpRequestInterceptor|'
                     r'ServerOAuth2AuthorizedClientExchangeFilterFunction|ServletOAuth2AuthorizedClientExchangeFilterFunction',
                     code) or not incoming.search(code):
            continue
        out = outgoing.search(code)
        if out:
            ctx.hit('SB-TOKEN-RELAY', j, out.start())


def check_filters(ctx, tenant_tables: set[str], rls: set[str]):
    conditions = {}
    for name, cond in re.findall(r'@Filter\s*\(\s*name\s*=\s*"([^"]+)"\s*,\s*condition\s*=\s*"([^"]*)"',
                                 ctx.all_main_code):
        conditions[name] = conditions.get(name, '') + ' ' + cond
    defs = []
    for j in ctx.main:
        for m in re.finditer(r'@FilterDef\s*\(', j.src.code):
            close = balanced(j.src.bare, m.end() - 1)
            args = j.src.code[m.end():close if close > 0 else m.end() + 300]
            name = re.search(r'\bname\s*=\s*"([^"]+)"', args)
            if name and TENANT_WORD.search(f'{name.group(1)} {args} {conditions.get(name.group(1), "")}'):
                defs.append((j, m.start(), name.group(1), bool(re.search(r'applyToLoadByKey\s*=\s*true', args))))
    if not defs:
        return []
    sites = [(j.rel, j.src.line_at(m.start())) for j in ctx.main for m in BY_ID.finditer(j.src.bare)]
    covered = bool(tenant_tables) and rls >= tenant_tables
    for j, offset, name, by_key in defs:
        if by_key or not sites:
            continue
        ctx.hit('SB-TENANT-FILTER-BYID', j, offset,
                f'filter {name} without applyToLoadByKey; {len(sites)} load-by-id calls in '
                f'{len({f for f, _ in sites})} files' + (' (RLS on the tables is the net)' if covered else ''),
                severity='medium' if covered else None, files=sorted({f'{f}:{l}' for f, l in sites})[:40])
    return [name for _, _, name, _ in defs]


def check_native_sql(ctx, tables: dict, tenant_tables: dict[str, str], rls: set[str]):
    exposed = {t: c for t, c in tenant_tables.items() if t not in rls}
    if not exposed:
        return
    for j in ctx.main:
        code = j.src.code
        if not NATIVE_API.search(code):
            continue
        jpql = [] if 'nativeQuery' in code else [(m.start(), balanced(j.src.bare, m.end() - 1))
                                                  for m in re.finditer(r'@Query\s*\(', code)]
        seen = set()
        for m in STRING.finditer(code):
            text = m.group(1) if m.group(1) is not None else m.group(2)
            if not SQL_TEXT.search(text) or any(a <= m.start() <= b for a, b in jpql):
                continue
            end = m.end()
            while more := re.match(r'\s*\+\s*' + STRING.pattern, code[end:]):
                text += more.group(1) if more.group(1) is not None else more.group(2)
                end += more.end()
            for raw in SQL_TABLE.findall(text):
                table = schema._name(raw)
                col = exposed.get(table)
                if not col or table in seen or re.search(r'\b' + col + r'\b', text, re.I) or TENANT_WORD.search(text):
                    continue
                seen.add(table)
                deliberate = _documented(ctx, tables.get(table, {}).get('file'))
                ctx.hit('SB-TENANT-NATIVE-SQL', j, m.start(), f'{table} without {col}: {text.strip()[:110]}',
                        **({'severity': 'low', 'note': 'the migration documents the table as cross-tenant'}
                           if deliberate else {}))


def check_session_set(ctx):
    rx = re.compile(r'(?i)["\'`]\s*set\s+(?:session\s+)?(?!local\b)[a-z_]+\.[a-z_]+\s*(=|\bto\b)|'
                    r'set_config\s*\(\s*\'[^\']+\'\s*,[^)]*?,\s*false\s*\)')
    for j in ctx.main:
        for m in rx.finditer(j.src.code):
            ctx.hit('SB-RLS-SESSION-SET', j, m.start())


def check_rls(ctx, tables: dict, tenant_tables: dict[str, str]):
    rls = {n for n, t in tables.items() if t['rls']}
    if not rls:
        return rls
    loose = sorted(n for n in rls if not tables[n]['force'])
    if loose:
        separate = any(e.norm.endswith(('flyway.user', 'liquibase.user')) for src, entries in ctx.configs
                       if not is_test_path(src.rel) for e in entries)
        rel, line = tables[loose[0]]['rls'].rsplit(':', 1)
        ctx.hit('DB-RLS-NO-FORCE', rel, int(line), f'{len(loose)} of {len(rls)} RLS tables without FORCE: '
                + ', '.join(loose[:8]) + ('' if separate else '; migrations run as the app user'),
                severity='medium' if separate else 'high')
    missing = sorted(n for n in tenant_tables if n not in rls)
    if missing:
        documented = [n for n in missing if _documented(ctx, tables[n]['file'])]
        open_ = [n for n in missing if n not in documented]
        first = tables[(open_ or documented)[0]]['file'] or ':'
        rel, line = first.rsplit(':', 1)
        ctx.hit('DB-TENANT-NO-RLS', rel or None, int(line) if line else None,
                f'{len(missing)} of {len(tenant_tables)} tenant tables without RLS: ' + ', '.join(open_[:10])
                + (f'; documented as deliberate: {", ".join(documented[:6])}' if documented else ''),
                severity=None if open_ else 'low', names=missing)
    return rls


def check_constraints(ctx, tables: dict, tenant_tables: dict[str, str]):
    nullable, unique = [], []
    for name, col in sorted(tenant_tables.items()):
        t = tables[name]
        if col not in t['notnull'] and col not in t['pk']:
            nullable.append(name)
        fk_cols = {c for cols, *_ in t['fks'] for c in cols}
        for cols in t['unique']:
            if col in cols or set(cols) & (t['pk'] | fk_cols) or any('(' in c or re.search(
                    r'token|hash|sub$|uuid|guid|external|keycloak|key$', c) for c in cols):
                continue
            unique.append(f'{name}({", ".join(cols)})')
    for items, label in ((nullable, 'tenant column nullable'), (unique, 'unique without the tenant')):
        if items:
            rel, line = (tables[items[0].split('(')[0]]['file'] or ':').rsplit(':', 1)
            ctx.hit('DB-TENANT-CONSTRAINT', rel or None, int(line) if line else None,
                    f'{label}: ' + ', '.join(items[:10]) + (f' (+{len(items) - 10})' if len(items) > 10 else ''))


def _interceptor_class(arg: str, fields: dict[str, str], j, cls) -> str | None:
    new = re.match(r'(?:new\s+)?([A-Z]\w*)\s*[(<{]', arg)
    if new:
        return new.group(1)
    ref = re.fullmatch(r'(?:this\s*\.\s*)?(\w+)\s*(\(\s*\))?', arg)
    if not ref:
        return None
    if not ref.group(2):
        return fields.get(ref.group(1))
    bean = next((m for m in j.methods(cls) if m.name == ref.group(1)), None)
    if not bean:
        return None
    made = re.search(r'\b([A-Z]\w*)\s*\(', j.body_text(bean, 'code'))
    return made.group(1) if made else re.sub(r'[<?].*', '', bean.returns).strip() or None


def interceptors(ctx) -> list[dict]:
    """addInterceptors(registry): which guard interceptor runs on which paths; marks the endpoints it covers."""
    classes, _ = _beans(ctx)
    consts, out = None, []
    for j in ctx.main:
        for m in j.methods():
            if m.name != 'addInterceptors' or not m.body:
                continue
            consts = consts if consts is not None else string_consts(ctx)
            cls = m.owner or j.cls
            bare, code = j.src.bare, j.src.code
            for a in re.compile(r'\baddInterceptor\s*\(').finditer(bare, m.body[0], m.body[1]):
                close = balanced(bare, a.end() - 1)
                name = _interceptor_class(code[a.end():close].strip(), _fields(j, cls), j, cls) if close > 0 else None
                found = classes.get(name or '')
                body = found[0].src.code[found[1].body[0]:found[1].body[1]] if found and found[1].body else ''
                if not (DENY.search(body) and CALLER_SRC.search(body) and PATH_SRC.search(body)):
                    continue
                calls, k = [], close + 1
                while c := re.match(r'\s*\.\s*(\w+)\s*\(', bare[k:]):
                    end = balanced(bare, k + c.end() - 1)
                    if end < 0:
                        break
                    calls.append((c.group(1), code[k + c.end():end]))
                    k = end + 1
                var = re.search(r'(\w+)\s*(?::\s*\w+)?\s*=\s*\w+\s*\.\s*$', bare[m.body[0]:a.start()].rsplit('\n', 1)[-1])
                if var:
                    for c in re.compile(r'\b' + var.group(1) + r'\s*\.\s*(\w+PathPatterns)\s*\(').finditer(bare, k, m.body[1]):
                        calls.append((c.group(1), code[c.end():balanced(bare, c.end() - 1)]))
                include = [v for n, args in calls if n == 'addPathPatterns' for v in string_values(args, consts)
                           if '{const}' not in v] or ['/**']
                exclude = [v for n, args in calls if n == 'excludePathPatterns' for v in string_values(args, consts)
                           if '{const}' not in v]
                covered = 0
                for e in ctx.endpoints:
                    key = re.sub(r'\{[^}]*\}', 'x', e['path'])
                    if _matches(include, key) and not _matches(exclude, key):
                        e.setdefault('covered_by', []).append(name)
                        covered += 1
                out.append({'class': name, 'where': f'{found[0].rel}:{found[1].line}',
                            'registered': f'{j.rel}:{j.src.line_at(a.start())}', 'include': include, 'exclude': exclude,
                            'endpoints': covered})
    return out


def _admin_only(e: dict) -> bool:
    for text in [e.get('url_rule_text') or ''] + e['auth_text']:
        role = SINGLE_ROLE.match(text)
        if role and (ADMIN_ROLE.search(role.group(1) or role.group(2)) or re.match(r'/admin\b', e['path'])):
            return True
    return False


def object_access(ctx, reach: dict, queries: dict[str, set[str]], tenant_app: bool) -> list[dict]:
    out = []
    for e in ctx.endpoints:
        m = e.get('_member')
        if m is None or '{' not in e['path'] or e.get('url_rule') in ('permitAll', 'anonymous', 'denyAll') or \
                e.get('covered_by') or re.search(r'#\w|authentication|principal|@\w+\.', ' '.join(e['auth_text'])):
            continue
        admin = _admin_only(e)
        if admin and not tenant_app:
            continue
        pairs = reach[id(m)]
        if any(GUARD_CALL.search(code) or DENY_THROW.search(code) or re.search(r'@PreAuthorize\s*\(\s*"[^"]*#\w', x.anno_code)
               or _scoped(j, x, queries) for j, x in pairs for code in [j.body_text(x, 'code')]):
            continue
        caller = any(CALLER_TYPE.search(p.type or '') or any(CALLER_ANNO.search(a) for a in p.annos) for p in m.params)
        out.append({'http': e['http'], 'path': e['path'], 'handler': f'{e["controller"]}.{e["method"]}',
                    'rule': e.get('url_rule') or '-', 'where': f'{e["file"]}:{e["line"]}', 'caller': caller,
                    'admin': admin})
    return sorted(out, key=lambda x: (x['admin'], not x['caller'], x['http'] == 'GET', x['path']))


def run(ctx, entities: list[dict]) -> dict:
    tables = (getattr(ctx, 'migrations', None) or schema.migrations(ctx.repo))['tables']
    tenant_tables = {n: c for n, t in tables.items() for c in [_tenant_col(t)] if c and not TENANT_TABLE.match(n)}
    customer = {n: c for n, t in tables.items() for c in [_tenant_col(t, CUSTOMER_COL)] if c and not CUSTOMER_TABLE.match(n)}
    by_customer = not tenant_tables and len(customer) >= 3
    tenant_tables = customer if by_customer else tenant_tables
    for e in entities or []:
        src = ctx.repo.source(e['file']).bare
        if e['table'] not in tables and not TENANT_TABLE.match(e['table']) and \
                re.search(r'@TenantId\b|\b(tenant|mandant)(Id)?\s*[:;=]', src):
            tenant_tables[e['table']] = 'tenant_id'
    holders = _holders(ctx)
    ctx.all_main_code = '\n'.join(j.src.code for j in ctx.main)
    tenant_id = re.search(r'@TenantId\b', ctx.all_main)
    routing = re.search(r'CurrentTenantIdentifierResolver|MultiTenantConnectionProvider|AbstractRoutingDataSource',
                        ctx.all_main)
    rls = check_rls(ctx, tables, tenant_tables)
    filters = check_filters(ctx, set(tenant_tables), rls)
    implicit = bool(any(h['tenant'] for h in holders) or rls or tenant_id or filters or routing)
    tenant_app = implicit or len(tenant_tables) >= 2

    check_method_security(ctx)
    check_fail_open(ctx)
    check_issuer(ctx)
    check_token_relay(ctx)
    check_threadlocals(ctx, holders)
    check_session_set(ctx)
    if tenant_app:
        check_context_lost(ctx, holders)
        check_caches(ctx, implicit)
        if implicit:
            check_native_sql(ctx, tables, tenant_tables, rls)
        check_constraints(ctx, tables, tenant_tables)
        cross = CROSS_CUSTOMER_TEST if by_customer else CROSS_TENANT_TEST
        if ctx.tests and not any(cross.search(s.rel + '\n' + s.text) for s in ctx.tests):
            ctx.hits.add('TESTGAP-TENANT', None, None, f'{len(tenant_tables)} tenant tables, '
                         f'{len(ctx.tests)} test files, none acts as a second tenant')

    model = []
    if re.search(r'JwtIssuer(Reactive)?AuthenticationManagerResolver|AuthenticationManagerResolver\s*<', ctx.all_main):
        model.append('realm per tenant (issuer resolver)')
    if re.search(CLAIM.format('organization'), ctx.all_main_code) or re.search(r'organization:', ctx.config_text):
        model.append('Keycloak Organizations')
    claims = sorted({m.group(1) for m in TENANT_CLAIM.finditer(ctx.all_main_code)} - {'organization'})
    if claims:
        model.append('claim ' + ', '.join(claims[:3]))
    headers = [h for h in ctx.hits.items if h['check'] == 'SB-HEADER-TRUST' and TENANT_WORD.search(h['evidence'])]
    if headers:
        model.append('request header')
    paths = [e for e in ctx.endpoints if re.search(r'(?i)\{(tenant|mandant|org)\w*\}', e['path'])]
    if paths:
        model.append(f'path variable ({len(paths)} endpoints)')
    if by_customer:
        model.append(f'customer as tenant ({sorted(set(tenant_tables.values()))[0]})')
    isolation = []
    if rls:
        isolation.append(f'RLS on {len(rls & set(tenant_tables))} of {len(tenant_tables)} tenant tables '
                         f'({sum(1 for n in rls if tables[n]["force"])} forced)')
    if tenant_id:
        isolation.append('@TenantId')
    if filters:
        isolation.append('Hibernate filter ' + ', '.join(filters[:2]))
    if routing:
        isolation.append(f'{routing.group(0)} (schema or database per tenant)')
    if tenant_tables and not (rls or tenant_id or filters or routing):
        isolation.append(f'tenant column in {len(tenant_tables)} tables, every query on its own')
    boot = ctx.boot()
    hibernate = {(3, 0): '6.1', (3, 1): '6.2', (3, 2): '6.4', (3, 3): '6.5', (3, 4): '6.6', (3, 5): '6.6'}.get(
        boot[:2], {2: '5', 3: '6', 4: '7'}.get(boot[0]))
    covered = interceptors(ctx)
    queries = _queries(ctx)
    reach = {id(e['_member']): delegates(ctx, e['_jf'], e['_member']) for e in ctx.endpoints if e.get('_member') is not None}
    members, owned = _guards(ctx, {e['entity']: e for e in entities or []})
    for pairs in reach.values():
        owned += [(j.rel, j.src.line_at(x.body[0] + at)) for j, x in pairs for at in _scoped(j, x, queries)]
    owned += [(j.rel, j.src.line_at(m.start())) for j in ctx.main for m in RETURN_OWNER.finditer(j.src.code)]
    return {'concepts': concepts(ctx, tables, sorted(set(owned)), members),
            'tenancy': {'tenant_app': tenant_app, 'model': model, 'isolation': isolation,
                        'tenant_tables': len(tenant_tables),
                        'holders': [f'{h["owner"]}.{h["var"]} ({h["jf"].rel})' for h in holders]},
            'hibernate': f'{hibernate} (from Boot {ctx.stack.get("boot")})' if hibernate else None,
            'interceptors': covered,
            'object_access': object_access(ctx, reach, queries, tenant_app)}
