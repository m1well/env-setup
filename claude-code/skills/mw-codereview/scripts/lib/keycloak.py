"""Keycloak hardening: the Spring resource server, the admin client, realm exports, the server image, keycloak-js."""
from __future__ import annotations

import json
import os
import re

from .core import Hits, Repo, define, entropy, is_test_path, profile_kind, redact, strings_in, version_tuple

define('KC-LEGACY-ADAPTER', 'Keycloak Spring adapter (deprecated since Keycloak 17, no fixes)', 'high', 'supply-chain',
       'keycloak-spring-boot-starter and the security adapters get no security fixes. The replacement is '
       'spring-boot-starter-oauth2-resource-server (or -client for a BFF).', security=True, owasp='A03')
define('KC-ROLES-UNMAPPED', 'Role checks on Keycloak tokens, but no converter reads the Keycloak role claims',
       'medium', 'authorization',
       'Spring maps only the scope claim (SCOPE_*). Keycloak roles sit in realm_access.roles and '
       'resource_access.<client>.roles. Without a converter every hasRole check fails closed - and the usual '
       'workaround is loosening it to authenticated().', security=True, rule='SEC-2', owasp='A01')
define('KC-ANY-REALM-USER', 'Keycloak API that only checks authenticated()', 'high', 'authorization',
       'Every account of the realm passes: users of other clients, test users, self-registered accounts. '
       'Check whether the realm holds only users of this app and whether registration is off.',
       security=True, rule='SEC-2', owasp='A01')
define('KC-NO-AUDIENCE', 'Keycloak tokens accepted without an audience or azp check', 'medium', 'authentication',
       'All clients of a realm share issuer and keys. Without aud (jwt.audiences, a JwtClaimValidator) or an '
       'azp check, a token minted for another client of the realm works here.', security=True, owasp='A07')
define('KC-JWK-ONLY', 'jwk-set-uri without issuer-uri - the issuer is not validated', 'medium', 'authentication',
       'With only jwk-set-uri Boot validates signature and time, not iss. Set issuer-uri (or add the '
       'issuer validator).', security=True, owasp='A07')
define('KC-ISSUER-HTTP', 'Keycloak URL over plain http outside of local development', 'medium', 'crypto',
       'Check the profile and whether TLS terminates in front of Keycloak.', security=True, owasp='A04')
define('KC-ADMIN-GRANT', 'Admin API reached with an admin user, admin-cli or the master realm', 'high',
       'authentication',
       'The app then holds credentials that administer the realm. A confidential client with a service '
       'account and only view-users/manage-users from realm-management is the fix.', security=True, owasp='A07')
define('KC-MUTABLE-USER-KEY', 'preferred_username or email used from the token', 'medium', 'authorization',
       'Fine for display. A finding when it is the key ownership is stored or looked up by - both change in '
       'Keycloak, sub does not.', security=True, owasp='A01')
define('KC-LOGOUT-LOCAL', 'oauth2Login against Keycloak without OIDC logout', 'medium', 'authentication',
       'Logout ends only the local session; the Keycloak SSO session lives on and the next login is silent. '
       'OidcClientInitiatedLogoutSuccessHandler, or oidcLogout for back-channel.', security=True, owasp='A07')
define('KC-ROLE-MISMATCH', 'Role checked in the frontend that no backend rule checks', 'medium', 'authorization',
       'The UI hides something the API may serve to every user. Find the endpoint behind the view and its rule.',
       security=True, owasp='A01')
define('KC-REALM-SSL', 'Realm with sslRequired none', 'high', 'crypto',
       'Passwords and tokens over plain http. A local import is fine - check whether this file reaches '
       'a shared or production Keycloak.', security=True, owasp='A04')
define('KC-REALM-BRUTE-FORCE', 'Realm without brute force detection', 'medium', 'authentication',
       'Login attempts are unlimited.', security=True, owasp='A07')
define('KC-REALM-PASSWORD-POLICY', 'Realm without a password policy', 'low', 'authentication',
       'length(12) and notUsername are the minimum; check whether login goes through an external IdP instead.',
       security=True, owasp='A07')
define('KC-REALM-TOKENS', 'Long-lived or reusable tokens in the realm', 'low', 'authentication',
       'Access tokens beyond 15 minutes, refresh tokens that are not rotated for public clients.',
       security=True, owasp='A07')
