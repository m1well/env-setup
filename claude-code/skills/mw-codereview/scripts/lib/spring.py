"""Spring Boot checks - security first, then persistence, transactions, layering and structure."""
from __future__ import annotations

import os
import re
import sys
from collections import defaultdict

from . import jvm
from .core import (Hits, Repo, balanced, config_entries, define, entropy, is_test_path, profile_kind, secret_id,
                   redact, split_top, strings_in, version_tuple)
from .extract import entity as entity_x, funs as funs_x

V_AUTHZ = ('Open the controller and the security config. A finding needs the path a request takes: '
           'which chain matches, which rule wins, whether the service checks the caller itself.')

define('SB-NO-SECURITY', 'Web endpoints, but no Spring Security on the classpath', 'high', 'authorization',
       'Check for a gateway, an API key filter or a servlet filter that authenticates instead. Without '
       'one every endpoint is public.', security=True, rule='SEC-2', owasp='A01')
define('SB-SEC-METHOD-OFF', 'Method security annotations used, but method security is not enabled',
       'critical', 'authorization',
       'Search every @Configuration for @EnableMethodSecurity (or prePostEnabled on the legacy '
       'annotation). Without it each @PreAuthorize is decoration.', security=True, rule='SEC-1', owasp='A01')
define('SB-SEC-PRIVATE', 'Security annotation on a method no proxy can intercept', 'high', 'authorization',
       'A private (or, in Kotlin without all-open, a final) method is called directly - the annotation '
       'never runs. Check who calls it.', security=True, rule='SEC-1', owasp='A01')
define('SB-KOTLIN-NO-ALLOPEN', 'Kotlin Spring module without the kotlin-spring (all-open) plugin', 'high',
       'config', 'Without all-open every class is final: CGLIB proxies fail or skip @Transactional, '
       '@PreAuthorize and @Cacheable. Check the plugins block and buildSrc conventions.',
       security=True, rule='STR-7', owasp='A02')
define('SB-SEC-REMOVED-API', 'Spring Security API removed in 6.x/7.x still in use', 'medium', 'upgrade',
       'WebSecurityConfigurerAdapter means the app is still on Spring Security 5 - unpatched. The DSL '
       'leftovers (antMatchers, authorizeRequests, and()) break on the next major.',
       security=True, rule='SEC-1', owasp='A02')
define('SB-SEC-PERMITALL-ANY', 'Default allow: anyRequest() is permitted', 'high', 'authorization',
       'Every path no earlier rule names is public. Check whether that is a deliberate public app.',
       security=True, rule='SEC-2', owasp='A01')
define('SB-SEC-NO-DEFAULT-DENY', 'Security chain without a closing anyRequest() rule', 'medium',
       'authorization', 'Paths no rule names fall through. List them against the endpoint inventory.',
       security=True, rule='SEC-2', owasp='A01')
define('SB-SEC-CSRF-OFF', 'CSRF protection disabled', 'medium', 'authorization',
       'Fine for a stateless bearer-token API. A blocker as soon as a cookie carries the session: '
       'form login, oauth2Login, a session cookie, a BFF.', security=True, rule='SEC-3', owasp='A01')
define('SB-SEC-CORS', 'CORS allows any origin', 'medium', 'config',
       'With credentials any website can make authenticated calls. Check allowCredentials and whether '
       'the origin list should be the frontend host.', security=True, rule='SEC-4', owasp='A02')
define('SB-SEC-HEADERS-OFF', 'Security headers or frame options disabled', 'medium', 'config',
       'Usually done for the H2 console. Check the profile it applies to.', security=True, owasp='A02')
define('SB-AUTHZ-PUBLIC-WRITE', 'Mutating endpoint reachable without authentication', 'high',
       'authorization', V_AUTHZ, security=True, rule='SEC-2', owasp='A01')
define('SB-AUTHZ-UNMATCHED', 'Endpoint covered by no URL rule and no method security', 'high',
       'authorization', V_AUTHZ, security=True, rule='SEC-2', owasp='A01')
define('SB-AUTHZ-INCONSISTENT', 'Sibling endpoints disagree about authorization', 'high', 'authorization',
       'The contrast is the finding: name the endpoint without the check and the siblings with it.',
       security=True, rule='SEC-2', owasp='A01')
define('SB-AUTHZ-ACTUATOR-PUBLIC', 'Actuator endpoints permitted without authentication', 'high',
       'config', 'health and info in public is normal. Anything else public is configuration or memory.',
       security=True, rule='SEC-9', owasp='A02')
define('SB-SQL-CONCAT', 'SQL or JPQL built from concatenated values', 'high', 'injection',
       'Trace the value: request input makes it critical, an enum or an allow-listed sort column makes '
       'it a false positive. Parameters or the Criteria API are the fix.', security=True, rule='DATA-6',
       owasp='A05')
define('SB-SPEL-INJECTION', 'SpEL expression parsed from a non-constant', 'high', 'injection',
       'If any part comes from a request, it is remote code execution.', security=True, rule='SEC-6',
       owasp='A05')
define('SB-CMD-EXEC', 'OS command execution', 'high', 'injection',
       'Check where the arguments come from and whether a shell (sh -c) is involved.', security=True,
       owasp='A05')
define('SB-DESERIALIZATION', 'Unsafe deserialization or polymorphic typing', 'high', 'deserialization',
       'Check whether the input can come from outside (request, queue, file upload).', security=True,
       rule='SEC-7', owasp='A08')
define('SB-XXE', 'XML parser without DOCTYPE/external entity hardening', 'high', 'injection',
       'Check whether the parser ever sees foreign XML. The fix is disallow-doctype-decl.',
       security=True, rule='SEC-7', owasp='A02')
define('SB-SSRF-INPUT', 'Endpoint takes a URL or host from the request', 'medium', 'ssrf',
       'Follow the parameter: fetched as given it reaches the metadata endpoint and the internal network.',
       security=True, rule='SEC-11', owasp='A01')
define('SB-HEADER-TRUST', 'Identity, tenant or client IP taken from a request header', 'high', 'authorization',
       'Safe only behind a gateway that removes the header from every client request and sets it itself, with the '
       'service reachable through that gateway alone (network policy, no public port). Otherwise any client sends '
       'X-Tenant-Id of another tenant. Identity, roles and tenant come from the validated token; the client IP from '
       'server.forward-headers-strategy with a trusted proxy list.', security=True, rule='SEC-2', owasp='A01')
define('SB-OPEN-REDIRECT', 'Redirect target built from a variable', 'medium', 'authorization',
       'Check whether the target comes from the request and is matched against an allow-list.',
       security=True, owasp='A01')
define('SB-AUTH-FILTER-SWALLOW', 'Auth filter catches every exception and lets the request through', 'high',
       'authentication', 'Fail anonymous: a timeout or a 5xx of the auth server turns into an anonymous request or a '
       '401 that tells the client its token is dead. Catch only the "token invalid" case, answer 503 on the rest.',
       security=True, owasp='A07')
define('SB-HEADER-RELAY', 'Request header passed unchecked into an outbound call', 'medium', 'authentication',
       'The client chooses what the other system sees - an app id, a source, a realm, a tenant. Take the value from '
       'configuration, or check it against an allow-list before it leaves.', security=True, owasp='A01')
define('AUTH-NO-RATELIMIT', 'Public endpoint checks a secret, no rate limiting anywhere', 'medium', 'authentication',
       'Every guess at a code, PIN or password costs one request. Check for a limit in front of the app (gateway, '
       'nginx limit_req) or in the system behind it; otherwise bucket4j or a resilience4j RateLimiter on this path.',
       security=True, owasp='A07')
define('SB-HOST-HEADER-LINK', 'Link in a mail built from the request host', 'high', 'authentication',
       'Always a suspicion, it depends on the proxy: unless the proxy overwrites Host and X-Forwarded-*, an attacker '
       'triggers the mail with his own host in the header and the victim gets a login or reset link to it. Build '
       'mail links from a configured base URL.', security=True, owasp='A01')
define('SB-GET-SIDE-EFFECT', 'GET endpoint that deletes or writes', 'medium', 'api',
       'Link previews, mail scanners and prefetching call GET on their own: a one-time link consumed on open is '
       'burnt before the user clicks, and a login over GET is login CSRF. Show a page that confirms with a POST.',
       security=True, rule='WEB-5', owasp='A01')
define('PUBLIC-MAIL-TO-INPUT', 'Public endpoint sends mail to an address from the request', 'medium', 'abuse',
       'A spam relay: anyone can make the app mail any address under its name and domain reputation. Check for a '
       'captcha, a limit per address and per IP, and whether the mail carries text the sender chose.',
       security=True, owasp='A04')
define('SB-PATH-TRAVERSAL', 'File path built from client-controlled input', 'medium', 'injection',
       'An uploaded file name or a path parameter reaching the filesystem needs normalising and a '
       'base-directory check.', security=True, owasp='A01')
define('SB-WEAK-HASH', 'MD5 or SHA-1 in use', 'medium', 'crypto',
       'Harmless for an ETag or a cache key, a finding for passwords, tokens and signatures.',
       security=True, owasp='A04')
define('SB-WEAK-CIPHER', 'Weak cipher or ECB mode', 'high', 'crypto',
       '"AES" alone means AES/ECB. Use AES/GCM with a random IV.', security=True, owasp='A04')
define('SB-STATIC-IV', 'Constant initialisation vector', 'medium', 'crypto',
       'A fixed IV makes equal plaintexts look equal.', security=True, owasp='A04')
define('SB-PASSWORD-ENCODER', 'Password encoder without a real hash', 'critical', 'crypto',
       'NoOp, MD5, SHA and the old StandardPasswordEncoder are blockers whatever the salt.', security=True,
       rule='SEC-10', owasp='A04')
define('SB-BCRYPT-STRENGTH', 'BCrypt strength below 10', 'low', 'crypto', 'Check whether it is a test config.',
       security=True, rule='SEC-10', owasp='A04')
define('SB-INSECURE-RANDOM', 'Non-cryptographic random next to a token, code or secret', 'medium', 'crypto',
       'java.util.Random and Math.random are predictable. SecureRandom for anything an attacker guesses.',
       security=True, owasp='A04')
define('SB-TLS-TRUST-ALL', 'TLS certificate or hostname verification switched off', 'high', 'crypto',
       'Check the profile. In production code this hands the connection to anyone on the path.',
       security=True, owasp='A04')
define('SB-JWT-UNVERIFIED', 'JWT parsed without verifying the signature', 'high', 'authentication',
       'Check whether the claims are used for an authorization decision.', security=True, owasp='A07')
define('SB-JWT-HARDCODED-KEY', 'JWT signing key in the source code', 'high', 'secrets',
       'Rotate it - it counts as leaked. Load it from the environment or a secret store.', security=True,
       rule='SEC-5', owasp='A07')
define('SB-LOG-SECRET', 'Log statement carries a secret-looking value', 'medium', 'logging',
       'Open the line: a token or password in a log ends up in every log aggregator.', security=True,
       rule='SEC-8', owasp='A09')
define('SB-ERROR-LEAK', 'Exception message or stack trace sent to the client', 'low', 'exposure',
       'Check what the message can contain - SQL, file paths, internal hostnames.', security=True,
       rule='WEB-3', owasp='A10')
define('SB-CFG-SECRET', 'Secret literal in Spring configuration', 'high', 'secrets',
       'A committed secret is leaked - rotate it, then move it to the environment. A dev-only profile '
       'with a local default is low.', security=True, rule='SEC-5', owasp='A07')
define('SB-CFG-SECRET-DEFAULT', 'Secret placeholder with a literal fallback', 'high', 'secrets',
       '${X:fallback} ships the fallback when the variable is missing - in production too.', security=True,
       rule='SEC-5', owasp='A07')
define('SB-CFG-ACTUATOR', 'Sensitive actuator endpoints exposed over HTTP', 'high', 'config',
       'env, configprops, heapdump, threaddump, loggers, shutdown: configuration and memory contents. '
       'Check the profile and whether the management port is internal.', security=True, rule='SEC-9',
       owasp='A02')
define('SB-CFG-ERROR-DETAILS', 'Error responses include stack traces or exception messages', 'medium',
       'exposure', 'Check the profile.', security=True, rule='WEB-3', owasp='A10')
define('SB-CFG-H2-CONSOLE', 'H2 console enabled', 'high', 'config',
       'A JDBC console in the browser. Fine on a laptop profile, a remote shell anywhere else.',
       security=True, owasp='A02')
define('SB-CFG-DEBUG', 'Debug or trace logging in a non-dev profile', 'medium', 'logging',
       'Security and web debug logs print headers, tokens and request bodies.', security=True, owasp='A09')
define('SB-CFG-COOKIE', 'Session cookie without Secure/HttpOnly', 'medium', 'config',
       'Check the profile and whether TLS terminates before the app.', security=True, owasp='A02')
define('SB-CFG-DDL-AUTO', 'Hibernate generates the schema outside of tests', 'high', 'persistence',
       'update/create/create-drop against a real database loses data or drifts from the migrations.',
       rule='MIG-10')
define('SB-CFG-OPEN-IN-VIEW', 'spring.jpa.open-in-view not switched off', 'low', 'persistence',
       'The connection stays open for the whole request, lazy loading happens in the view.', rule='DATA-4')
define('SB-ENTITY-REQUEST', 'Entity bound directly from the request body', 'high', 'authorization',
       'Mass assignment: the client can set every column, the id and the owner included.', security=True,
       rule='WEB-1', owasp='A08')
define('SB-ENTITY-RESPONSE', 'Entity returned from a controller', 'medium', 'layering',
       'The persistence model is the API contract now; lazy relations serialize or explode.', rule='WEB-1')
define('SB-NO-VALID', 'Request body without @Valid', 'medium', 'api',
       'Check whether the DTO carries constraints at all and whether the service validates.', rule='WEB-2')
define('SB-ANY-METHOD', '@RequestMapping on a method without an HTTP method', 'low', 'api',
       'It answers GET as well - a state change over GET bypasses CSRF and lands in caches.', rule='WEB-5')
define('SB-FIELD-INJECTION', 'Field injection with @Autowired', 'low', 'coupling', 'Count, not a hunt.',
       rule='STR-1')
define('SB-CTOR-DEPS', 'Class with more than 10 injected dependencies', 'medium', 'coupling',
       'The number is the finding. Group the dependencies by the job they serve.', rule='STR-6')
define('SB-CLASS-SIZE', 'Class past 400 lines or 15 public methods', 'medium', 'size',
       'Name what the class does besides its main job.')
define('SB-METHOD-PARAMS', 'Method with more than 6 parameters', 'low', 'size',
       'Several of the same type in a row is a call site waiting to swap them.')
define('SB-CTRL-REPO', 'Controller injects a repository', 'medium', 'layering',
       'Whatever the service layer guarantees - transactions, checks - does not happen on this path.',
       rule='STR-6')
define('SB-TX-CONTROLLER', '@Transactional on a controller', 'medium', 'transaction', '', rule='DATA-1')
define('SB-TX-PRIVATE', '@Transactional on a private method', 'medium', 'transaction',
       'The proxy never sees the call - no transaction.', rule='DATA-2')
define('SB-TX-REMOTE-CALL', 'Remote call inside a transaction', 'medium', 'transaction',
       'The connection stays open for as long as the other system takes. Check whether the call can '
       'move after the commit (event, outbox).', rule='DATA-1')
define('SB-SCHEDULED-NO-LOCK', '@Scheduled job without a distributed lock', 'medium', 'transaction',
       'Fine on one instance, runs twice on two. Check the deployment.')
define('SB-HTTP-NO-TIMEOUT', 'Outbound HTTP client without a configured timeout', 'medium', 'resilience',
       'Default timeouts are infinite or minutes long - the other system\'s bad day becomes yours.',
       rule='WEB-8')