define('KC-REALM-REGISTRATION', 'Self-registration enabled', 'medium', 'authentication',
       'Anyone can create an account - every check that is only authenticated() is open to the internet.',
       security=True, owasp='A01')
define('KC-REALM-USERS', 'Users with passwords in a realm export', 'medium', 'secrets',
       'Test accounts are fine in a local import. In a file that seeds a shared Keycloak they are live logins.',
       security=True, rule='SEC-5', owasp='A07')
define('KC-REALM-EVENTS', 'Login and admin events not recorded', 'low', 'logging',
       'No trail of failed logins or admin changes.', security=True, owasp='A09')
define('KC-CLIENT-REDIRECT', 'Client redirect URI or web origin with a wildcard', 'high', 'authorization',
       'A wildcard redirect sends the authorization code wherever the attacker points it. List exact URIs.',
       security=True, owasp='A01')
define('KC-CLIENT-IMPLICIT', 'Implicit flow enabled on a client', 'high', 'authentication',
       'Removed in OAuth 2.1 - tokens travel in the URL fragment. Authorization code with PKCE.',
       security=True, owasp='A07')
define('KC-CLIENT-DIRECT-GRANT', 'Direct access grants (password grant) enabled', 'medium', 'authentication',
       'The client sees the password, brute force protection and MFA are bypassed. Often left on for e2e tests '
       '- then it belongs in a test client only.', security=True, owasp='A07')
define('KC-CLIENT-NO-PKCE', 'Public client without enforced PKCE', 'medium', 'authentication',
       'Set pkce.code.challenge.method = S256 on the client, so Keycloak rejects code requests without it.',
       security=True, owasp='A07')
define('KC-CLIENT-SECRET', 'Client secret in a realm export', 'high', 'secrets',
       'A committed secret is leaked. A local import with a dev secret is low.', security=True, rule='SEC-5',
       owasp='A07')
define('KC-CLIENT-FULL-SCOPE', 'Clients with full scope allowed', 'low', 'authorization',
       'Every token carries every realm role and all client roles the user has - for all apps of the realm.',
       security=True, owasp='A01')
define('KC-SERVICE-ACCOUNT-ADMIN', 'Service account with realm-wide admin roles', 'high', 'authorization',
       'Whoever holds the client secret administers the realm. manage-users and view-users are usually enough.',
       security=True, owasp='A01')
define('KC-REALM-LOCAL', 'Local realm import - what to harden before it seeds a shared Keycloak', 'low', 'config',
       'Lax settings are normal for a laptop. The list is the checklist for the realm that serves real users: '
       'compare it with the production realm, or the import that creates it.', security=True, owasp='A02')
define('KC-START-DEV', 'Keycloak started with start-dev', 'high', 'config',
       'Dev mode: plain http, an in-memory H2, relaxed hostname checks. Fine in a local compose file only.',
       security=True, owasp='A02')
define('KC-IMAGE-OLD', 'Keycloak image below the supported major', 'high', 'supply-chain',
       'Only the current Keycloak major gets security fixes.', security=True, owasp='A03')
define('KC-JS-FLOW', 'Implicit or hybrid flow in the frontend OIDC client', 'high', 'authentication',
       'Tokens in the URL fragment end up in history and logs. flow: standard with PKCE.', security=True,
       owasp='A07')
define('KC-JS-NO-PKCE', 'keycloak-js without PKCE', 'medium', 'authentication',
       'keycloak-js below 26 does not use PKCE unless pkceMethod: \'S256\' is set.', security=True, owasp='A07')
define('KC-JS-NO-REFRESH', 'keycloak-js without token refresh', 'medium', 'resilience',
       'The access token expires after the realm\'s access token lifespan; every call fails until a reload. '
       'updateToken() before requests, or keycloak-angular\'s auto refresh.')

KC_CURRENT_MAJOR = 26
BUILTIN_CLIENTS = {'account', 'account-console', 'admin-cli', 'broker', 'realm-management',
                   'security-admin-console'}
LOCAL_URL = re.compile(r'^(https?://)?(localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]|host\.docker\.internal)\b')
DEV_PATH = re.compile(r'(?i)(^|[/_.-])(local|dev|develop|test|e2e|it|playground|demo|sample|example|mock)([/_.-]|$)')
ADMIN_ROLES = {'realm-admin', 'manage-realm', 'manage-clients', 'manage-authorization', 'impersonation',
               'manage-identity-providers'}