define('SB-ENUM-ORDINAL', 'Enum column stored by ordinal', 'high', 'persistence',
       'Inserting a value in the middle of the enum rewrites what every row means. JPA defaults to '
       'ORDINAL when @Enumerated is missing.', rule='MODEL-7')
define('SB-ENTITY-NO-PK', 'Entity without a visible primary key', 'medium', 'persistence',
       'Usually the @MappedSuperclass sits in another module - check before reporting.')
define('SB-ENTITY-WIDE', 'Entity with more than 25 columns', 'medium', 'size',
       'Look for column prefixes - that is where an embeddable is hiding.', rule='MODEL-2')
define('SB-ENTITY-DATA-CLASS', 'Entity declared as a Kotlin data class', 'medium', 'persistence',
       'equals/hashCode/toString walk lazy relations and change with the id.', rule='MODEL-4')
define('SB-EAGER', 'Eager association', 'medium', 'persistence',
       '@ManyToOne and @OneToOne are EAGER unless told otherwise.', rule='DATA-3')
define('SB-REPO-SIZE', 'Repository with more than 20 query methods', 'low', 'size',
       'Business rules moved into derived query names.')
define('SB-EVENT-ORPHAN', 'Event without listener, or listener without publisher', 'low', 'dead-code',
       'One side was deleted. Check for listeners in other services (Kafka, Modulith externalization).')
define('SB-SWALLOWED', 'Exception caught and dropped', 'medium', 'error-handling',
       'Check whether the error is logged, rethrown or turned into a result.', owasp='A10')
define('SB-STDOUT', 'println / printStackTrace in production code', 'low', 'logging', '', rule='OPS-1')
define('SB-NO-MIGRATIONS', 'JPA entities without Flyway or Liquibase', 'medium', 'persistence',
       'The schema comes from somewhere - ddl-auto or a manual script.', rule='MIG-1')
define('SB-NO-ARCHUNIT', 'No ArchUnit in a codebase of this size', 'low', 'testing',
       'Layer and module rules live in a README until a test enforces them.', rule='TEST-7')
define('SB-UNTESTED', 'Controllers and services no test names', 'low', 'testing',
       'A name match, not coverage - a class tested through another one counts as untested here.')
define('SB-PACKAGE-CYCLE', 'Cycle between top-level packages', 'medium', 'coupling',
       'Name both directions and the import that closes the cycle.', rule='STR-3')
define('SB-INTERNAL-IMPORT', 'Import of another module\'s internal package', 'high', 'boundary',
       'The module boundary only exists on paper.', rule='STR-8')
define('SB-MOCKBEAN', '@MockBean / @SpyBean (removed in Spring Boot 4)', 'low', 'upgrade', '', rule='TEST-2')
define('SB-JACKSON2-ON-BOOT4', 'Jackson 2 imports on Spring Boot 4', 'medium', 'upgrade',
       'Boot 4 auto-configures Jackson 3 (tools.jackson). Jackson 2 annotations still work, the '
       'ObjectMapper customisation does not.', rule='WEB-10')
define('SB-BOOT4-RENAMED', 'Starter or property renamed in Spring Boot 4', 'low', 'upgrade', '')

AUTH_ANNOS = {'PreAuthorize', 'PostAuthorize', 'Secured', 'RolesAllowed', 'PreFilter', 'PostFilter',
              'AuthorizeReturnObject'}
PUBLIC_RULES = {'permitAll', 'anonymous'}
MAPPING = re.compile(r'@(Get|Post|Put|Patch|Delete|Request)Mapping\b')
URLISH = re.compile(r'(?i)^(url|uri|link|href|callback\w*|webhook\w*|redirect\w*|return\w*url|target\w*|'
                    r'host\w*|endpoint|location|image\w*url|avatar\w*|feed\w*|\w+url|\w+uri)$')
PATHISH = re.compile(r'(?i)^(file\w*|path\w*|dir\w*|folder|\w*filename|\w*path)$')
INTENDED_PUBLIC = re.compile(r'(?i)/(login|logout|register|signup|sign-up|auth|oauth2?|token|refresh|'
                             r'password|forgot|reset|verify|confirm|activate|webhooks?|callback|public|'
                             r'contact|newsletter|subscribe|health|csp-report|oeffentlich|öffentlich|kontakt|'
                             r'anmeldung|abmeldung|bestaetigung|registrierung)\b')
SECRET_KEY = re.compile(r'(?i)(^|[._-])(password|passwd|pwd|secret|token|api[._-]?key|apikey|private[._-]?key|'
                        r'client[._-]?secret|credentials?|access[._-]?key|secret[._-]?key|signing[._-]?key|'
                        r'jwt[._-]?(key|secret)|encryption[._-]?key|master[._-]?key|webhook[._-]?secret|'
                        r'auth[._-]?token)$')
NOT_A_SECRET = re.compile(r'(?i)^(\$\{[^:}]*\}|\{cipher\}.*|ENC\(.*\)|classpath:.*|file:.*|vault:.*|'
                          r'true|false|none|null|~|-?\d{1,4}[smhd]?|\$\{[^}]+\}.*)$')
WEAK_DEFAULT = re.compile(r'(?i)^(changeme|change-me|password\d*|secret\d*|admin\d*|root|postgres|sa|'
                          r'test\d*|user|guest|demo|default|12345\d*|qwerty|letmein)$')
SENSITIVE_ACTUATOR = {'*', 'env', 'configprops', 'heapdump', 'threaddump', 'shutdown', 'loggers', 'beans',
                      'mappings', 'jolokia', 'logfile', 'httpexchanges', 'httptrace', 'sessions',
                      'quartz', 'auditevents', 'conditions', 'caches', 'scheduledtasks', 'sbom'}
OUTBOUND = re.compile(r'\b(RestTemplate|RestClient|WebClient|@FeignClient|FeignClient|HttpClient\.new|'
                      r'OkHttpClient|HttpURLConnection|openConnection\s*\(|@HttpExchange|HttpServiceProxyFactory)')
TIMEOUT = re.compile(r'(?i)(connect-?timeout|read-?timeout|response-?timeout|connection-?timeout|'
                     r'CONNECT_TIMEOUT_MILLIS|setConnectTimeout|setReadTimeout|\.timeout\s*\(|'
                     r'ReadTimeoutHandler|connectTimeout|readTimeout|responseTimeout|socket-?timeout|'
                     r'withRequestFactorySettings|ClientHttpRequestFactorySettings|HttpClientSettings|'
                     r'spring\.http\.clients?\.)')
REMOTE_CALL = re.compile(r'\b(restTemplate|webClient|restClient|\w+Client|\w+Gateway|\w+Adapter|kafkaTemplate|'
                         r'rabbitTemplate|jmsTemplate|streamBridge|httpClient|\w*[mM]ailSender)\s*\??\.\s*'
                         r'(get\w*|post\w*|put\w*|patch\w*|delete\w*|exchange|retrieve|send\w*|convertAndSend|'
                         r'execute|call\w*|fetch\w*|request\w*|publish\w*|upload\w*|download\w*)\s*\(')


class Ctx:
    def __init__(self, repo: Repo, stack: dict, hits: Hits):
        self.repo, self.stack, self.hits = repo, stack, hits
        self.build = stack['build_text']
        sources = [f for f in repo.by_ext('.kt', '.java') if not f.startswith('buildSrc/')]
        self.main = [jvm.JFile(repo.source(f)) for f in sources if not is_test_path(f)]
        self.tests = [repo.source(f) for f in sources if is_test_path(f)]
        self.all_main = '\n'.join(j.src.bare for j in self.main)
        self.by = defaultdict(list)
        for j in self.main:
            self.by[j.stereotype].append(j)
        self.enums = set(re.findall(r'\benum\s+(?:class\s+)?(\w+)', self.all_main))
        self.converted = set(re.findall(r'AttributeConverter\s*<\s*(\w+)', self.all_main))
        self.class_names = {c.name for j in self.main for c in j.classes}
        self.custom_auth = set()
        for j in self.main:
            for c in j.classes:
                if getattr(c, 'kind_detail', '') in ('class', 'interface') and \
                        re.search(r'\bannotation\s+class\b|@interface\b', j.src.bare[c.offset - 12:c.offset + 40]) \
                        and c.has(*AUTH_ANNOS):
                    self.custom_auth.add(c.name)
        self.auth_annos = AUTH_ANNOS | self.custom_auth
        self.configs = [(repo.source(f), config_entries(repo.source(f))) for f in repo.files
                        if re.search(r'(^|/)(application|bootstrap)(-[\w.-]+)?\.(ya?ml|properties)$', f)]
        self.config_text = '\n'.join(s.text for s, _ in self.configs)
        self.inventory: dict = {}

    def hit(self, check, jf_or_rel, offset_or_line, evidence=None, **kw):
        if isinstance(jf_or_rel, jvm.JFile):
            src = jf_or_rel.src
            line = src.line_at(offset_or_line) if offset_or_line is not None else None
            rel = jf_or_rel.rel
            evidence = src.line(line).strip() if evidence is None and line else evidence
        else:
            rel, line = jf_or_rel, offset_or_line
        self.hits.add(check, rel, line, evidence or '', **kw)

    def boot(self) -> tuple[int, ...]:
        return version_tuple(self.stack.get('boot') or '0')


def _args(src_bare: str, src_code: str, open_at: int) -> tuple[str, str, int]:
    close = balanced(src_bare, open_at)
    if close < 0:
        close = min(len(src_bare), open_at + 400)
    return src_bare[open_at + 1:close], src_code[open_at + 1:close], close


def _anno_args(m: jvm.Member, name_re: re.Pattern) -> list[tuple[str, str, str]]:
    """(annotation name, bare args, code args) for every annotation in the member's block matching."""
    out = []
    for hit in name_re.finditer(m.anno_text):
        k = hit.end()
        while k < len(m.anno_text) and m.anno_text[k] in ' \t':
            k += 1
        if m.anno_text[k:k + 1] == '(':
            bare, code, _ = _args(m.anno_text, m.anno_code, k)
            out.append((hit.group(0), bare, code))
        else:
            out.append((hit.group(0), '', ''))
    return out


def string_consts(ctx: Ctx) -> dict[str, str]:
    """UPPER_CASE string constants of the codebase (const val, companion and object members, static final String),
    name -> initializer as code."""
    if getattr(ctx, '_consts', None) is None:
        ctx._consts = {}
        for j in ctx.main:
            for m in re.finditer(r'(?:\b(?:val|var)|\bString(?:\s*\[\s*\])?|\b(?:List|Set)\s*<\s*String\s*>)\s+'
                                 r'([A-Z][A-Z0-9_]+)\s*(?::[^=\n]+)?=\s*', j.src.bare):
                ctx._consts.setdefault(m.group(1), j.src.code[m.end():statement_end(j.src.bare, m.end())])
    return ctx._consts


def string_values(expr: str, consts: dict[str, str], depth: int = 0) -> list[str]:
    """The strings an expression or argument list evaluates to: literals, constants, arrays and lists of them,
    concatenations and templates. An unknown constant stays as {const}."""
    out = []
    if depth > 4:
        return out
    for _, arg in split_top(expr):
        arg = re.sub(r'^\s*(?:value|path)\s*=\s*', '', arg).strip().lstrip('*').strip()
        inner = re.fullmatch(r'(?:(?:mutable)?(?:listOf|arrayOf|setOf)|List\.of|Set\.of|Arrays\.asList|'
                             r'new\s+String\s*\[\s*\]\s*)?\s*[({\[]([\s\S]*)[)}\]]', arg)
        if inner and not arg.startswith('"'):
            out += string_values(inner.group(1), consts, depth + 1)
            continue
        text = ''
        for _, piece in split_top(arg, '+'):
            piece = piece.strip()
            lit = re.fullmatch(r'"((?:\\.|[^"\\])*)"', piece)
            if lit:
                text += re.sub(r'(?<!\\)\$\{?(?:\w+\.)*([A-Z][A-Z0-9_]+)\}?', lambda c: (string_values(
                    consts.get(c.group(1), ''), consts, depth + 1) or ['{const}'])[0], lit.group(1))
            elif re.fullmatch(r'[\w.]+', piece):
                found = string_values(consts.get(piece.split('.')[-1], ''), consts, depth + 1) or ['{const}']
                if piece == arg:
                    out += found
                    text = None
                    break
                text += found[0]
            else:
                text = None
                break
        if text:
            out.append(text)
    return out


def _paths(bare: str, code: str, consts: dict[str, str]) -> list[str]:
    if not bare.strip():
        return ['']
    paths = []
    for start, part in split_top(bare):
        key = re.match(r'\s*(\w+)\s*=', part)
        if key and key.group(1) not in ('value', 'path'):
            continue
        text = code[start:start + len(part)]
        if '$' in text or re.search(r'[A-Za-z_+]', re.sub(r'^\s*\w+\s*=|"(?:\\.|[^"\\])*"', '', text)):
            paths += string_values(text, consts) or ['{const}']
        else:
            paths += strings_in(text)
    return paths or ['']


def _join(*parts: str) -> str:
    path = '/' + '/'.join(p.strip('/') for p in parts if p and p.strip('/'))
    return re.sub(r'/+', '/', path)


def _pattern(p: str) -> re.Pattern | None:
    if p.startswith('<'):
        return None
    if not p.startswith('/'):
        p = '/' + p
    tail = ''
    if p.endswith('/**'):
        p, tail = p[:-3], '(?:/.*)?'
    out = []
    for tok in re.split(r'(\*\*|\*|\?|\{\*?[^}]*\})', p):
        if tok == '**':
            out.append('.*')
        elif tok == '*':
            out.append('[^/]*')
        elif tok == '?':
            out.append('[^/]')
        elif tok.startswith('{*'):
            out.append('.*')
        elif tok.startswith('{'):
            out.append('[^/]+')
        else:
            out.append(re.escape(tok))
    return re.compile(''.join(out) + tail)


def _matches(patterns: list[str], path: str) -> bool:
    for p in patterns:
        if p == '<actuator>' and path.startswith('/actuator'):
            return True
        rx = _pattern(p)
        if rx and rx.fullmatch(path):
            return True
    return False



def _configurer(bare: str, name: str) -> list[tuple[int, str]]:
    out = []
    for m in re.finditer(r'\b' + name + r'\b\s*([({])', bare):
        open_at = m.end() - 1
        close = balanced(bare, open_at, m.group(1), ')' if m.group(1) == '(' else '}')
        body = bare[open_at:close + 1] if close > 0 else bare[open_at:open_at + 200]
        tail = re.match(r'\s*\.\s*(\w+)\s*\(', bare[close + 1:close + 60]) if close > 0 else None
        out.append((m.start(), body + (' .' + tail.group(1) if tail else '')))
    return out


DISABLED = re.compile(r'[({]\s*(?:\(?\s*\w+\s*\)?\s*->\s*)?(?:\w+\s*\.\s*)?disable\s*\(\s*\)\s*;?\s*[)}]|'
                      r'\(\s*[\w.]*::disable\s*\)')


def _configured(bare: str, name: str) -> bool:
    for _, text in _configurer(bare, name):
        body, _, tail = text.partition(' .')
        if not (DISABLED.fullmatch(body.strip()) or (tail == 'disable' and re.fullmatch(r'\(\s*\)', body.strip()))):
            return True
    return False