AUD_GUARD = re.compile(r'"azp"|\bazp\b|"aud"|\.audience\b|getAudience\s*\(|JwtClaimValidator|AudienceValidator|'
                       r'JwtAudienceValidator|OAuth2TokenValidator')
ROLE_RULE = re.compile(r'\b(hasRole|hasAnyRole|hasAuthority|hasAnyAuthority)\s*\(([^)]*)\)')


def _realm_docs(repo: Repo) -> list[tuple[str, dict]]:
    out = []
    for rel in repo.by_ext('.json'):
        name = os.path.basename(rel)
        if name.startswith(('package', 'tsconfig', 'project.json', 'angular.json', 'nx.json')):
            continue
        text = repo.source(rel).text
        if '"realm"' not in text[:20000] or not re.search(r'"(clients|roles|users|sslRequired)"', text):
            continue
        try:
            data = json.loads(text)
        except ValueError:
            continue
        for doc in data if isinstance(data, list) else [data]:
            if isinstance(doc, dict) and isinstance(doc.get('realm'), str):
                out.append((rel, doc))
    return out


def _line(repo: Repo, rel: str, needle: str, after: str | None = None) -> int | None:
    lines = repo.source(rel).lines
    start = 0
    if after:
        start = next((i for i, l in enumerate(lines) if after in l), 0)
    return next((i + 1 for i, l in enumerate(lines[start:], start) if needle in l), None)


def _custom_clients(doc: dict) -> list[dict]:
    return [c for c in doc.get('clients') or [] if isinstance(c, dict)
            and c.get('clientId') not in BUILTIN_CLIENTS and not str(c.get('clientId', '')).startswith('$')]


def _local_realm(rel: str, doc: dict) -> bool:
    urls = []
    for c in _custom_clients(doc):
        urls += [u for u in (c.get('redirectUris') or []) + (c.get('webOrigins') or []) + [c.get('rootUrl') or '']
                 if u and u not in ('+', '/*')]
    return bool(DEV_PATH.search(rel)) or (bool(urls) and all(LOCAL_URL.match(u) for u in urls))