def parse_chains(ctx: Ctx) -> list[dict]:
    chains = []
    for jf in ctx.main:
        if not re.search(r'SecurityFilterChain|SecurityWebFilterChain|WebSecurityConfigurerAdapter',
                         jf.src.bare):
            continue
        candidates = [m for m in jf.methods() if re.search(r'Security(Web)?FilterChain', m.returns + m.sig)
                      or (m.name == 'configure' and 'HttpSecurity' in m.sig)]
        for m in candidates:
            if not m.body:
                continue
            start, end = m.body
            bare, code = jf.src.bare[start:end + 1], jf.src.code[start:end + 1]
            order = re.search(r'@Order\s*\(\s*([-\w.]+)', m.anno_text + (m.owner.anno_text if m.owner else ''))
            order_val = 0
            if order:
                raw = order.group(1)
                order_val = int(raw) if re.fullmatch(r'-?\d+', raw) else \
                    (-2 ** 31 if 'HIGHEST' in raw else 2 ** 31 if 'LOWEST' in raw else 0)
            chain = {'file': jf.rel, 'line': m.line, 'name': m.name, 'order': order_val,
                     'index': len(chains), 'matchers': [], 'rules': [], 'offset': start}
            skip = []
            for sm in re.finditer(r'\bsecurityMatchers?\s*\(', bare):
                b, c, close = _args(bare, code, sm.end() - 1)
                chain['matchers'] += strings_in(c) or (['<actuator>'] if 'EndpointRequest' in b else [])
                skip.append((sm.start(), close))
            for mm in re.finditer(r'\.(requestMatchers|antMatchers|mvcMatchers|regexMatchers|pathMatchers)\s*\(',
                                  bare):
                if any(s <= mm.start() <= e for s, e in skip):
                    continue
                b, c, close = _args(bare, code, mm.end() - 1)
                patterns = strings_in(c)
                if 'EndpointRequest' in b:
                    detail = re.search(r'EndpointRequest\s*\.\s*(\w+)\s*\(([^)]*)\)', b)
                    patterns.append('<actuator>' if not detail or detail.group(1) == 'toAnyEndpoint'
                                    else f'<actuator:{detail.group(2).strip() or detail.group(1)}>')
                if 'PathRequest' in b:
                    patterns.append('<static>')
                method = re.search(r'HttpMethod\s*\.\s*(\w+)', b)
                method_var = re.match(r'\s*([a-z]\w*)\s*,', b)
                if not patterns and method:
                    patterns = ['/**']
                rule = _rule_after(bare, code, close + 1)
                if rule:
                    chain['rules'].append({'patterns': patterns,
                                           'method': method.group(1) if method else ('?' if method_var else None),
                                           'rule': rule[0], 'text': rule[1], 'any': False,
                                           'regex': mm.group(1) == 'regexMatchers',
                                           'line': jf.src.line_at(start + mm.start())})
            for am in re.finditer(r'\.(anyRequest|anyExchange)\s*\(\s*\)', bare):
                rule = _rule_after(bare, code, am.end())
                if rule:
                    chain['rules'].append({'patterns': [], 'method': None, 'rule': rule[0], 'text': rule[1],
                                           'any': True, 'line': jf.src.line_at(start + am.start())})
            for km in re.finditer(r'\bauthorize\s*\(', bare):
                b, c, close = _args(bare, code, km.end() - 1)
                parts = split_top(b)
                if not parts:
                    continue
                rule_start, rule_bare = parts[-1]
                rule_text = c[rule_start:rule_start + len(rule_bare)].strip()
                name = re.match(r'\s*(\w+)', rule_bare)
                lead = b[:rule_start]
                method = re.search(r'HttpMethod\s*\.\s*(\w+)', lead)
                patterns = strings_in(c[:rule_start])
                is_any = bool(re.search(r'\b(anyRequest|anyExchange)\b', lead))
                if 'EndpointRequest' in lead:
                    patterns.append('<actuator>')
                if not patterns and not is_any:
                    patterns = ['/**'] if method else []
                if name:
                    chain['rules'].append({'patterns': patterns, 'method': method.group(1) if method else None,
                                           'rule': name.group(1), 'text': rule_text, 'any': is_any,
                                           'line': jf.src.line_at(start + km.start())})
            chain['rules'].sort(key=lambda r: r['line'])
            for kind in ('csrf', 'headers', 'cors', 'frameOptions'):
                for off, text in _configurer(bare, kind):
                    if re.search(r'\bdisable\b', text) and not re.search(r'ignoringRequestMatchers', text):
                        chain.setdefault(kind + '_off', jf.src.line_at(start + off))
            chain['stateless'] = 'STATELESS' in bare
            for flag in ('formLogin', 'oauth2Login', 'oauth2ResourceServer', 'httpBasic', 'saml2Login',
                         'rememberMe', 'logout', 'sessionManagement', 'oneTimeTokenLogin', 'webAuthn'):
                chain[flag] = _configured(bare, flag)
            chains.append(chain)
    return chains


def _rule_after(bare: str, code: str, at: int) -> tuple[str, str] | None:
    m = re.match(r'\s*\.\s*(permitAll|authenticated|denyAll|anonymous|fullyAuthenticated|rememberMe|hasRole|'
                 r'hasAnyRole|hasAuthority|hasAnyAuthority|access|hasIpAddress|not)\s*\(', bare[at:at + 120])
    if not m:
        return None
    open_at = at + m.end() - 1
    close = balanced(bare, open_at)
    text = code[at:close + 1].strip().lstrip('.').strip() if close > 0 else m.group(1)
    if m.group(1) == 'not':
        nested = _rule_after(bare, code, close + 1)
        return ('not ' + nested[0], text + (nested[1] if nested else '')) if nested else ('not', text)
    return m.group(1), text


def check_security_setup(ctx: Ctx, chains: list[dict]):
    controllers = ctx.by['controller']
    has_security = bool(re.search(r'spring-boot-starter-security|spring-security-|starter-oauth2|'
                                  r'security-oauth2|spring-boot-starter-security-\w+', ctx.build))
    if controllers and not has_security:
        ctx.hit('SB-NO-SECURITY', controllers[0], controllers[0].cls.offset if controllers[0].cls else 0,
                f'{len(controllers)} controllers, no spring-security dependency in any build file')

    users = [(jf, m) for jf in ctx.main for m in jf.members if m.has(*ctx.auth_annos)]
    enable = re.search(r'@Enable(Reactive)?MethodSecurity\b', ctx.all_main)
    legacy = re.search(r'@EnableGlobalMethodSecurity\s*\(([^)]*)\)', ctx.all_main)
    jf0 = users[0][0] if users else None
    uses = {a for _, m in users for a in m.annos if a in ctx.auth_annos}
    if users and not enable and not (legacy and 'prePostEnabled' in legacy.group(1)):
        ctx.hit('SB-SEC-METHOD-OFF', jf0, users[0][1].anno_offset,
                f'{len(users)} annotated members ({", ".join(sorted(uses))}), no @EnableMethodSecurity')
    elif users:
        enable_text = (enable.group(0) if enable else '') + ctx.all_main[enable.end():enable.end() + 200] \
            if enable else legacy.group(0)
        for anno, flag in (('Secured', 'securedEnabled'), ('RolesAllowed', 'jsr250Enabled')):
            if anno in uses and not re.search(flag + r'\s*=\s*true', enable_text):
                where = next((jf, m) for jf, m in users if anno in m.annos)
                ctx.hit('SB-SEC-METHOD-OFF', where[0], where[1].anno_offset,
                        f'@{anno} used, {flag} = true missing on the method security annotation')
    for jf, m in users:
        if m.kind == 'method' and m.private:
            ctx.hit('SB-SEC-PRIVATE', jf, m.offset, f'{m.anno_text.strip()} {m.sig.strip()}'[:160])

    if any(j.kotlin for j in ctx.main) and not re.search(
            r'plugin\.spring|kotlin-spring|allopen|all-open|kotlin\("plugin\.spring"\)', ctx.build):
        build = next((f for f in ctx.repo.files if f.endswith('build.gradle.kts') or f.endswith('pom.xml')), None)
        ctx.hit('SB-KOTLIN-NO-ALLOPEN', build, None, 'no kotlin("plugin.spring") / allopen in any build file')

    for jf in ctx.main:
        for pattern, sev, label in (
                (r'WebSecurityConfigurerAdapter\b', 'high', 'WebSecurityConfigurerAdapter (Spring Security 5)'),
                (r'@EnableGlobalMethodSecurity\b', 'medium', '@EnableGlobalMethodSecurity -> @EnableMethodSecurity'),
                (r'\.(antMatchers|mvcMatchers|regexMatchers)\s*\(', 'medium', 'antMatchers/mvcMatchers -> requestMatchers'),
                (r'\.authorizeRequests\s*\(', 'medium', 'authorizeRequests -> authorizeHttpRequests'),
                (r'\)\s*\.\s*and\s*\(\s*\)', 'medium', '.and() chaining - removed in Spring Security 7')):
            m = re.search(pattern, jf.src.bare)
            if m:
                ctx.hit('SB-SEC-REMOVED-API', jf, m.start(), label, severity=sev)

    for c in chains:
        rel = c['file']
        anys = [r for r in c['rules'] if r['any']]
        if anys and anys[-1]['rule'] in PUBLIC_RULES:
            scoped = ', '.join(c['matchers'])
            ctx.hit('SB-SEC-PERMITALL-ANY', rel, anys[-1]['line'],
                    anys[-1]['text'] + (f'   chain scoped to {scoped}' if scoped else ''),
                    severity='low' if scoped else None)
        if not anys and not c['matchers']:
            ctx.hit('SB-SEC-NO-DEFAULT-DENY', rel, c['line'], f'chain {c["name"]}: {len(c["rules"])} rules, '
                                                                  'no anyRequest()')
        if 'csrf_off' in c:
            cookie_login = c['formLogin'] or c['oauth2Login'] or c['saml2Login'] or c['rememberMe']
            sev = 'high' if cookie_login or not c['stateless'] else 'low'
            ctx.hit('SB-SEC-CSRF-OFF', rel, c['csrf_off'],
                    f'chain {c["name"]}: csrf disabled, stateless={c["stateless"]}, '
                    f'formLogin={c["formLogin"]}, oauth2Login={c["oauth2Login"]}', severity=sev)
        for kind in ('headers_off', 'frameOptions_off'):
            if kind in c:
                ctx.hit('SB-SEC-HEADERS-OFF', rel, c[kind], f'chain {c["name"]}: {kind[:-4]} disabled')
        exposed = set()
        for _, entries in ctx.configs:
            for e in entries:
                if e.norm.endswith('management.endpoints.web.exposure.include') and profile_kind(e.profile) != 'dev':
                    exposed |= {x.strip().strip('"\'') for x in e.value.strip('[]').split(',')}
        for r in c['rules']:
            if r['rule'] in PUBLIC_RULES and any(p == '<actuator>' or re.match(r'/actuator/\*', p)
                                                 for p in r['patterns']):
                sensitive = exposed & SENSITIVE_ACTUATOR
                ctx.hit('SB-AUTHZ-ACTUATOR-PUBLIC', rel, r['line'],
                        f'{r["text"]} {", ".join(r["patterns"])}   exposed: {", ".join(sorted(exposed)) or "health (default)"}',
                        severity='high' if sensitive else 'low')

    cors_any = re.compile(r'allowedOrigin(s|Patterns)\s*\(\s*(listOf\(|List\.of\(|arrayOf\()?\s*"\*"|'
                          r'addAllowedOrigin(Pattern)?\s*\(\s*"\*"|allowedOrigin(s|Patterns)\s*=\s*'
                          r'(listOf\(|mutableListOf\()?\s*"\*"|setAllowedOrigin(s|Patterns)\s*\(\s*'
                          r'(listOf\(|List\.of\(|Arrays\.asList\(|Collections\.singletonList\()\s*"\*"')
    for jf in ctx.main:
        for m in cors_any.finditer(jf.src.code):
            creds = bool(re.search(r'allowCredentials\s*(\(|=)\s*true|setAllowCredentials\s*\(\s*true',
                                   jf.src.code))
            ctx.hit('SB-SEC-CORS', jf, m.start(), severity='high' if creds else 'medium',
                    evidence=jf.src.line(jf.src.line_at(m.start())).strip() + f'   (allowCredentials={creds})')
        for m in re.finditer(r'@CrossOrigin\b(\s*\(([^)]*)\))?', jf.src.code):
            args = m.group(2) or ''
            if not args.strip() or '"*"' in args:
                ctx.hit('SB-SEC-CORS', jf, m.start(), severity='medium')
    for src, entries in ctx.configs:
        for e in entries:
            if re.search(r'allowedorigin', e.norm) and e.value.strip('"\'[] ') == '*':
                ctx.hit('SB-SEC-CORS', src.rel, e.line, f'{e.key}: {e.value}')



def endpoints(ctx: Ctx, chains: list[dict]) -> list[dict]:
    out = []
    consts = string_consts(ctx)
    for jf, cls in ((jf, c) for jf in ctx.main for c in jf.classes if c.has('RestController', 'Controller')):
        prefixes = ['']
        for name, b, c in _anno_args(cls, re.compile(r'@RequestMapping\b')):
            prefixes = _paths(b, c, consts)
        class_auth = [a for a in cls.annos if a in ctx.auth_annos]
        for m in jf.methods(cls):
            for name, b, c in _anno_args(m, MAPPING):
                verb = MAPPING.match(name).group(1)
                methods = [verb.upper()] if verb != 'Request' else \
                    (re.findall(r'RequestMethod\s*\.\s*(\w+)', b) or ['ANY'])
                auth = [a for a in m.annos if a in ctx.auth_annos]
                auth_text = re.findall(r'@(?:PreAuthorize|Secured|RolesAllowed|PostAuthorize)\s*\(([^\n]*)\)',
                                       m.anno_code)
                body = next((p for p in m.params if 'RequestBody' in p.annos), None)
                urlish = [p.name for p in m.params if
                          ({'RequestParam', 'PathVariable', 'RequestBody'} & set(p.annos)) and URLISH.match(p.name)]
                for prefix in prefixes:
                    for path in _paths(b, c, consts):
                        for http in methods:
                            out.append({'http': http, 'path': _join(prefix, path), 'controller': cls.name,
                                        'method': m.name, 'file': jf.rel, 'line': m.line,
                                        'auth': auth, 'auth_text': [t[:80] for t in auth_text],
                                        'class_auth': class_auth,
                                        'body': body.type if body else None,
                                        'valid': bool(body and {'Valid', 'Validated'} & set(body.annos)),
                                        'returns': m.returns, 'urlish': urlish,
                                        'params': [p.name for p in m.params], '_member': m, '_jf': jf,
                                        '_body': body.name if body else None})
    for jf in ctx.main:
        if not re.search(r'\bcoRouter\b|\brouter\s*\{|RouterFunctions\s*\.\s*route|RouterFunctions\.route',
                         jf.src.bare):
            continue
        for m in re.finditer(r'\b(GET|POST|PUT|PATCH|DELETE)\s*\(\s*"([^"]*)"', jf.src.code):
            out.append({'http': m.group(1), 'path': _join(m.group(2)), 'controller': jf.name,
                        'method': '(router)', 'file': jf.rel, 'line': jf.src.line_at(m.start()),
                        'auth': [], 'auth_text': [], 'class_auth': [], 'body': None, 'valid': True,
                        'returns': '', 'urlish': [], 'params': [], '_member': None, '_jf': jf})

    ordered = sorted(chains, key=lambda c: (c['order'], c['index']))
    for e in out:
        key = re.sub(r'\{[^}]*\}', 'x', e['path'])
        e['url_rule'], e['chain'] = None, None
        for c in ordered:
            if c['matchers'] and not _matches(c['matchers'], key):
                continue
            e['chain'] = f'{c["file"]}:{c["line"]}'
            for r in c['rules']:
                if r['method'] not in (None, '?') and e['http'] not in (r['method'], 'ANY'):
                    continue
                if r['any'] or (_regex_match(r, key) if r.get('regex') else _matches(r['patterns'], key)):
                    e['url_rule'], e['url_rule_text'] = r['rule'], r['text']
                    break
            break
    return out


def _regex_match(rule: dict, path: str) -> bool:
    for p in rule['patterns']:
        try:
            if re.fullmatch(p, path):
                return True
        except re.error:
            pass
    return False


def check_endpoints(ctx: Ctx, eps: list[dict], chains: list[dict]):
    mutating = {'POST', 'PUT', 'PATCH', 'DELETE', 'ANY'}
    for e in eps:
        method_auth = bool(e['auth'] or e['class_auth'])
        label = f'{e["http"]} {e["path"]} -> {e["controller"]}.{e["method"]}'
        if chains and not method_auth:
            if e['url_rule'] in PUBLIC_RULES and e['http'] in mutating:
                sev = 'medium' if INTENDED_PUBLIC.search(e['path']) else 'high'
                ctx.hit('SB-AUTHZ-PUBLIC-WRITE', e['file'], e['line'], f'{label}   rule: {e["url_rule_text"]}',
                        severity=sev)
            elif e['url_rule'] is None:
                ctx.hit('SB-AUTHZ-UNMATCHED', e['file'], e['line'], f'{label}   chain: {e["chain"] or "none"}')
        if e['http'] == 'ANY':
            ctx.hit('SB-ANY-METHOD', e['file'], e['line'], label)
        if e['body'] and e['http'] in mutating and not e['valid']:
            ctx.hit('SB-NO-VALID', e['file'], e['line'], f'{label}   body: {e["body"]}')
        urlish = e['urlish'] + [f'{e["_body"]}.{f}' for f in dto_fields(ctx, e['body'])
                                if e.get('_body') and URLISH.match(f)]
        if urlish and e['_member'] is not None and 'InetAddressFilter' not in ctx.all_main:
            reach = flow(ctx, e['_jf'], e['_member'], set(urlish), _url_sink, 2)
            if reach:
                ctx.hit('SB-SSRF-INPUT', e['file'], e['line'], f'{label}   params: {", ".join(urlish)}',
                        note=chain_text(reach))
        if any(t in ctx.entity_names for t in re.findall(r'\w+', e['body'] or '')):
            ctx.hit('SB-ENTITY-REQUEST', e['file'], e['line'], f'{label}   body: {e["body"]}')
        ret = re.findall(r'\w+', e['returns'] or '')
        if any(t in ctx.entity_names for t in ret):
            ctx.hit('SB-ENTITY-RESPONSE', e['file'], e['line'], f'{label}   returns: {e["returns"]}')
        m = e['_member']
        if m is not None and m.body:
            body = e['_jf'].src.code[m.body[0]:m.body[1]]
            names = [p for p in e['params'] if PATHISH.match(p)]
            for call in re.finditer(r'(Paths\s*\.\s*get|Path\s*\.\s*of|\bFile|FileSystemResource|UrlResource|'
                                    r'\.resolve|FileInputStream|FileOutputStream)\s*\(([^)]*)\)', body):
                if any(re.search(r'\b' + re.escape(n) + r'\b', call.group(2)) for n in names):
                    ctx.hit('SB-PATH-TRAVERSAL', e['file'], e['line'], f'{label}   {call.group(0)[:90]}')
                    break

    by_controller = defaultdict(list)
    for e in eps:
        by_controller[(e['file'], e['controller'])].append(e)
    for (rel, name), group in by_controller.items():
        with_auth = [e for e in group if e['auth']]
        if not with_auth or any(e['class_auth'] for e in group):
            continue
        sample = with_auth[0]['auth_text'][0] if with_auth[0]['auth_text'] else '@' + with_auth[0]['auth'][0]
        for e in group:
            if not e['auth'] and e['http'] in mutating and e['url_rule'] in (None, 'authenticated', 'permitAll',
                                                                              'anonymous', 'fullyAuthenticated'):
                ctx.hit('SB-AUTHZ-INCONSISTENT', rel, e['line'],
                        f'{e["http"]} {e["path"]} has no method check - {len(with_auth)} of {len(group)} '
                        f'siblings in {name} do ({sample[:60]})')



SQL_STRICT = re.compile(r'\b(createQuery|createNativeQuery|createSQLQuery|createSelectionQuery|createMutationQuery|'
                        r'executeQuery|executeUpdate|executeLargeUpdate|prepareStatement|prepareCall|addBatch|'
                        r'queryForObject|queryForList|queryForMap|queryForRowSet|queryForStream|batchUpdate)\s*\(')
SQL_BOUND = re.compile(r'\b(?:jdbc\w*|\w*[Tt]emplate|\w*[Jj]dbc[Cc]lient|statement|stmt|conn\w*|session|em|'
                       r'entityManager|dsl|db|database)\s*\??\.\s*(query|update|execute|sql|fetch|resultQuery)\s*\(')
KT_TEMPLATE = re.compile(r'\$\{(?!\'\$\'\})|\$[a-z_]\w*')


def _dynamic(bare: str, code: str, kotlin: bool) -> str | None:
    for m in re.finditer(r'\+', bare):
        left, right = bare[:m.start()].rstrip(), bare[m.end():].lstrip()
        if not left or not right or not ('"' in (left[-1], right[0])):
            continue
        operand = re.match(r'(\w+)', right) if left.endswith('"') else re.search(r'(\w+)\s*\)?$', left)
        if operand and not re.fullmatch(r'[A-Z][A-Z0-9_]*', operand.group(1)):
            return 'concatenation'
    if kotlin:
        for s in strings_in(code):
            t = KT_TEMPLATE.search(s)
            if t and not re.fullmatch(r'\$[A-Z][A-Z0-9_]*', t.group(0)):
                return 'string template'
    if re.search(r'\bString\s*\.\s*format\s*\(|\.format\s*\(|\.formatted\s*\(', bare):
        return 'format'
    return None


def check_sinks(ctx: Ctx):
    outbound = OUTBOUND.search(ctx.all_main)
    for jf in ctx.main:
        bare, code, kt = jf.src.bare, jf.src.code, jf.kotlin
        for rx in (SQL_STRICT, SQL_BOUND):
            for m in rx.finditer(bare):
                b, c, _ = _args(bare, code, m.end() - 1)
                parts = split_top(b)
                if not parts:
                    continue
                first_start, first = parts[0]
                how = _dynamic(first, c[first_start:first_start + len(first)], kt)
                ident = re.fullmatch(r'\s*([a-z]\w*)\s*(\.toString\(\))?\s*', first)
                if not how and ident:
                    name = ident.group(1)
                    decl = re.search(r'(?:val|var|String|StringBuilder|final\s+String)\s+' + name +
                                     r'\s*(?::\s*\w+\s*)?=\s*', bare)
                    if decl:
                        end = bare.find('\n\n', decl.end())
                        end = len(bare) if end < 0 else end
                        stmt_end = decl.end()
                        depth = 0
                        while stmt_end < end:
                            ch = bare[stmt_end]
                            depth += ch in '([{'
                            depth -= ch in ')]}'
                            if (ch == ';' or (ch == '\n' and depth <= 0 and not re.match(
                                    r'\s*[.+]', bare[stmt_end + 1:stmt_end + 20]))):
                                break
                            stmt_end += 1
                        how = _dynamic(bare[decl.end():stmt_end], code[decl.end():stmt_end], kt)
                    if not how and re.search(r'\b' + name + r'\s*(\+=|\.append\s*\()\s*(?!")', bare):
                        how = 'built with += / append'
                if how:
                    ctx.hit('SB-SQL-CONCAT', jf, m.start(), note=how)
        for m in re.finditer(r'\bparseExpression\s*\(', bare):
            b, c, _ = _args(bare, code, m.end() - 1)
            if not re.fullmatch(r'\s*"[^"]*"\s*', c) and 'Spel' in bare + ' '.join(jf.imports):
                ctx.hit('SB-SPEL-INJECTION', jf, m.start())
        for m in re.finditer(r'Runtime\s*\.\s*getRuntime\s*\(\s*\)\s*\.\s*exec\s*\(|\bProcessBuilder\s*\(', bare):
            b, c, _ = _args(bare, code, m.end() - 1)
            dynamic = re.search(r'[A-Za-z_]\w*', re.sub(r'"[^"]*"', '', c)) is not None
            ctx.hit('SB-CMD-EXEC', jf, m.start(), severity='high' if dynamic else 'low')
        for pattern in (r'\bObjectInputStream\s*\(', r'\.enableDefaultTyping\s*\(', r'\.activateDefaultTyping\s*\(',
                        r'JsonTypeInfo\s*\.\s*Id\s*\.\s*(CLASS|MINIMAL_CLASS)\b|use\s*=\s*Id\s*\.\s*(CLASS|MINIMAL_CLASS)\b',
                        r'\bXStream\s*\(', r'\bXMLDecoder\s*\(', r'SerializationUtils\s*\.\s*deserialize\s*\(',
                        r'\bfromXML\s*\('):
            for m in re.finditer(pattern, bare):
                ctx.hit('SB-DESERIALIZATION', jf, m.start())
        hardened = re.search(r'disallow-doctype-decl|FEATURE_SECURE_PROCESSING|ACCESS_EXTERNAL_DTD|'
                             r'IS_SUPPORTING_EXTERNAL_ENTITIES|SUPPORT_DTD|external-general-entities|'
                             r'setExpandEntityReferences\s*\(\s*false', code)
        if not hardened:
            for m in re.finditer(r'\b(DocumentBuilderFactory|SAXParserFactory|XMLInputFactory|TransformerFactory|'
                                 r'SchemaFactory|XMLReaderFactory)\s*\.\s*(newInstance|newFactory|newDefaultInstance|'
                                 r'createXMLReader)\s*\(|\bSAXReader\s*\(|\bSAXBuilder\s*\(', bare):
                ctx.hit('SB-XXE', jf, m.start())
        for m in re.finditer(r'"redirect:|\b(sendRedirect|RedirectView)\s*\(', code):
            if m.group(1):
                close = balanced(bare, m.end() - 1)
                expr_at, expr_end = m.end(), (close if close > 0 else m.end())
            else:
                expr_at, expr_end = m.start(), statement_end(bare, m.start())
            first = split_top(bare[expr_at:expr_end])
            if first:
                expr_at, expr_end = expr_at + first[0][0], expr_at + first[0][0] + len(first[0][1])
            if not _pinned(ctx, jf, expr_at, expr_end):
                ctx.hit('SB-OPEN-REDIRECT', jf, m.start())
        if re.search(r'getOriginalFilename\s*\(|\.originalFilename\b', bare) and \
                re.search(r'Paths\s*\.\s*get|Path\s*\.\s*of|\bFile\s*\(|\.resolve\s*\(|transferTo\s*\(|'
                          r'FileOutputStream\s*\(', bare):
            m = re.search(r'getOriginalFilename\s*\(|\.originalFilename\b', bare)
            ctx.hit('SB-PATH-TRAVERSAL', jf, m.start(), note='uploaded file name next to a filesystem call')
        if outbound:
            for m in re.finditer(r'\b(?:URL|URI)\s*\(\s*(?!")[a-z]\w*\s*\)\s*\.\s*(openConnection|openStream|toURL)|'
                                 r'new\s+URL\s*\(\s*(?!")[a-z]\w*\s*\)', bare):
                ctx.hit('SB-SSRF-INPUT', jf, m.start(), severity='low', note='URL from a variable')

        for m in re.finditer(r'MessageDigest\s*\.\s*getInstance\s*\(\s*"(MD2|MD4|MD5|SHA-?1|SHA)"|'
                             r'DigestUtils\s*\.\s*(md5|sha1|sha)(Hex|Digest)?\s*\(|Hashing\s*\.\s*(md5|sha1)\s*\(',
                             code):
            near = code[max(0, m.start() - 300):m.end() + 300].lower()
            ctx.hit('SB-WEAK-HASH', jf, m.start(), severity='high' if 'password' in near else 'medium')
        for m in re.finditer(r'Cipher\s*\.\s*getInstance\s*\(\s*"([^"]+)"', code):
            alg = m.group(1).upper()
            if re.match(r'(DES|DESEDE|RC2|RC4|BLOWFISH|ARCFOUR)\b', alg) or alg == 'AES' or '/ECB/' in alg:
                ctx.hit('SB-WEAK-CIPHER', jf, m.start(), severity='medium' if alg.startswith('RSA') else None)
            elif alg == 'RSA' or 'NOPADDING' in alg and alg.startswith('RSA'):
                ctx.hit('SB-WEAK-CIPHER', jf, m.start(), severity='medium')
        for m in re.finditer(r'IvParameterSpec\s*\(\s*(new\s+byte\s*\[|ByteArray\s*\(|byteArrayOf|"[^"]*"\s*\.\s*'
                             r'(toByteArray|getBytes)|[A-Z_]{3,}\s*[),])', code):
            ctx.hit('SB-STATIC-IV', jf, m.start())
        for m in re.finditer(r'\b(NoOpPasswordEncoder|StandardPasswordEncoder|Md5PasswordEncoder|ShaPasswordEncoder|'
                             r'LdapShaPasswordEncoder|MessageDigestPasswordEncoder|Md4PasswordEncoder)\b', bare):
            ctx.hit('SB-PASSWORD-ENCODER', jf, m.start())
        for m in re.finditer(r'"\{noop\}', code):
            ctx.hit('SB-PASSWORD-ENCODER', jf, m.start(), severity='high')
        for m in re.finditer(r'BCryptPasswordEncoder\s*\(\s*([4-9])\s*[,)]', bare):
            ctx.hit('SB-BCRYPT-STRENGTH', jf, m.start())
        for m in re.finditer(r'(?<![\w.])Random\s*\(|Math\s*\.\s*random\s*\(|ThreadLocalRandom\s*\.\s*current|'
                             r'RandomStringUtils\s*\.\s*random\w*\s*\(|kotlin\.random\.Random|'
                             r'\bRandom\s*\.\s*next\w+\s*\(', bare):
            window = code[max(0, m.start() - 250):m.end() + 250]
            if re.search(r'(?i)(token|secret|password|otp|nonce|salt|reset|verification|api.?key|invite|'
                         r'session|csrf|activation)', window) and 'SecureRandom' not in window:
                ctx.hit('SB-INSECURE-RANDOM', jf, m.start())
        for m in re.finditer(r'\b(TrustAllStrategy|TrustSelfSignedStrategy|NoopHostnameVerifier|AllowAllHostnameVerifier|'
                             r'ALLOW_ALL_HOSTNAME_VERIFIER|InsecureTrustManagerFactory)\b|'
                             r'checkServerTrusted\s*\([^)]*\)\s*(:\s*Unit\s*)?\{\s*\}|'
                             r'(HostnameVerifier|hostnameVerifier|setHostnameVerifier)\s*[({]\s*\(?\s*\w+\s*,\s*\w+\s*\)?'
                             r'\s*->\s*true', bare):
            ctx.hit('SB-TLS-TRUST-ALL', jf, m.start())
        for m in re.finditer(r'\b(parseUnsecuredClaims|parseUnsecured|parseClaimsJwt)\s*\(|Algorithm\s*\.\s*none\s*\(|'
                             r'\bPlainJWT\b', bare):
            ctx.hit('SB-JWT-UNVERIFIED', jf, m.start())
        if re.search(r'\bJWT\s*\.\s*decode\s*\(', bare) and not re.search(r'JWT\s*\.\s*require\s*\(|JWTVerifier',
                                                                          bare):
            m = re.search(r'\bJWT\s*\.\s*decode\s*\(', bare)
            ctx.hit('SB-JWT-UNVERIFIED', jf, m.start(), note='JWT.decode without JWT.require/verify in the file')
        for m in re.finditer(r'(setSigningKey|signWith|verifyWith|hmacShaKeyFor|HMAC\d+|SecretKeySpec)\s*\(\s*'
                             r'"([^"]{6,})"', code):
            ctx.hit('SB-JWT-HARDCODED-KEY', jf, m.start(), evidence=f'{m.group(1)}("{redact(m.group(2))}")',
                    secret=secret_id(m.group(2)))

        for m in re.finditer(r'\b(log|logger|LOG|LOGGER|log\.atInfo\(\)|klogger)\s*\.\s*(trace|debug|info|warn|warning|error)'
                             r'\s*\(', bare):
            b, c, _ = _args(bare, code, m.end() - 1)
            sensitive = r'(?i)(password|passwd|secret|token|credential|apikey|api_key|authorization|bearer|iban|' \
                        r'creditcard|cardnumber|privatekey)'
            in_code = re.search(r'\b\w*' + sensitive[4:] + r'\w*\b', b)
            in_template = kt and any(re.search(r'\$\{?[\w.]*' + sensitive[4:], s, re.I) for s in strings_in(c))
            if (in_code and not re.search(r'(?i)(Service|Encoder|Provider|Repository|Type|Filter|Util|Exception|'
                                          r'Valid|Expired|Length|Count|Header)\b', in_code.group(0))) or in_template:
                ctx.hit('SB-LOG-SECRET', jf, m.start())
        if jf.stereotype == 'advice':
            for m in re.finditer(r'\b(ex|e|exception|throwable|t|err|error|cause)\s*\.\s*(message|localizedMessage|'
                                 r'getMessage\s*\(\s*\)|getLocalizedMessage\s*\(\s*\)|stackTraceToString\s*\(\s*\)|'
                                 r'stackTrace)\b', bare):
                ctx.hit('SB-ERROR-LEAK', jf, m.start())
                break