def check_realms(repo: Repo, hits: Hits, realms: list[tuple[str, dict]]) -> list[dict]:
    out = []
    for rel, doc in realms:
        local = _local_realm(repo.root.name + '/' + rel, doc)
        name = doc['realm']
        deferred = []

        def add(check, needle, evidence, severity=None, after=None, **kw):
            if local:
                deferred.append((check, evidence))
                return
            hits.add(check, rel, _line(repo, rel, needle, after) if needle else None, f'realm {name}: {evidence}',
                     severity=severity, **kw)

        if doc.get('sslRequired') == 'none':
            add('KC-REALM-SSL', '"sslRequired"', 'sslRequired = none')
        if not doc.get('bruteForceProtected'):
            add('KC-REALM-BRUTE-FORCE', '"bruteForceProtected"', 'bruteForceProtected is off')
        if not doc.get('passwordPolicy') and not doc.get('identityProviders'):
            add('KC-REALM-PASSWORD-POLICY', None, 'no passwordPolicy')
        lifespan = doc.get('accessTokenLifespan')
        if isinstance(lifespan, int) and lifespan > 900:
            add('KC-REALM-TOKENS', '"accessTokenLifespan"', f'accessTokenLifespan = {lifespan}s')
        public = [c for c in _custom_clients(doc) if c.get('publicClient')]
        if public and not doc.get('revokeRefreshToken'):
            add('KC-REALM-TOKENS', None, f'revokeRefreshToken off with {len(public)} public client(s) - '
                                         'refresh tokens are not rotated')
        if doc.get('registrationAllowed'):
            add('KC-REALM-REGISTRATION', '"registrationAllowed"', 'registrationAllowed = true')
        if not doc.get('eventsEnabled') or not doc.get('adminEventsEnabled'):
            off = [k for k in ('eventsEnabled', 'adminEventsEnabled') if not doc.get(k)]
            add('KC-REALM-EVENTS', None, ', '.join(off) + ' off')
        with_pw = [u.get('username') for u in doc.get('users') or [] if isinstance(u, dict)
                   and any(isinstance(c, dict) and c.get('type') == 'password' and (c.get('value') or c.get('secretData'))
                           for c in u.get('credentials') or [])]
        if with_pw:
            add('KC-REALM-USERS', '"credentials"', f'{len(with_pw)} user(s) with a password: '
                                                   + ', '.join(str(u) for u in with_pw[:6]))

        full_scope = []
        for c in _custom_clients(doc):
            cid = c.get('clientId')
            anchor = f'"clientId": "{cid}"' if _line(repo, rel, f'"clientId": "{cid}"') else f'"{cid}"'
            redirects = c.get('redirectUris') or []
            wild = [u for u in redirects if u in ('*', 'http*', 'https://*', 'http://*') or
                    re.match(r'https?://\*', u) or (u.endswith('*') and not LOCAL_URL.match(u) and
                                                     not re.match(r'https?://[^/*]+/', u))]
            origins = [o for o in c.get('webOrigins') or [] if o == '*']
            if wild or origins:
                add('KC-CLIENT-REDIRECT', '"redirectUris"', f'client {cid}: '
                    + ', '.join(f'redirect {u}' for u in wild) + (', webOrigins *' if origins else ''), after=anchor)
            if c.get('implicitFlowEnabled'):
                add('KC-CLIENT-IMPLICIT', '"implicitFlowEnabled"', f'client {cid}', after=anchor)
            if c.get('directAccessGrantsEnabled') and not c.get('bearerOnly'):
                add('KC-CLIENT-DIRECT-GRANT', '"directAccessGrantsEnabled"', f'client {cid}'
                    + (' (public)' if c.get('publicClient') else ''), after=anchor)
            attrs = c.get('attributes') or {}
            if c.get('publicClient') and c.get('standardFlowEnabled', True) and \
                    not attrs.get('pkce.code.challenge.method'):
                add('KC-CLIENT-NO-PKCE', None, f'client {cid}: public, no pkce.code.challenge.method')
            secret = c.get('secret')
            if secret and not c.get('publicClient') and not set(str(secret)) <= {'*'} and \
                    not str(secret).startswith('${'):
                value = str(secret)
                sev = 'critical' if entropy(value) >= 3.5 and len(value) >= 24 else 'high'
                add('KC-CLIENT-SECRET', '"secret"', f'client {cid}: secret {redact(value)}', severity=sev,
                    after=anchor, tracked=repo.is_tracked(rel))
            if c.get('fullScopeAllowed', True) and not c.get('bearerOnly'):
                full_scope.append(cid)
        if full_scope:
            add('KC-CLIENT-FULL-SCOPE', None, 'fullScopeAllowed on ' + ', '.join(full_scope[:8]))
        for u in doc.get('users') or []:
            if not isinstance(u, dict) or not u.get('serviceAccountClientId'):
                continue
            roles = set((u.get('clientRoles') or {}).get('realm-management') or [])
            broad = sorted(roles & ADMIN_ROLES)
            if broad:
                add('KC-SERVICE-ACCOUNT-ADMIN', '"serviceAccountClientId"',
                    f'service account of {u["serviceAccountClientId"]}: realm-management {", ".join(broad)}')
        if deferred:
            serious = {'KC-CLIENT-REDIRECT', 'KC-CLIENT-IMPLICIT', 'KC-SERVICE-ACCOUNT-ADMIN'}
            hits.add('KC-REALM-LOCAL', rel, None, f'realm {name}: ' + '; '.join(e for _, e in deferred),
                     severity='medium' if serious & {c for c, _ in deferred} else None,
                     names=[e for _, e in deferred])
        out.append({'file': rel, 'realm': name, 'local': local, 'clients': [c.get('clientId') for c in
                                                                            _custom_clients(doc)],
                    'registration': bool(doc.get('registrationAllowed'))})
    return out


def check_infra(repo: Repo, hits: Hits) -> list[str]:
    images = []
    for rel in repo.files:
        if not (re.search(r'(^|/)(docker-)?compose[\w.-]*\.ya?ml$', rel) or rel.endswith(('.yml', '.yaml'))
                or os.path.basename(rel).startswith(('Dockerfile', 'Containerfile'))):
            continue
        src = repo.source(rel)
        if 'keycloak' not in src.text.lower():
            continue
        local = bool(DEV_PATH.search(repo.root.name + '/' + rel))
        compose = bool(re.search(r'(^|/)(docker-)?compose[\w.-]*\.ya?ml$', rel))
        prod = bool(re.search(r'(?i)prod|live|stage', rel))
        for i, line in enumerate(src.lines, 1):
            s = line.split('#')[0]
            img = re.search(r'(?:image:\s*|FROM\s+)["\']?([\w./-]*keycloak[\w./-]*):([\w.-]+)', s)
            if img:
                images.append(f'{img.group(1)}:{img.group(2)}')
                major = version_tuple(img.group(2))[0]
                if 0 < major < KC_CURRENT_MAJOR:
                    hits.add('KC-IMAGE-OLD', rel, i, s.strip(), severity='medium' if local else None)
            if re.search(r'\bstart-dev\b', s):
                hits.add('KC-START-DEV', rel, i, s.strip(),
                         severity='low' if local and not prod else 'medium' if compose and not prod else None)
    return images