IDENTITY_HEADER = re.compile(r'(?i)^(?:x-)?(?:auth(?:enticated)?-|forwarded-|remote-|original-|end-)?'
                             r'(?:user(?:-?id|-?name)?|username|benutzer(?:-?id)?|tenant(?:-?id)?|mandant(?:-?id)?|'
                             r'org(?:-?id)?|organi[sz]ation(?:-?id)?|account(?:-?id)?|roles?|rollen?|groups?|e-?mail|'
                             r'subject|principal|userinfo|preferred-username|customer(?:-?id)?|kunde(?:-?id)?|'
                             r'permissions?|scopes?|is-?admin)$')
CLIENT_IP_HEADER = re.compile(r'(?i)^(x-forwarded-for|x-real-ip|forwarded|x-client-ip|true-client-ip|cf-connecting-ip)$')
_ARG = r'([\w."-]+)'
HEADER_READ = re.compile(r'@RequestHeader\s*\(\s*(?:(?:name|value)\s*=\s*)?' + _ARG +
                         r'|@RequestHeader\s+(?:(\w+)\s*:|\w+\s+(\w+)\s*[,)])'
                         r'|\b(?:getHeader|getHeaders|firstHeader)\s*\(\s*' + _ARG + r'\s*\)'
                         r'|\b(?:headers?|request)\s*(?:\(\s*\))?\s*\??\.\s*(?:getFirst|get|header)\s*\(\s*' + _ARG +
                         r'\s*\)|\bheaders\s*\[\s*' + _ARG + r'\s*\]')


def header_constants(ctx: Ctx) -> dict[str, str]:
    return dict(re.findall(r'\b([A-Z][A-Z0-9_]+|\w*[Hh]eader\w*)\s*(?::\s*String)?\s*=\s*"([\w-]+)"',
                           '\n'.join(j.src.code for j in ctx.main)))


def check_headers(ctx: Ctx):
    constants = header_constants(ctx)
    for jf in ctx.main:
        for m in HEADER_READ.finditer(jf.src.code):
            arg = next(g for g in m.groups() if g)
            name = arg.strip('"') if arg.startswith('"') else constants.get(arg.split('.')[-1], arg)
            evidence = f'{name}: ' + jf.src.line(jf.src.line_at(m.start())).strip()
            if IDENTITY_HEADER.match(name):
                ctx.hit('SB-HEADER-TRUST', jf, m.start(), evidence)
            elif CLIENT_IP_HEADER.match(name):
                ctx.hit('SB-HEADER-TRUST', jf, m.start(), evidence, severity='medium',
                        note='client IP - rate limits, audit logs and allow-lists can be spoofed')


def check_config(ctx: Ctx):
    for src, entries in ctx.configs:
        for e in entries:
            kind = profile_kind(e.profile)
            value = e.value.strip()
            last = e.key.split('.')[-1]
            if SECRET_KEY.search(last) or SECRET_KEY.search('.'.join(e.key.split('.')[-2:])):
                fallback = re.fullmatch(r'\$\{[^:}]+:([^}]*)\}', value)
                if fallback and fallback.group(1).strip() and not NOT_A_SECRET.match(fallback.group(1).strip()):
                    fb = fallback.group(1).strip()
                    ctx.hit('SB-CFG-SECRET-DEFAULT', src.rel, e.line,
                            f'{e.key}: ${{...:{redact(fb)}}}   profile={e.profile or "default"}',
                            severity='medium' if kind == 'dev' else None, secret=secret_id(fb))
                elif value and not NOT_A_SECRET.match(value) and not value.startswith('${'):
                    if kind == 'dev':
                        sev = 'low'
                    elif WEAK_DEFAULT.match(value):
                        sev = 'high'
                    else:
                        sev = 'critical' if entropy(value) >= 3.5 and len(value) >= 16 else 'high'
                    ctx.hit('SB-CFG-SECRET', src.rel, e.line,
                            f'{e.key}: {redact(value)}   profile={e.profile or "default"}', severity=sev,
                            tracked=ctx.repo.is_tracked(src.rel), secret=secret_id(value))
            if kind == 'dev':
                continue
            n = e.norm
            if n.endswith('management.endpoints.web.exposure.include'):
                exposed = {x.strip().strip('"\'') for x in value.strip('[]').split(',')}
                bad = exposed & SENSITIVE_ACTUATOR
                if bad:
                    sev = 'high' if bad & {'*', 'env', 'heapdump', 'configprops', 'shutdown', 'jolokia',
                                           'threaddump', 'loggers', 'logfile'} else 'medium'
                    ctx.hit('SB-CFG-ACTUATOR', src.rel, e.line, f'{e.key}: {value}', severity=sev)
            elif re.match(r'management\.endpoint\.shutdown\.(enabled|access)$', n) and \
                    value.lower() in ('true', 'unrestricted'):
                ctx.hit('SB-CFG-ACTUATOR', src.rel, e.line, f'{e.key}: {value}', severity='critical')
            elif re.match(r'management\.endpoint\.(env|configprops|quartz)\.showvalues$', n) and value.lower() == 'always':
                ctx.hit('SB-CFG-ACTUATOR', src.rel, e.line, f'{e.key}: {value}', severity='high')
            elif re.match(r'server\.error\.include(stacktrace|message|exception|bindingerrors)$', n) and \
                    value.lower() in ('always', 'true', 'onparam', 'on-param', 'on_param'):
                ctx.hit('SB-CFG-ERROR-DETAILS', src.rel, e.line, f'{e.key}: {value}')
            elif n == 'spring.h2.console.enabled' and value.lower() == 'true':
                ctx.hit('SB-CFG-H2-CONSOLE', src.rel, e.line, f'{e.key}: {value}   profile={e.profile or "default"}')
            elif n.startswith('logging.level.') and value.upper() in ('DEBUG', 'TRACE') and \
                    re.search(r'root|security|web|springframework$|hibernate\.(sql|orm\.jdbc\.bind|type)', n):
                ctx.hit('SB-CFG-DEBUG', src.rel, e.line, f'{e.key}: {value}   profile={e.profile or "default"}')
            elif n in ('debug', 'trace') and value.lower() == 'true':
                ctx.hit('SB-CFG-DEBUG', src.rel, e.line, f'{e.key}: {value}')
            elif re.match(r'server\.(servlet|reactive)\.session\.cookie\.(secure|httponly)$', n) and \
                    value.lower() == 'false':
                ctx.hit('SB-CFG-COOKIE', src.rel, e.line, f'{e.key}: {value}')
            elif n.endswith('hibernate.ddlauto') and value.lower() in ('update', 'create', 'create-drop'):
                ctx.hit('SB-CFG-DDL-AUTO', src.rel, e.line, f'{e.key}: {value}   profile={e.profile or "default"}')
    if ctx.by['entity'] and not re.search(r'open-?in-?view\s*[:=]\s*false|openinview\s*[:=]\s*false',
                                          ctx.config_text, re.I):
        rel = next((s.rel for s, _ in ctx.configs if '/src/main/' in '/' + s.rel), None)
        ctx.hit('SB-CFG-OPEN-IN-VIEW', rel, None, 'spring.jpa.open-in-view is not set to false')



def check_persistence(ctx: Ctx):
    superclasses = {j.cls.name: j for j in ctx.by['superclass'] if j.cls}

    def has_pk(names: list[str], depth: int = 0) -> bool:
        for n in names:
            j = superclasses.get(n)
            if j and (re.search(r'@(Id|EmbeddedId)\b', j.src.bare) or
                      (depth < 3 and has_pk(entity_x.supertypes_of(j.src.bare[j.cls.offset:].split('{')[0])
                                            if j.kotlin else re.findall(r'extends\s+(\w+)', j.cls.header),
                                            depth + 1))):
                return True
        return False

    ctx.entity_names = set()
    for jf in ctx.by['entity']:
        ctx.entity_names.add(jf.name)
        try:
            found = entity_x.entity(jf.src.path)
        except Exception as exc:  # the vendored extractor must never stop a scan
            print(f'  entity extractor failed on {jf.rel}: {exc}', file=sys.stderr)
            found = None
        if not found:
            continue
        name, data = found
        cols = data['columns']
        if not any(c.get('pk') for c in cols) and not has_pk(data['supertypes']) and \
                not re.search(r'@(Id|EmbeddedId)\b', jf.src.bare):
            ctx.hit('SB-ENTITY-NO-PK', jf, jf.cls.offset, f'{name}: {len(cols)} columns, '
                                                          f'supertypes {data["supertypes"] or "-"}')
        if len(cols) > 25:
            ctx.hit('SB-ENTITY-WIDE', jf, jf.cls.offset, f'{name}: {len(cols)} columns, table {data["table"]}')
        for c in cols:
            t = c['type']
            if t.startswith('? ') and t[2:].strip() in ctx.enums and t[2:].strip() not in ctx.converted:
                line = next((i for i, l in enumerate(jf.src.lines, 1)
                             if re.search(r'\b' + re.escape(t[2:].strip()) + r'\b', l) and
                             re.search(r'\b(va[lr]|private|protected)\b', l)), None)
                ctx.hit('SB-ENUM-ORDINAL', jf.rel, line, f'{name}.{c["name"]}: {t[2:]} without @Enumerated')
    ctx.entity_names |= {c.name for j in ctx.main for c in j.classes if c.has('Entity')}
    for jf in ctx.by['entity']:
        for m in re.finditer(r'@Enumerated\b(?!\s*\(\s*(?:value\s*=\s*)?(?:EnumType\s*\.\s*)?STRING)', jf.src.bare):
            ctx.hit('SB-ENUM-ORDINAL', jf, m.start())
        if jf.kotlin and jf.cls and re.search(r'\bdata\s+class\b', jf.cls.sig):
            ctx.hit('SB-ENTITY-DATA-CLASS', jf, jf.cls.offset)
        for m in re.finditer(r'@(ManyToOne|OneToOne)\b(\s*\(([^)]*)\))?', jf.src.bare):
            if 'LAZY' not in (m.group(3) or ''):
                ctx.hit('SB-EAGER', jf, m.start(), note='ToOne defaults to EAGER')
        for m in re.finditer(r'FetchType\s*\.\s*EAGER', jf.src.bare):
            ctx.hit('SB-EAGER', jf, m.start())
    for jf in ctx.by['repository']:
        methods = [m for m in jf.methods() if not m.private]
        if len(methods) > 20:
            ctx.hit('SB-REPO-SIZE', jf, jf.cls.offset, f'{jf.name}: {len(methods)} query methods')
    if ctx.by['entity'] and not re.search(r'flyway|liquibase', ctx.build, re.I):
        ctx.hit('SB-NO-MIGRATIONS', ctx.by['entity'][0], ctx.by['entity'][0].cls.offset,
                f'{len(ctx.by["entity"])} entities, no flyway/liquibase dependency')



def _deps(jf: jvm.JFile) -> list[str]:
    cls = jf.cls
    if not cls:
        return []
    if jf.kotlin:
        types = [p.type for p in cls.params]
    else:
        ctors = [m for m in jf.methods(cls) if m.name == cls.name]
        types = [p.type for p in max(ctors, key=lambda m: len(m.params)).params] if ctors else []
        if not types and re.search(r'@(RequiredArgsConstructor|AllArgsConstructor)\b', cls.anno_text):
            types = [f.returns for f in jf.members if f.kind == 'field' and f.owner is cls
                     and re.match(r'\s*private\s+final\b', f.sig) and 'static' not in f.sig]
    types += [f.returns for f in jf.members if f.kind == 'field' and f.has('Autowired', 'Inject')]
    return [t for t in types if t]


def check_structure(ctx: Ctx):
    beans = [j for j in ctx.main if j.stereotype in ('controller', 'service', 'component', 'client', 'advice')]
    for jf in beans:
        deps = _deps(jf)
        if len(deps) > 10:
            ctx.hit('SB-CTOR-DEPS', jf, jf.cls.offset, f'{jf.name}: {len(deps)} dependencies')
        lines = jf.src.text.count('\n') + 1
        try:
            public, _, _, _ = funs_x.members(jf.src.path)
        except Exception:
            public = [m.sig for m in jf.methods() if not m.private]
        if lines > 400 or len(public) > 15:
            ctx.hit('SB-CLASS-SIZE', jf, jf.cls.offset, f'{jf.name}: {lines} lines, {len(public)} public methods')
        for m in jf.methods():
            if len(m.params) > 6 and not m.private and not m.has('Bean'):
                ctx.hit('SB-METHOD-PARAMS', jf, m.offset, f'{jf.name}.{m.name}: {len(m.params)} parameters')
        if jf.stereotype == 'controller':
            repos = [t for t in deps if re.search(r'Repository\b', t) or
                     any(t.split('<')[0].strip() == r.name for r in ctx.by['repository'])]
            if repos:
                ctx.hit('SB-CTRL-REPO', jf, jf.cls.offset, f'{jf.name} injects {", ".join(repos)}')
            for m in jf.members:
                if m.has('Transactional'):
                    ctx.hit('SB-TX-CONTROLLER', jf, m.anno_offset)
                    break
    for jf in ctx.main:
        for m in jf.members:
            if m.kind == 'field' and m.has('Autowired'):
                ctx.hit('SB-FIELD-INJECTION', jf, m.offset)
            if m.kind == 'method' and m.has('Transactional') and m.private:
                ctx.hit('SB-TX-PRIVATE', jf, m.offset)
            if m.kind == 'method' and m.body and (m.has('Transactional') or (m.owner and m.owner.has('Transactional'))
                                                  and not m.private) and not tx_safe(m, jf.body_text(m)):
                direct = remote_sites(ctx, jf, *m.body)
                hop = None if direct else next(iter(paths(ctx, jf, m, remote_sites, 2, tx=True)), None)
                site = direct[0] if direct else hop[-1][2] if hop else None
                if site:
                    head = f'{m.owner.name if m.owner else jf.name}.{m.name}: {site["text"][:60]}' if direct \
                        else chain_text(hop)
                    ctx.hit('SB-TX-REMOTE-CALL', jf, m.offset, head + ' inside a transaction',
                            **({'note': 'the mail goes out even when the transaction rolls back'}
                               if site['kind'] == 'mail' else {}))

    shedlock = re.search(r'shedlock', ctx.build, re.I)
    for jf in ctx.main:
        for m in jf.methods():
            if m.has('Scheduled') and not m.has('SchedulerLock'):
                ctx.hit('SB-SCHEDULED-NO-LOCK', jf, m.offset,
                        f'{jf.name}.{m.name}' + ('' if shedlock else '   (no ShedLock dependency)'))

    clients = [j for j in ctx.main if OUTBOUND.search(j.src.bare)]
    if clients and not (TIMEOUT.search(ctx.all_main) or TIMEOUT.search(ctx.config_text)):
        ctx.hit('SB-HTTP-NO-TIMEOUT', clients[0], 0, f'{len(clients)} files use an HTTP client: '
                + ', '.join(j.name for j in clients[:6]))
    for jf in ctx.main:
        for m in re.finditer(r'(?<![\w.])(new\s+)?RestTemplate\s*\(\s*\)', jf.src.bare):
            ctx.hit('SB-HTTP-NO-TIMEOUT', jf, m.start(), severity='medium', note='RestTemplate() has no timeouts')

    published, listened = {}, {}
    for jf in ctx.main:
        for m in re.finditer(r'publishEvent\s*\(\s*(?:new\s+)?([A-Z]\w+)\s*\(', jf.src.bare):
            published.setdefault(m.group(1), (jf, m.start()))
        for m in jf.methods():
            if m.has('EventListener', 'TransactionalEventListener', 'ApplicationModuleListener'):
                explicit = re.findall(r'(\w+)(?:::class|\.class)', m.anno_text)
                types = explicit or [p.type.split('<')[0].strip('? ') for p in m.params[:1]]
                for t in types:
                    listened.setdefault(t, (jf, m.offset))
        for m in re.finditer(r'ApplicationListener\s*<\s*(\w+)', jf.src.bare):
            listened.setdefault(m.group(1), (jf, m.start()))

    externalized = 'Externalized' in ctx.all_main
    for t, (jf, off) in published.items():
        if not lineage(ctx, t) & set(listened) and t in ctx.class_names and not externalized:
            ctx.hit('SB-EVENT-ORPHAN', jf, off, f'publishes {t}, no listener in this codebase')
    for t, (jf, off) in listened.items():
        covered = any(t in lineage(ctx, p) for p in published)
        if not covered and t in ctx.class_names and not re.search(r'\b' + t + r'\s*\(', ctx.all_main):
            ctx.hit('SB-EVENT-ORPHAN', jf, off, f'listens to {t}, nothing constructs it')

    for jf in ctx.main:
        for m in re.finditer(r'\bcatch\s*\([^)]*\)\s*\{\s*\}', jf.src.bare):
            ctx.hit('SB-SWALLOWED', jf, m.start())
        for m in re.finditer(r'\.printStackTrace\s*\(\s*\)|System\s*\.\s*(out|err)\s*\.\s*print|(?<![\w.])println\s*\(',
                             jf.src.bare):
            ctx.hit('SB-STDOUT', jf, m.start())

    if (len(ctx.main) > 60 or len(ctx.stack['modules']) > 1) and 'archunit' not in ctx.build.lower():
        ctx.hit('SB-NO-ARCHUNIT', None, None, f'{len(ctx.main)} production classes, '
                                              f'{len(ctx.stack["modules"])} modules, no archunit dependency')
    tested_text = '\n'.join(s.text for s in ctx.tests)
    targets = [j for j in ctx.main if j.stereotype in ('controller', 'service')]
    untested = [j.name for j in targets if not re.search(r'\b' + re.escape(j.name) + r'\b', tested_text)]
    if targets and untested:
        ctx.hit('SB-UNTESTED', None, None, f'{len(untested)} of {len(targets)} controllers/services: '
                + ', '.join(untested[:12]) + (' ...' if len(untested) > 12 else ''),
                names=untested)
    for s in ctx.tests:
        m = re.search(r'@(MockBean|SpyBean)\b', s.text)
        if m and ctx.boot() >= (3, 4):
            ctx.hit('SB-MOCKBEAN', s.rel, s.line_at(m.start()), s.line(s.line_at(m.start())).strip(),
                    keep_in_tests=True)

    if ctx.boot() >= (4,):
        for jf in ctx.main:
            m = re.search(r'(?m)^\s*import\s+com\.fasterxml\.jackson\.databind\.(ObjectMapper|json\.JsonMapper|'
                          r'module\.SimpleModule|SerializationFeature|DeserializationFeature)', jf.src.bare)
            if m:
                ctx.hit('SB-JACKSON2-ON-BOOT4', jf, m.start())
        for pattern, label in ((r'spring-boot-starter-web["\':]', 'spring-boot-starter-web -> spring-boot-starter-webmvc'),
                               (r'spring-boot-starter-aop\b', 'spring-boot-starter-aop -> spring-boot-starter-aspectj'),
                               (r'spring-boot-starter-oauth2-(resource-server|client)\b',
                                'spring-boot-starter-oauth2-* -> spring-boot-starter-security-oauth2-*')):
            found = []
            for f in ctx.repo.files:
                if os.path.basename(f) in ('build.gradle.kts', 'build.gradle', 'pom.xml') or f.endswith('.versions.toml'):
                    src = ctx.repo.source(f)
                    m = re.search(pattern, src.text)
                    if m:
                        found.append((f, src.line_at(m.start())))
            if found:
                ctx.hit('SB-BOOT4-RENAMED', found[0][0], found[0][1],
                        label + (f'   ({len(found)} build files)' if len(found) > 1 else ''))

    check_packages(ctx)