def _backend_signals(ctx) -> dict:
    issuers, jwk_only = [], []
    for src, entries in ctx.configs:
        if is_test_path(src.rel):
            continue
        for e in entries:
            if '/realms/' in e.value or (e.norm.endswith(('issueruri', 'jwkseturi')) and e.value):
                issuers.append((src.rel, e))
        jwk = next((e for e in entries if e.norm.endswith('resourceserver.jwt.jwkseturi') and e.value.strip('"\'')),
                   None)
        if jwk and not any(e.norm.endswith('resourceserver.jwt.issueruri') for e in entries):
            jwk_only.append((src.rel, jwk))
    code_realm = [j for j in ctx.main if re.search(r'/realms/|realm_access|resource_access|org\.keycloak', j.src.code)]
    deps = re.search(r'org\.keycloak|keycloak-', ctx.build)
    return {'issuers': issuers, 'jwk_only': jwk_only, 'code': code_realm, 'deps': bool(deps),
            'keycloak': bool(deps or code_realm or any('/realms/' in e.value for _, e in issuers))}


def _role_names(text: str, consts: dict[str, str]) -> set[str]:
    out = set()
    for _, args in ROLE_RULE.findall(text):
        out |= {s for s in strings_in(args)}
        out |= {consts[n] for n in re.findall(r'\b([A-Z][A-Z0-9_]+)\b', args) if n in consts}
    return {r for r in out if r and not r.startswith('SCOPE_')}