def check_packages(ctx: Ctx):
    packages = [j.package for j in ctx.main if j.package]
    if not packages:
        return
    base = os.path.commonprefix([p.split('.') for p in packages])
    depth = len(base) + 1
    own = '.'.join(base)

    def feature(pkg: str) -> str | None:
        parts = pkg.split('.')
        return '.'.join(parts[:depth]) if len(parts) >= depth and pkg.startswith(own) else None

    edges = defaultdict(dict)
    for jf in ctx.main:
        src_feature = feature(jf.package)
        for imp in jf.imports:
            if not imp.startswith(own + '.'):
                continue
            target = feature('.'.join(imp.split('.')[:-1]))
            if src_feature and target and target != src_feature:
                edges[src_feature].setdefault(target, (jf, imp))
            if '.internal.' in imp + '.':
                owner = imp.split('.internal')[0]
                if not jf.package.startswith(owner):
                    off = jf.src.bare.find(imp)
                    ctx.hit('SB-INTERNAL-IMPORT', jf, off, f'{jf.package} imports {imp}')

    index, low, stack, on, sccs = {}, {}, [], set(), []

    def strong(v):
        index[v] = low[v] = len(index)
        stack.append(v)
        on.add(v)
        for w in edges.get(v, {}):
            if w not in index:
                strong(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on.discard(w)
                comp.append(w)
                if w == v:
                    break
            if len(comp) > 1:
                sccs.append(comp)

    sys.setrecursionlimit(max(10000, sys.getrecursionlimit()))
    for v in list(edges):
        if v not in index:
            strong(v)
    for comp in sccs:
        short = [c[len(own) + 1:] for c in comp]
        a, b = comp[0], next(w for w in edges[comp[0]] if w in comp)
        jf, imp = edges[a][b]
        back = next(((x, y) for x, y in edges[b].items() if x in comp), None)
        ctx.hit('SB-PACKAGE-CYCLE', jf, jf.src.bare.find(imp),
                f'cycle {" <-> ".join(short)}: {a[len(own) + 1:]} imports {imp.split(".")[-1]}'
                + (f', {b[len(own) + 1:]} imports {back[1][1].split(".")[-1]}' if back else ''))


CLIENT_TYPES = {
    'RestTemplate': 'http', 'RestOperations': 'http', 'RestClient': 'http', 'WebClient': 'http', 'HttpClient': 'http',
    'OkHttpClient': 'http', 'CloseableHttpClient': 'http', 'CloseableHttpAsyncClient': 'http',
    'HttpAsyncClient': 'http', 'AsyncHttpClient': 'http', 'JavaMailSender': 'mail', 'MailSender': 'mail',
    'JavaMailSenderImpl': 'mail', 'KafkaTemplate': 'kafka', 'KafkaOperations': 'kafka',
    'ReactiveKafkaProducerTemplate': 'kafka', 'RabbitTemplate': 'rabbit', 'AmqpTemplate': 'rabbit',
    'RabbitOperations': 'rabbit', 'RabbitMessagingTemplate': 'rabbit', 'JmsTemplate': 'jms', 'JmsOperations': 'jms',
    'JmsMessagingTemplate': 'jms', 'JmsClient': 'jms', 'StreamBridge': 'stream',
}
CLIENT_VERBS = {
    'http': re.compile(r'(get|post|put|patch|delete|head|options|method|exchange|execute\w*|send|sendAsync|newCall|'
                       r'getFor\w+|postFor\w+|patchForObject|headForHeaders|optionsForAllow|request|submitForm\w*|'
                       r'prepare\w+)$'),
    'mail': re.compile(r'send$'),
    'kafka': re.compile(r'(send\w*|executeInTransaction)$'),
    'rabbit': re.compile(r'(send|convertAndSend|convertSendAndReceive\w*|sendAndReceive\w*)$'),
    'jms': re.compile(r'(send\w*|convertAndSend|convertSendAndReceive\w*)$'),
    'stream': re.compile(r'send$'),
}
FACTORY = re.compile(r'(?:new\s+)?(RestClient|WebClient|HttpClient|OkHttpClient|HttpClients|HttpAsyncClients|'
                     r'RestTemplate|RestTemplateBuilder|HttpClientBuilder|DefaultAsyncHttpClient|AsyncHttpClient|'
                     r'JavaMailSenderImpl)\b(?:\.Builder)?')
STATIC_REMOTE = [
    (re.compile(r'\b(RestClient|WebClient)\s*\.\s*create\s*\([^()]*\)\s*\.\s*(get|post|put|patch|delete)\s*\('), 'http'),
    (re.compile(r'\b(HttpClient)\s*\.\s*newHttpClient\s*\(\s*\)\s*\.\s*(send\w*)\s*\('), 'http'),
    (re.compile(r'\b(Transport)\s*\.\s*(send)\s*\('), 'mail'),
    (re.compile(r'\b(URL|URI)\s*\([^()]*\)(?:\s*\.\s*toURL\s*\(\s*\))?\s*\.\s*(openConnection|openStream)\s*\('), 'http'),
]
TYPED_KT = re.compile(r'(?<![\w.])(\w+)\s*:\s*([\w.]+(?:\s*<[^<>\n]*(?:<[^<>\n]*>[^<>\n]*)?>)?\??)')
TYPED_JAVA = re.compile(r'(?<![\w.])([A-Z][\w.]*(?:\s*<[^<>\n]*(?:<[^<>\n]*>[^<>\n]*)?>)?)\s+(\w+)\s*(?=[;=,)])')
INIT = re.compile(r'(?:\b(?:val|var)\s+|\b[A-Z][\w.]*(?:<[^<>\n]*>)?\s+|\bthis\s*\.\s*)(\w+)(?:\s*:\s*[\w.<>?, ]+?)?'
                  r'\s*(?:=(?!=)|by\s+lazy\s*\{)\s*')
GETTER = re.compile(r'\bfun\s+(\w+)\s*\(\s*\)\s*:\s*([\w.<>?]+)|\b([A-Z][\w.]*(?:<[^<>\n]*>)?)\s+(\w+)\s*\(\s*\)\s*\{')
UNWRAP = re.compile(r'\s*(?:[?!]*\.\s*(?:ifAvailable|getIfAvailable\s*\(\s*\)|getObject\s*\(\s*\)|`?object`?|ifUnique|'
                    r'getIfUnique\s*\(\s*\)|get\s*\(\s*\))|!!)?\s*;?\s*')
FILTER_TYPES = {'OncePerRequestFilter', 'GenericFilterBean', 'Filter', 'HandlerInterceptor', 'AsyncHandlerInterceptor',
                'WebFilter', 'WebRequestInterceptor', 'HandlerInterceptorAdapter',
                'AbstractAuthenticationProcessingFilter'}
FILTER_METHODS = {'doFilterInternal', 'doFilter', 'preHandle', 'filter', 'attemptAuthentication'}
TX_SAFE = re.compile(r'\b(afterCommit|registerSynchronization|isSynchronizationActive|isActualTransactionActive)\b')
CALL = re.compile(r'(?<![\w.$])(?:this\s*\.\s*)?(\w+)\s*(?:\?\.|!!\.|\.)\s*(\w+)\s*\(')
LOCAL_CALL = re.compile(r'(?<![\w.$])(\w+)\s*\(')


def remote_kind(receiver: str) -> str:
    r = receiver.lower()
    for k in ('kafka', 'rabbit', 'jms', 'stream', 'mail'):
        if k in r:
            return k
    return 'http'


def client_kind(t: str, declarative: set) -> str | None:
    t = re.sub(r'\s+', '', t or '').rstrip('?')
    inner = re.fullmatch(r'(?:[\w.]*\.)?(?:ObjectProvider|Provider|Optional|Lazy)<(.+)>', t)
    parts = (inner.group(1) if inner else t).rstrip('?').split('<')[0].split('.')
    if parts[-1] == 'Builder' and len(parts) > 1 and parts[-2] in CLIENT_TYPES or \
            parts[-1] in ('RestTemplateBuilder', 'HttpClientBuilder'):
        return 'builder'
    if parts[-1] in CLIENT_TYPES:
        return CLIENT_TYPES[parts[-1]]
    return 'declarative' if parts[-1] in declarative else None


def statement_end(bare: str, start: int, limit: int = 1500) -> int:
    """End of the statement or call chain starting at `start`: `;`, or a newline at depth 0 not continuing a chain."""
    depth, i, stop = 0, start, min(len(bare), start + limit)
    while i < stop:
        ch = bare[i]
        if ch in '([{':
            depth += 1
        elif ch in ')]}':
            depth -= 1
            if depth < 0:
                return i
        elif depth == 0 and (ch == ';' or ch == '\n' and bare[start:i].strip() and
                             not re.match(r'\s*(\?\.|\.|\?:|\+|&&|\|\||\))', bare[i + 1:i + 40])):
            return i
        i += 1
    return i


def graph(ctx: Ctx) -> dict:
    g = getattr(ctx, '_graph', None)
    if g:
        return g
    classes, parents, methods, files, declarative = {}, defaultdict(set), defaultdict(list), {}, set()
    for jf in ctx.main:
        for c in jf.classes:
            classes.setdefault(c.name, (jf, c))
            files[id(c)] = jf
            head = re.sub(r'\s+', ' ', c.header)
            if jf.kotlin:
                names = entity_x.supertypes_of(head.split('{')[0])
            else:
                names = re.findall(r'\b(?:extends|implements)\s+([\w\s,<>.]+)', head)
                names = [n.strip().split('<')[0].split('.')[-1] for part in names for n in part.split(',')]
            parents[c.name] |= {n.split('.')[-1] for n in names if n}
            if c.has('FeignClient', 'HttpExchange'):
                declarative.add(c.name)
        for m in jf.methods():
            if m.owner:
                methods[(m.owner.name, m.name)].append((jf, m))
                if re.search(r'@(Get|Post|Put|Patch|Delete)Exchange\b', m.anno_text):
                    declarative.add(m.owner.name)
    impls = defaultdict(set)
    for c, ps in parents.items():
        for p in ps:
            impls[p].add(c)
    ctx._graph = g = {'classes': classes, 'parents': parents, 'impls': impls, 'methods': methods, 'files': files,
                      'declarative': declarative, 'fields': {}, 'callees': {}, 'paths': {}, 'recv': {}}
    return g


def lineage(ctx: Ctx, name: str) -> set[str]:
    parents = graph(ctx)['parents']
    seen, todo = set(), [name]
    while todo:
        x = todo.pop()
        if x not in seen:
            seen.add(x)
            todo += parents.get(x, ())
    return seen


def fields(ctx: Ctx, cls: jvm.Member | None) -> dict[str, str]:
    if cls is None:
        return {}
    g = graph(ctx)
    if id(cls) not in g['fields']:
        out = {p.name: p.type for p in cls.params}
        jf = g['files'].get(id(cls))
        for m in (jf.members if jf else []):
            if m.owner is cls and m.kind == 'field' and m.returns:
                out.setdefault(m.name, m.returns)
            elif m.owner is cls and m.kind == 'method' and m.name == cls.name:
                for p in m.params:
                    out.setdefault(p.name, p.type)
        g['fields'][id(cls)] = out
    return g['fields'][id(cls)]


def type_targets(ctx: Ctx, t: str) -> list[str]:
    g = graph(ctx)
    inner = re.match(r'\s*(?:[\w.]*\.)?(?:ObjectProvider|Provider|Optional|Lazy)\s*<\s*([\w.]+)', t or '')
    base = (inner.group(1) if inner else re.sub(r'<.*', '', t or '')).strip('?! ').split('.')[-1]
    out, todo = [], [base]
    while todo:
        x = todo.pop()
        if x not in out:
            out.append(x)
            todo += sorted(g['impls'].get(x, ()))
    return [x for x in out if x in g['classes']]


def receivers(ctx: Ctx, jf: jvm.JFile) -> dict[str, dict]:
    """Names in the file that hold an outbound client: typed fields and params, built values, getters."""
    g = graph(ctx)
    if jf.rel in g['recv']:
        return g['recv'][jf.rel]
    bare = jf.src.bare
    out = {}
    rx = TYPED_KT if jf.kotlin else TYPED_JAVA
    for m in rx.finditer(bare):
        name, t = (m.group(1), m.group(2)) if jf.kotlin else (m.group(2), m.group(1))
        kind = client_kind(t, g['declarative'])
        if kind:
            out.setdefault(name, {'kind': kind, 'type': re.sub(r'\s+', '', t), 'init': None, 'from': None})
    for m in GETTER.finditer(bare):
        name, t = (m.group(1), m.group(2)) if m.group(1) else (m.group(4), m.group(3))
        kind = client_kind(t, g['declarative'])
        if kind and name not in out:
            end = statement_end(bare, m.end()) if m.group(1) else m.end()
            out[name + '()'] = {'kind': kind, 'type': t, 'init': (m.end(), end), 'from': None}
    for _ in range(2):
        for m in INIT.finditer(bare):
            name = m.group(1)
            if name in out and out[name]['init']:
                continue
            end = statement_end(bare, m.end())
            init = bare[m.end():end]
            f = FACTORY.match(init)
            src = re.match(r'(?:this\s*\.\s*)?(\w+)(\s*\(\s*\))?', init)
            key = src and src.group(1) + ('()' if src.group(2) else '')
            kind, origin = None, None
            if f:
                built = re.search(r'\.\s*build\s*\(\s*\)', init)
                kind = 'builder' if re.search(r'\.\s*(builder|newBuilder|custom)\s*\(', init) and not built or \
                    f.group(0).endswith('Builder') and not built else ('mail' if f.group(1) == 'JavaMailSenderImpl'
                                                                       else 'http')
            elif src and key in out and key != name:
                base, rest = out[key], init[src.end():]
                origin = key
                if base['kind'] == 'builder' and re.search(r'\.\s*build\s*\(\s*\)', rest):
                    kind = 'http'
                elif UNWRAP.fullmatch(rest):
                    kind = base['kind']
            if kind:
                out[name] = {'kind': kind, 'type': out.get(origin, {}).get('type') or (f.group(1) if f else ''),
                             'init': (m.end(), end), 'from': origin}
    g['recv'][jf.rel] = out
    return out


def _recv_rx(recv: dict) -> re.Pattern | None:
    names = sorted({n.rstrip('()') for n in recv}, key=len, reverse=True)
    if not names:
        return None
    return re.compile(r'(?<![\w.$])(?:this\s*\.\s*)?(' + '|'.join(map(re.escape, names)) +
                      r')\b(\s*\(\s*\))?\s*(?:\?\.|!!\.|\.)\s*(\w+)\s*[({]')


def remote_sites(ctx: Ctx, jf: jvm.JFile, start: int, end: int) -> list[dict]:
    recv = receivers(ctx, jf)
    bare, code = jf.src.bare, jf.src.code
    out, seen = [], set()
    rx = _recv_rx(recv)
    for c in (rx.finditer(bare, start, end + 1) if rx else ()):
        r = recv.get(c.group(1) + ('()' if c.group(2) else '')) or recv.get(c.group(1))
        verb = c.group(3)
        seen.add(c.start())
        if not r or r['kind'] == 'builder':
            continue
        kind = 'http' if r['kind'] == 'declarative' else r['kind']
        if r['kind'] == 'declarative' and verb in ('equals', 'hashCode', 'toString') or \
                r['kind'] != 'declarative' and not CLIENT_VERBS[kind].match(verb):
            continue
        out.append({'offset': c.start(), 'receiver': c.group(1), 'verb': verb, 'kind': kind,
                    'text': code[c.start():c.end() - 1] + '(', 'declarative': r['kind'] == 'declarative'})
    for c in REMOTE_CALL.finditer(bare, start, end + 1):
        receiver = c.group(1)
        if c.start() in seen or receiver in recv or \
                re.search(r'(Repository|Repo|Mapper|Factory|Builder|Converter|Validator)$', receiver):
            continue
        out.append({'offset': c.start(), 'receiver': receiver, 'verb': c.group(2), 'kind': remote_kind(receiver),
                    'text': code[c.start():c.end()]})
    for rx2, kind in STATIC_REMOTE:
        for c in rx2.finditer(bare, start, end + 1):
            out.append({'offset': c.start(), 'receiver': c.group(1), 'verb': c.group(2), 'kind': kind,
                        'text': code[c.start():c.end()]})
    if not any(r['kind'] == 'mail' for r in recv.values()):
        for c in re.finditer(r'\bMimeMessageHelper\s*\(', bare[start:end + 1]):
            out.append({'offset': start + c.start(), 'receiver': 'MimeMessageHelper', 'verb': 'send', 'kind': 'mail',
                        'text': c.group(0)})
            break
    return sorted(out, key=lambda s: s['offset'])


def callees(ctx: Ctx, jf: jvm.JFile, m: jvm.Member) -> list[tuple]:
    """(offset, label, open paren offset, [(jf, member)], same class) for every call this method makes into a
    bean method through an injected field, or into a method of its own class."""
    g = graph(ctx)
    if id(m) in g['callees']:
        return g['callees'][id(m)]
    out = []
    if m.body and m.owner:
        start, end = m.body
        bare = jf.src.bare
        own = fields(ctx, m.owner)
        for c in CALL.finditer(bare, start, end + 1):
            t = own.get(c.group(1))
            if not t:
                continue
            targets = [x for n in type_targets(ctx, t) for x in g['methods'].get((n, c.group(2)), [])]
            if targets:
                out.append((c.start(), f'{c.group(1)}.{c.group(2)}', c.end() - 1, targets, False))
        for c in LOCAL_CALL.finditer(bare, start, end + 1):
            targets = [x for x in g['methods'].get((m.owner.name, c.group(1)), []) if x[1] is not m]
            if targets:
                out.append((c.start(), c.group(1), c.end() - 1, targets, True))
    g['callees'][id(m)] = out
    return out


def tx_safe(m: jvm.Member, body: str) -> bool:
    return m.has('Async', 'TransactionalEventListener') or bool(m.owner and m.owner.has('Async')) or \
        bool(TX_SAFE.search(body)) or bool(re.search(r'Propagation\s*\.\s*(NOT_SUPPORTED|NEVER)', m.anno_text))


def paths(ctx: Ctx, jf: jvm.JFile, m: jvm.Member, sites, depth: int, tx: bool = False, _stack=()) -> list[list]:
    """Every way from this method to a site `sites` finds, through own-class calls (free) and up to `depth` bean
    hops. A path is [(jf, member, site), ...]; every site but the last is the call into the next method."""
    g = graph(ctx)
    key = (id(m), sites, depth, tx)
    if key in g['paths']:
        return g['paths'][key]
    if not m.body or id(m) in _stack or (tx and tx_safe(m, jf.body_text(m))):
        return []
    out = [[(jf, m, s)] for s in sites(ctx, jf, *m.body)]
    for off, label, _, targets, local in callees(ctx, jf, m):
        d = depth if local else depth - 1
        if d < 0:
            continue
        for jf2, m2 in targets:
            for p in paths(ctx, jf2, m2, sites, d, tx, _stack + (id(m),)):
                out.append([(jf, m, {'offset': off, 'text': label + '(', 'kind': 'call'})] + p)
                if len(out) > 40:
                    break
    g['paths'][key] = out
    return out


def chain_text(path: list, head: bool = True) -> str:
    out = []
    for i, (jf, m, s) in enumerate(path):
        out.append(('' if i == 0 and not head else f'{m.owner.name if m.owner else jf.name}.{m.name}: ')
                   + re.sub(r'\s+', '', s['text'])[:50])
    return ' -> '.join(out)


def sites_http(ctx, jf, start, end):
    return [s for s in remote_sites(ctx, jf, start, end) if s['kind'] == 'http']


def sites_mail(ctx, jf, start, end):
    return [s for s in remote_sites(ctx, jf, start, end) if s['kind'] == 'mail']


def request_filters(ctx: Ctx) -> list[tuple[jvm.JFile, jvm.Member]]:
    out = []
    for jf in ctx.main:
        for c in jf.classes:
            if lineage(ctx, c.name) & FILTER_TYPES:
                out += [(jf, m) for m in jf.methods(c) if m.name in FILTER_METHODS and m.body]
    return out


def config_values(ctx: Ctx, key: str, near: str = '') -> list[str]:
    """Values of a config key: the app closest to `near` first, then prod-like profiles, the default, dev; no tests."""
    norm = re.sub(r'[-_]', '', key.lower())
    found = []
    for src, entries in ctx.configs:
        if is_test_path(src.rel):
            continue
        shared = len(os.path.commonprefix([src.rel.split('/'), near.split('/')]))
        for e in entries:
            if e.norm == norm:
                found.append((-shared, {'prod-like': 0, 'default': 1}.get(profile_kind(e.profile), 2), e.value))
    return [v for *_, v in sorted(found, key=lambda x: x[:2])]


def _taint(ctx: Ctx, expr: str, tracked: set[str]) -> str | None:
    """'' when the expression carries a tracked value as a whole, a field name when it carries it in that field of
    a constructed object or of a passed object, None when it carries nothing tracked."""
    expr = expr.strip()
    named = re.match(r'(\w+)\s*=(?!=)\s*', expr)
    if named:
        expr = expr[named.end():]
    for t in tracked:
        obj, _, fld = t.partition('.')
        if fld and re.fullmatch(re.escape(obj) + r'\s*(!!)?', expr):
            return fld
    if not any(re.search(r'(?<![\w.$])' + r'\s*\??\.\s*'.join(map(re.escape, t.split('.'))) + r'\b', expr)
               for t in tracked):
        return None
    ctor = re.match(r'(?:new\s+)?([A-Z]\w*)\s*\(', expr)
    if ctor and ctor.group(1) in graph(ctx)['classes']:
        close = balanced(expr, ctor.end() - 1)
        if close == len(expr) - 1:
            params = graph(ctx)['classes'][ctor.group(1)][1].params
            for i, (_, part) in enumerate(split_top(expr[ctor.end():close])):
                if _taint(ctx, part, tracked) is not None:
                    name = re.match(r'\s*(\w+)\s*=(?!=)', part)
                    if name:
                        return name.group(1)
                    if i < len(params):
                        return params[i].name
    return ''


def flow(ctx: Ctx, jf: jvm.JFile, m: jvm.Member, tracked: set[str], sink, depth: int, _stack=()) -> list | None:
    """First path along which a tracked value (a name, or name.field) reaches `sink(ctx, jf, m, tracked)`: through
    derived locals, own-class calls (free) and up to `depth` bean hops. Lookups through another bean end the trail."""
    if not m.body or id(m) in _stack or not tracked:
        return None
    start, end = m.body
    bare, code = jf.src.bare, jf.src.code
    own = fields(ctx, m.owner)
    tracked = set(tracked)
    for _ in range(2):
        for d in re.finditer(r'\b(?:val|var|final\s+[\w.<>\[\]]+|[A-Z][\w.<>\[\]]*)\s+(\w+)\s*(?::\s*[\w.<>?]+\s*)?'
                             r'=(?!=)\s*', bare[start:end]):
            s = start + d.end()
            init = code[s:statement_end(bare, s)]
            lead = re.match(r'(?:this\s*\.\s*)?(\w+)\s*[?!]*\.\s*\w+\s*\(', init)
            if lead and lead.group(1) in own:
                continue
            t = _taint(ctx, init, tracked)
            if t is not None:
                tracked.add(d.group(1) + ('.' + t if t else ''))
    hit = sink(ctx, jf, m, tracked)
    if hit:
        return [(jf, m, hit)]
    for off, label, open_at, targets, local in callees(ctx, jf, m):
        close = balanced(bare, open_at)
        if close < 0:
            continue
        args = [(a, code[open_at + 1 + a:open_at + 1 + a + len(p)]) for a, p in split_top(bare[open_at + 1:close])]
        for i, (_, arg) in enumerate(args):
            t = _taint(ctx, arg, tracked)
            if t is None:
                continue
            named = re.match(r'\s*(\w+)\s*=(?!=)', arg)
            for jf2, m2 in targets:
                params = [p.name for p in m2.params]
                p = named.group(1) if named and named.group(1) in params else (params[i] if i < len(params) else None)
                if not p or (not local and depth < 1):
                    continue
                sub = flow(ctx, jf2, m2, {p + ('.' + t if t else '')}, sink, depth - (0 if local else 1),
                           _stack + (id(m),))
                if sub:
                    return [(jf, m, {'offset': off, 'text': label + '(', 'kind': 'call'})] + sub
    return None


def mentions(text: str, tracked: set[str]) -> bool:
    return any(re.search(r'(?<![\w.$])' + r'\s*\??\.\s*'.join(map(re.escape, t.split('.'))) + r'\b', text)
               for t in tracked)


def enclosing(jf: jvm.JFile, offset: int) -> jvm.Member | None:
    return next((m for m in jf.methods() if m.body and m.body[0] <= offset <= m.body[1]), None)


def owner_at(jf: jvm.JFile, offset: int) -> jvm.Member | None:
    owners = [c for c in jf.classes if c.body and c.body[0] <= offset <= c.body[1]]
    return max(owners, key=lambda c: c.body[0]) if owners else None


def dto_fields(ctx: Ctx, t: str | None) -> list[str]:
    found = graph(ctx)['classes'].get(re.sub(r'<.*', '', t or '').strip('?! ').split('.')[-1])
    if not found:
        return []
    jf, cls = found
    return [p.name for p in cls.params] + [m.name for m in jf.members if m.owner is cls and m.kind == 'field']


TEMPLATE_VAR = re.compile(r'\$\{\s*([^}]*)\}|\$([A-Za-z_]\w*)')


def _pins(prefix: str) -> bool:
    if prefix in ('', '/') or prefix.startswith('//'):
        return False
    if re.match(r'(?i)[a-z][\w+.-]*:', prefix):
        return bool(re.match(r'(?i)[a-z][\w+.-]*://[^/?#]+[/?#]', prefix))
    return True


def _pinned(ctx: Ctx, jf: jvm.JFile, start: int, end: int, depth: int = 2) -> bool:
    """True when a redirect target starts with a constant that fixes the host, or a path below /."""
    text, prefix, pos = jf.src.code[start:end], '', 0
    while True:
        lit = re.match(r'\s*"((?:\\.|[^"\\])*)"', text[pos:])
        if not lit:
            var = re.match(r'\s*((?:this\s*\.\s*)?[\w.]+)', text[pos:])
            if not var:
                return False
            var = var.group(1)
            break
        s = lit.group(1)
        s = s[len('redirect:'):] if not prefix and s.startswith('redirect:') else s
        t = TEMPLATE_VAR.search(s) if jf.kotlin else None
        prefix += s[:t.start()] if t else s
        if t:
            var = (t.group(1) or t.group(2)).strip()
            break
        pos += lit.end()
        plus = re.match(r'\s*\+', text[pos:])
        if not plus:
            return True
        pos += plus.end()
    return _pins(prefix) or (depth >= 0 and _constant(ctx, jf, start + pos, var, depth))


def _constant(ctx: Ctx, jf: jvm.JFile, at: int, var: str, depth: int) -> bool:
    if re.fullmatch(r'(?:[A-Z]\w*\.)*[A-Z][A-Z0-9_]+', var):
        return True
    name = re.match(r'(?:this\s*\.\s*)?(\w+)', var)
    m = enclosing(jf, at)
    if not name or m is None:
        return False
    name = name.group(1)
    bare = jf.src.bare
    if name in [p.name for p in m.params]:
        if MAPPING.search(m.anno_text):
            return False
        index = [p.name for p in m.params].index(name)
        verdicts = []
        for c in re.finditer(r'(?<![\w.])' + re.escape(m.name) + r'\s*\(', bare):
            if c.start() <= m.offset + len(m.sig) and c.start() >= m.offset:
                continue
            close = balanced(bare, c.end() - 1)
            args = split_top(bare[c.end():close]) if close > 0 else []
            if index >= len(args):
                return False
            a = c.end() + args[index][0]
            verdicts.append(_pinned(ctx, jf, a, a + len(args[index][1]), depth - 1))
        return bool(verdicts) and all(verdicts)
    local = re.search(r'\b(?:val|var|final\s+String|String)\s+' + re.escape(name) + r'\b[^=\n]*=(?!=)\s*',
                      bare[m.body[0]:m.body[1]])
    if local:
        s = m.body[0] + local.end()
        return _pinned(ctx, jf, s, statement_end(bare, s), depth - 1)
    return any(x.kind == 'field' and x.name == name and x.owner is m.owner for x in jf.members) or \
        name in fields(ctx, m.owner)


URL_SINK = re.compile(r'\b(?:URI\s*\.\s*create|URI|URL|new\s+UR[IL]|HttpRequest\s*\.\s*newBuilder|Jsoup\s*\.\s*connect|'
                      r'UrlResource)\s*\(|\.\s*(?:uri|url|baseUrl|getForObject|getForEntity|postForObject|postForEntity|'
                      r'postForLocation|exchange|openConnection)\s*\(')


def _url_sink(ctx, jf, m, tracked):
    bare, code = jf.src.bare, jf.src.code
    for c in URL_SINK.finditer(bare, m.body[0], m.body[1]):
        close = balanced(bare, c.end() - 1)
        args = split_top(bare[c.end():close]) if close > 0 else []
        if args and mentions(code[c.end() + args[0][0]:c.end() + args[0][0] + len(args[0][1])], tracked):
            return {'offset': c.start(), 'text': code[c.start():c.end()]}
    return None


def _outbound_sink(ctx, jf, m, tracked):
    for s in sites_http(ctx, jf, *m.body):
        if mentions(jf.src.code[s['offset']:statement_end(jf.src.bare, s['offset'])], tracked):
            return s
    return None


CHECKED = re.compile(r'==|!=|\.equals\s*\(|\bmatches\s*\(|isEqual\s*\(|\b(verify|check|validate|pruef|redeem|einloes)\w*'
                     r'\s*\(|\bauthenticate\s*\(|\b(find|exists|get|load)\w*By\w*\s*\(')


def _check_sink(ctx, jf, m, tracked):
    code = jf.src.code
    for line in code[m.body[0]:m.body[1]].split('\n'):
        if mentions(line, tracked) and CHECKED.search(line):
            return {'offset': m.body[0] + code[m.body[0]:m.body[1]].find(line), 'text': line.strip()[:50]}
    return None


RECIPIENT = re.compile(r'\b(?:setTo|addTo|to|setRecipients?|addRecipients?|setCc|setBcc|addCc|addBcc|InternetAddress|'
                       r'parse)\s*\(([^;\n]*)|\b(?:to|an|recipient|empfaenger)\s*=(?!=)\s*([^\n;,)]+)')


def _mail_to_sink(ctx, jf, m, tracked):
    sites = sites_mail(ctx, jf, *m.body)
    if not sites:
        return None
    for r in RECIPIENT.finditer(jf.src.code, m.body[0], m.body[1]):
        if mentions(r.group(1) or r.group(2) or '', tracked):
            return sites[0]
    return None


WRITE_VERB = re.compile(r'(save|insert|persist|merge|speichern)|'
                        r'(delete|remove|loeschen|entfernen|markUsed|consume|redeem|einloes|invalidate)')
CONSUMING = re.compile(r'(?i)confirm|verif|activat|aktivier|bestaetig|einloes|redeem|consume|unsubscribe|abmeld|login|'
                       r'anmeld|accept|approve|annehm|reset|markUsed')


def sites_write(ctx, jf, start, end):
    own = fields(ctx, owner_at(jf, start))
    g = graph(ctx)
    repos = {j.name for j in ctx.by['repository']}
    out = []
    for c in CALL.finditer(jf.src.bare, start, end + 1):
        recv, meth = c.group(1), c.group(2)
        base = re.sub(r'<.*', '', own.get(recv, '')).strip('?! ').split('.')[-1]
        verb = WRITE_VERB.match(meth)
        kind = None
        if recv in ('entityManager', 'em') and meth in ('persist', 'remove', 'merge'):
            kind = 'delete' if meth == 'remove' else 'save'
        elif base and (base in repos or re.search(r'(Repository|Repo|Dao)$', base)):
            kind = 'delete' if any(x.has('Modifying') for _, x in g['methods'].get((base, meth), [])) or \
                verb and verb.group(2) else 'save' if verb else None
        elif base and re.fullmatch(r'(Named\w*)?Jdbc(Template|Client|Operations)|DSLContext', base):
            kind = 'delete' if meth in ('update', 'batchUpdate') else None
        elif base and re.match(r'(markUsed|consume|redeem)', meth):
            kind = 'delete'
        if kind:
            out.append({'offset': c.start(), 'text': f'{recv}.{meth}(', 'kind': kind})
    return out


HOST_LINK = re.compile(r'ServletUriComponentsBuilder\s*\.\s*fromCurrent(?:ContextPath|Request|RequestUri|'
                       r'ServletMapping)\b|'
                       r'\b\w*[rR]equest\s*\.\s*(?:serverName|requestURL|getServerName\s*\(|getRequestURL\s*\()|'
                       r'\bgetHeader\s*\(\s*"(?:Host|X-Forwarded-Host)"')
BROAD_CATCH = re.compile(r'\bcatch\s*\(\s*(?:\w+\s*:\s*(?:[\w.]*\.)?(?:Exception|Throwable|RuntimeException)|'
                         r'(?:final\s+)?(?:[\w.]*\.)?(?:Exception|Throwable|RuntimeException)\s+\w+)\s*\)\s*\{')
SECRET_INPUT = re.compile(r'(?i)^\w*(code|pin|otp|tan|token|passwor[dt]|passcode|kennwort|secret)$')
NOT_SECRET_INPUT = re.compile(r'(?i)(country|postal|post|zip|lang\w*|currency|area|iso|status|error|product|article|'
                              r'region|state|branch|bank|tax|colou?r|class|type|kind|hash|qr|bar|short|refresh|csrf|xsrf|'
                              r'captcha|page|next|continuation|cursor|sort|spin|ou?tan|zeitpin)(code|token|pin|tan)?$|'
                              r'^(spin|span|tan|ota\w*)$')
EMAIL_NAME = re.compile(r'(?i)^(e-?mail\w*|\w*e-?mail(address|adresse)?|mail(address|adresse)?|recipient\w*|'
                        r'empfaenger\w*)$')
AUTH_PATH = re.compile(r'(?i)/(auth|login|logout|token|oauth2?|session|signin|sign-in|anmeld\w*|verify)\b')
NOT_RELAYED = re.compile(r'(?i)authorization|cookie|token|secret|passw|api-?key|code|session|signature|request-?id|'
                         r'correlation|trace|^b3$|user-agent|^accept|^content-|^if-|cache-control|^host$')
RATE_LIMITED = re.compile(r'(?i)bucket4j|rate.?limit|throttl|TOO_MANY_REQUESTS|\b429\b|@RateLimiter\b')


def check_flows(ctx: Ctx, eps: list[dict]):
    for jf, m in request_filters(ctx):
        bare = jf.src.bare
        start, end = m.body
        if not re.search(r'SecurityContextHolder|\.authentication\s*=|setAuthentication\s*\(|securityContext',
                         bare[start:end]):
            continue
        for c in BROAD_CATCH.finditer(bare, start, end):
            close = balanced(bare, c.end() - 1, '{', '}')
            block = bare[c.end():close]
            if close > 0 and not re.search(r'\b(throw|return)\b|sendError|setStatus\s*\(|\.status\s*=(?!=)|commence\s*\(|'
                                           r'onAuthenticationFailure', block) and \
                    re.search(r'\b\w*[cC]hain\s*\.\s*(doFilter|filter)\s*\(', bare[close:end]):
                ctx.hit('SB-AUTH-FILTER-SWALLOW', jf, c.start(), f'{m.owner.name}.{m.name}: '
                        + jf.src.code[c.start():c.end() - 1].strip() + ' - the chain continues afterwards')
                break

    constants = header_constants(ctx)
    relay = [(jf, m, None) for jf, m in request_filters(ctx)] + \
        [(e['_jf'], e['_member'], e) for e in eps if e['_member'] is not None and e['_member'].body and
         (AUTH_PATH.search(e['path']) or re.search(r'(?i)auth|login|token|session|security', e['controller']))]
    done = set()
    for jf, m, e in relay:
        if id(m) in done:
            continue
        done.add(id(m))
        body = jf.src.code[m.body[0]:m.body[1]]
        reads = [(v.group(1), v.group(2), m.body[0] + v.start()) for v in re.finditer(
            r'\b(?:val|var|final\s+String|String)\s+(\w+)\s*(?::\s*String\??\s*)?=\s*\w+\s*\.\s*(?:getHeader|header)\s*'
            r'\(\s*([\w."-]+)\s*\)', body)]
        for p in m.params:
            if 'RequestHeader' in p.annos and 'Pattern' not in p.annos:
                arg = re.search(r'RequestHeader\s*\(\s*(?:(?:name|value)\s*=\s*)?([\w."-]+)', p.code)
                reads.append((p.name, arg.group(1) if arg else p.name, m.offset))
        for var, arg, at in reads:
            name = arg.strip('"') if arg.startswith('"') else constants.get(arg.split('.')[-1], arg.split('.')[-1])
            if NOT_RELAYED.search(name) or re.search(r'\b(if|when|require|check)\b[^\n]*\b' + re.escape(var) + r'\b|\b'
                                                     + re.escape(var) + r'\s*(!?in\b|==|!=|\.equals|\.matches)', body):
                continue
            reach = flow(ctx, jf, m, {var}, _outbound_sink, 2)
            if reach:
                where = f'{e["http"]} {e["path"]} -> ' if e else ''
                ctx.hit('SB-HEADER-RELAY', jf.rel, jf.src.line_at(at),
                        f'{where}{m.owner.name}.{m.name}: header {name} -> {chain_text(reach, head=False)}')

    if not (RATE_LIMITED.search(ctx.build) or RATE_LIMITED.search(ctx.all_main) or
            RATE_LIMITED.search(ctx.config_text)):
        for e in eps:
            m = e['_member']
            if m is None or not m.body or e['url_rule'] not in PUBLIC_RULES or e['auth'] or e['class_auth']:
                continue
            tracked = {p.name for p in m.params if {'RequestParam', 'PathVariable', 'RequestHeader', 'RequestBody'} &
                       set(p.annos) and SECRET_INPUT.match(p.name) and not NOT_SECRET_INPUT.search(p.name)}
            tracked |= {f'{e["_body"]}.{f}' for f in dto_fields(ctx, e['body'])
                        if e['_body'] and SECRET_INPUT.match(f) and not NOT_SECRET_INPUT.search(f)}
            guessable = {t for t in tracked if not re.search(r'(?i)token$', t)}
            reach = tracked and (flow(ctx, e['_jf'], m, tracked, _outbound_sink, 1) or
                                 flow(ctx, e['_jf'], m, guessable, _check_sink, 1))
            if reach:
                ctx.hit('AUTH-NO-RATELIMIT', e['file'], e['line'],
                        f'{e["http"]} {e["path"]} -> {e["controller"]}.{e["method"]}   input: '
                        + ', '.join(sorted(tracked)), note=chain_text(reach))

    strategy = next(iter(config_values(ctx, 'server.forward-headers-strategy')), 'not set')
    public = {id(e['_member']) for e in eps if e['url_rule'] in PUBLIC_RULES and not (e['auth'] or e['class_auth'])}
    for jf in ctx.main:
        for m in jf.methods():
            link = HOST_LINK.search(jf.src.code, *m.body) if m.body else None
            mail = link and next(iter(paths(ctx, jf, m, sites_mail, 4)), None)
            if mail:
                source = re.sub(r'[\s(]+', '', link.group(0))
                ctx.hit('SB-HOST-HEADER-LINK', jf, link.start(),
                        f'{m.owner.name if m.owner else jf.name}.{m.name}: {source} -> mail via '
                        f'{chain_text(mail, head=False)}',
                        severity=None if id(m) in public else 'medium',
                        note=f'server.forward-headers-strategy: {strategy}'
                        + ('' if id(m) in public else ' - the caller is authenticated, it can only aim at itself'))

    for e in eps:
        m = e['_member']
        label = f'{e["http"]} {e["path"]} -> {e["controller"]}.{e["method"]}'
        if m is None or not m.body:
            continue
        if e['http'] == 'GET':
            write = next((p for p in paths(ctx, e['_jf'], m, sites_write, 1) if p[-1][2]['kind'] == 'delete' or
                          any(CONSUMING.search(x.name) for _, x, _ in p)), None)
            if write:
                ctx.hit('SB-GET-SIDE-EFFECT', e['file'], e['line'], f'{label}   {chain_text(write, head=False)}')
        if e['url_rule'] in PUBLIC_RULES and not (e['auth'] or e['class_auth']):
            tracked = {p.name for p in m.params if {'RequestParam', 'PathVariable', 'RequestBody'} & set(p.annos)
                       and EMAIL_NAME.match(p.name)}
            tracked |= {f'{e["_body"]}.{f}' for f in dto_fields(ctx, e['body']) if e['_body'] and EMAIL_NAME.match(f)}
            reach = flow(ctx, e['_jf'], m, tracked, _mail_to_sink, 4) if tracked else None
            if reach:
                ctx.hit('PUBLIC-MAIL-TO-INPUT', e['file'], e['line'],
                        f'{label}   recipient: {", ".join(sorted(tracked))}', note=chain_text(reach))


def run(ctx: Ctx) -> dict:
    ctx.entity_names = set()
    chains = parse_chains(ctx)
    check_security_setup(ctx, chains)
    check_persistence(ctx)
    eps = endpoints(ctx, chains)
    ctx.chains, ctx.endpoints = chains, eps
    check_endpoints(ctx, eps, chains)
    check_sinks(ctx)
    check_headers(ctx)
    check_config(ctx)
    check_structure(ctx)
    check_flows(ctx, eps)
    counts = defaultdict(int)
    for j in ctx.main:
        counts[j.stereotype or 'other'] += 1
    return {
        'counts': dict(counts),
        'chains': [{k: v for k, v in c.items() if k not in ('offset', 'index')} for c in chains],
        'endpoints': [{k: v for k, v in e.items() if not k.startswith('_')} for e in eps],
        'method_security': bool(re.search(r'@Enable(Reactive)?MethodSecurity|@EnableGlobalMethodSecurity',
                                          ctx.all_main)),
        'custom_auth_annotations': sorted(ctx.custom_auth),
    }