def check_backend(ctx, sig: dict, realms: list[dict]) -> set[str]:
    hits = ctx.hits
    m = re.search(r'keycloak-spring-boot-(starter|\d+-adapter)|keycloak-spring-security-adapter|'
                  r'keycloak-(tomcat|undertow|servlet-filter|jetty\d*)-adapter|KeycloakWebSecurityConfigurerAdapter',
                  ctx.build + ctx.all_main)
    if m:
        build = next((f for f in ctx.repo.files if os.path.basename(f) in ('build.gradle.kts', 'build.gradle', 'pom.xml')
                      and m.group(0) in ctx.repo.source(f).text), None)
        hits.add('KC-LEGACY-ADAPTER', build, None, m.group(0))

    for rel, e in sig['jwk_only']:
        hits.add('KC-JWK-ONLY', rel, e.line, f'{e.key}: {e.value}   profile={e.profile or "default"}',
                 severity='low' if profile_kind(e.profile) == 'dev' else None)
    for rel, e in sig['issuers']:
        raw = e.value
        fallback = re.fullmatch(r'\$\{[^:}]+:([^}]*)\}', raw)
        url = fallback.group(1) if fallback else raw
        if url.startswith('http://') and not LOCAL_URL.match(url) and profile_kind(e.profile) != 'dev':
            hits.add('KC-ISSUER-HTTP', rel, e.line, f'{e.key}: {raw}')

    chains = ctx.chains
    resource_server = any(c.get('oauth2ResourceServer') for c in chains) or \
        any(e.norm.endswith('resourceserver.jwt.issueruri') for _, e in sig['issuers'])
    consts = dict(re.findall(r'\b(?:const\s+val|val|static\s+final\s+String|final\s+String)\s+([A-Z][A-Z0-9_]+)'
                             r'\s*(?::\s*String)?\s*=\s*"([^"]+)"', '\n'.join(j.src.code for j in ctx.main)))
    rule_text = ' '.join(r['text'] for c in chains for r in c['rules']) + ' ' + \
        ' '.join(t for e in ctx.endpoints for t in e['auth_text'])
    code_text = '\n'.join(j.src.code for j in ctx.main)
    backend_roles = {re.sub(r'^ROLE_', '', r).lower() for r in _role_names(rule_text + ' ' + code_text, consts)}
    reads_roles = re.search(r'realm_access|resource_access|setAuthoritiesClaimName|authoritiesClaimName|'
                            r'JwtGrantedAuthoritiesConverter|Converter\s*<\s*Jwt\b|jwtAuthenticationConverter|'
                            r'authorities-claim-name|authoritiesclaimname', code_text + ctx.config_text, re.I)
    if resource_server and sig['keycloak']:
        sec_file, sec_line = next(((c['file'], c['line']) for c in chains), (None, None))
        if backend_roles and not reads_roles:
            hits.add('KC-ROLES-UNMAPPED', sec_file, sec_line,
                     f'roles checked: {", ".join(sorted(backend_roles)[:6])}; no converter reads realm_access/resource_access')
        audiences = [e for src, entries in ctx.configs if not is_test_path(src.rel) for e in entries
                     if e.norm.endswith('resourceserver.jwt.audiences') and e.value.strip('[]"\' ')
                     and not re.fullmatch(r'\$\{[^:}]+:\}', e.value.strip())]
        guarded = bool(AUD_GUARD.search(code_text) or audiences)
        if not guarded:
            hits.add('KC-NO-AUDIENCE', sec_file, sec_line,
                     'no aud/azp validation in code or config (spring.security.oauth2.resourceserver.jwt.audiences)')
        protected = [e for e in ctx.endpoints if e.get('url_rule') not in ('permitAll', 'anonymous', 'denyAll')]
        role_based = [e for e in protected if e['auth'] or e['class_auth'] or
                      e.get('url_rule') not in (None, 'authenticated', 'fullyAuthenticated')]
        if protected and not role_based and not guarded:
            registration = any(r['registration'] for r in realms)
            hits.add('KC-ANY-REALM-USER', sec_file, sec_line,
                     f'{len(protected)} endpoints, all only authenticated, no role, aud or azp check'
                     + ('; a realm export allows self-registration' if registration else ''),
                     severity=None if registration else 'medium')

    admin = []
    for j in ctx.main:
        code = j.src.code
        if not re.search(r'/admin/realms|KeycloakBuilder|org\.keycloak\.admin|Keycloak\.getInstance', code):
            continue
        for rx, sev, label in ((r'"password"\s*\)|grant_type=password|OAuth2Constants\.PASSWORD|\.grantType\s*\(\s*"password"|'
                                r'\.username\s*\(', 'high', 'password grant with a user account'),
                               (r'realm\s*\(\s*"master"\s*\)|/realms/master\b|"master"', 'high', 'master realm'),
                               (r'"admin-cli"', 'medium', 'admin-cli client')):
            hit = re.search(rx, code)
            if hit:
                hits.add('KC-ADMIN-GRANT', j.rel, j.src.line_at(hit.start()), f'{label}: '
                         + j.src.line(j.src.line_at(hit.start())).strip(), severity=sev)
        admin.append(j.rel)

    seen = set()
    for j in ctx.main:
        for hit in re.finditer(r'getClaimAsString\s*\(\s*"(preferred_username|email)"|\.preferredUsername\b|'
                               r'claims\s*\[\s*"(preferred_username|email)"\s*\]|'
                               r'(?:getClaim|claims\s*\.\s*get)\s*\(\s*"(preferred_username|email)"', j.src.code):
            if j.rel not in seen:
                seen.add(j.rel)
                hits.add('KC-MUTABLE-USER-KEY', j.rel, j.src.line_at(hit.start()),
                         j.src.line(j.src.line_at(hit.start())).strip())

    for c in chains:
        if c.get('oauth2Login') and sig['keycloak'] and \
                not re.search(r'OidcClientInitiatedLogoutSuccessHandler|OidcClientInitiatedServerLogoutSuccessHandler|'
                              r'oidcLogout', code_text):
            hits.add('KC-LOGOUT-LOCAL', c['file'], c['line'], f'chain {c["name"]}: oauth2Login, no OIDC logout handler')
    ctx.keycloak_admin = admin
    return backend_roles


def check_frontend(repo: Repo, hits: Hits, ws: dict, backend_roles: set[str] | None) -> dict | None:
    declared = ws['declared']
    lib = next((n for n in ('keycloak-angular', 'keycloak-js', 'angular-auth-oidc-client', 'angular-oauth2-oidc',
                            'oidc-client-ts') if n in declared), None)
    if not lib:
        return None
    prefix = '' if ws['path'] == '.' else ws['path'] + '/'
    files = [f for f in repo.files if f.startswith(prefix) and f.endswith('.ts') and not is_test_path(f)]
    texts = {f: repo.source(f).code for f in files}
    joined = '\n'.join(texts.values())
    if lib not in ('keycloak-angular', 'keycloak-js') and '/realms/' not in joined:
        return None
    kc_version = ws['installed'].get('keycloak-js') or re.sub(r'^[\^~>=<\s]+', '', declared.get('keycloak-js', ''))
    for f, code in texts.items():
        for m in re.finditer(r'\bflow\s*:\s*[\'"](implicit|hybrid)[\'"]|\bresponseType\s*:\s*[\'"](id_token token|token|'
                             r'id_token)[\'"]', code):
            hits.add('KC-JS-FLOW', f, repo.source(f).line_at(m.start()), m.group(0))
        for m in re.finditer(r'\bpkceMethod\s*:\s*false', code):
            hits.add('KC-JS-NO-PKCE', f, repo.source(f).line_at(m.start()), m.group(0))
    init = next(((f, m) for f, code in texts.items() for m in [re.search(r'\.init\s*\(|provideKeycloak\s*\(|'
                                                                        r'initOptions\s*:', code)] if m), None)
    if 'keycloak-js' in declared or 'keycloak-angular' in declared:
        major = version_tuple(kc_version or '0')[0]
        if init and 0 < major < 26 and not re.search(r'pkceMethod\s*:\s*[\'"]S256', joined):
            hits.add('KC-JS-NO-PKCE', init[0], repo.source(init[0]).line_at(init[1].start()),
                     f'keycloak-js {kc_version}, init without pkceMethod: \'S256\'')
        if init and 'keycloak-angular' not in declared and \
                not re.search(r'\bupdateToken\s*\(|withAutoRefreshToken|AutoRefreshTokenService|onTokenExpired', joined):
            hits.add('KC-JS-NO-REFRESH', init[0], repo.source(init[0]).line_at(init[1].start()),
                     f'{lib}: no updateToken(), onTokenExpired or auto refresh in {ws["path"]}')
    front_roles = set()
    for code in texts.values():
        for m in re.finditer(r'\bhas(?:Realm|Resource)Role\s*\(\s*[\'"]([^\'"]+)[\'"]|\broles\s*:\s*\[([^\]]*)\]', code):
            front_roles |= {m.group(1)} if m.group(1) else set(strings_in(m.group(2) or ''))
    front_roles = {r.lower() for r in front_roles if r}
    if backend_roles and front_roles:
        missing = sorted(front_roles - backend_roles)
        if missing:
            where = next(((f, m) for f, code in texts.items() for m in [re.search(re.escape(missing[0]), code, re.I)] if m),
                         None)
            hits.add('KC-ROLE-MISMATCH', where[0] if where else None,
                     repo.source(where[0]).line_at(where[1].start()) if where else None,
                     f'frontend checks {", ".join(missing[:6])}; backend rules check {", ".join(sorted(backend_roles)[:6])}')
    return {'path': ws['path'], 'library': lib, 'version': kc_version or declared.get(lib), 'roles': sorted(front_roles)}


def run(repo: Repo, hits: Hits, ctx=None, workspaces=()) -> dict | None:
    realms_raw = _realm_docs(repo)
    sig = _backend_signals(ctx) if ctx else None
    fronts = [ws for ws in workspaces if any(n in ws['declared'] for n in (
        'keycloak-angular', 'keycloak-js', 'angular-auth-oidc-client', 'angular-oauth2-oidc', 'oidc-client-ts'))]
    if not (realms_raw or (sig and sig['keycloak']) or fronts):
        return None
    realms = check_realms(repo, hits, realms_raw)
    images = check_infra(repo, hits)
    backend_roles = check_backend(ctx, sig, realms) if sig and sig['keycloak'] else None
    frontends = [f for f in (check_frontend(repo, hits, ws, backend_roles) for ws in fronts) if f]
    if not (realms or (sig and sig['keycloak']) or frontends):
        return None
    issuers = sorted({e.value for _, e in sig['issuers']}) if sig else []
    return {'issuers': issuers[:6], 'realms': realms, 'images': sorted(set(images)), 'frontends': frontends,
            'admin_api': bool(sig and getattr(ctx, 'keycloak_admin', None)),
            'backend_roles': sorted(backend_roles or [])}
