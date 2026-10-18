# Evaluating the scan

## Reading a Spring security chain

- **Which chain.** Chains are tried in `@Order` order; one with a `securityMatcher` only sees its
  paths. The inventory's `chain` column says which one matched an endpoint.
- **Which rule.** Inside a chain the first matching rule wins. A broad `permitAll()` above a
  specific `hasRole()` beats it - read the order, not the set.
- **`method=?` in a rule** means `requestMatchers(someVariable, ...)`, usually a loop over
  `HttpMethod`s. The rule then covers only those methods; read the loop.
- **Normal and not a finding:** `dispatcherTypeMatchers(ASYNC, ERROR).permitAll()` and the matching
  early `return true` for `DispatcherType.ASYNC` in a `HandlerInterceptor`, `/error` permitted,
  `health`/`info` public, CSRF off on a `STATELESS` bearer-token chain.
- **The auth filter.** Open the `OncePerRequestFilter` that reads the token. What happens on a
  missing or invalid token - 401, or the chain continues unauthenticated? Is the signature checked,
  `exp`, issuer and audience? Which paths does `shouldNotFilter` skip? A filter that asks another
  service instead of validating a JWT: "Opaque token" in `references/authorization.md`.
- **CSRF off plus a cookie** - session, `formLogin`, `oauth2Login`, a refresh-token cookie, a BFF -
  is critical. Look at the frontend: `withCredentials`, cookie names, the XSRF config. Spring
  Security 7 has `csrf { spa() }` for exactly this case.
- **Method security.** `@PreAuthorize` without `@EnableMethodSecurity` is dead code. On a Kotlin
  class without the all-open plugin it is dead too. The scanner flags both.

## What only a reader sees

Do these on every run. They are where the real holes are, and no regex finds them.

1. **Object-level access (IDOR).** Up to eight endpoints from the `object` list of `--show authz`,
   writes first; `references/authorization.md` says what decides it. A finding names the endpoint
   and the missing check.
2. **Tenant isolation.** When the digest has a `tenant:` line, work through "Tenant and isolation"
   in `references/authorization.md` and sample three repositories, including one native `@Query`.
3. **Login and tokens.** Rate limiting or lockout on login, token lifetime, refresh handling,
   logout that invalidates, reset tokens that are random, single-use and expire, error messages
   that do not tell a known user from an unknown one.
4. **Webhooks and callbacks.** Signature verified before the body is parsed, replay window,
   idempotency. `SB-AUTHZ-PUBLIC-WRITE` on a webhook path is expected - the signature is the check.
5. **Uploads.** `spring.servlet.multipart.max-file-size`, content type checked against content,
   storage path not built from the client's file name, downloads served with
   `Content-Disposition: attachment` and a fixed content type.
6. **Frontend and backend agree.** Every guarded Angular route has a backend path with a matching
   rule - a guard is UX, the backend is the check. The token travels the way both sides expect
   (interceptor, cookie). CORS origins on the backend are the real frontend host. The CSP comes
   from somewhere: `index.html`, the nginx config, `security.autoCsp`.
7. **Secrets.** One line of the `secrets` block is one value, however many tools found it. For
   each: tracked, untracked, or ignored but packaged (`SB-RESOURCE-UNTRACKED`, `SB-ARTIFACT-CONFIG` in a built jar), prod-like profile or
   local, used anywhere, and does gitleaks see it in history. Once committed it is leaked - after the
   fix commit too. For a JWT the note shows alg, iss, aud, exp and whether the signature looks
   fake; a fake-looking one in a fixture is noise, a real-looking one from a real issuer is the
   finding. Read the file through `--cat` only.
8. **Limits strangers can use up.** Sign-up slots, invitation codes, trial quotas, mail sends: the
   limit is keyed per caller or per object, counted after the validation, and no global quota on a
   public path lets one stranger exhaust it for everyone.
9. **Changed security code.** Every file of the `changes` line: what did it protect before, and
   where did that go? A deleted filter, a removed CORS origin or a loosened matcher fires no check.

On a big codebase take the sample from the writes and from the personal or financial data, and
write the sample size into "Not checked".

## False positives by check family

| check | usually harmless when | a finding when |
|---|---|---|
| `SB-SQL-CONCAT` | the value is a constant, an enum, or an allow-listed sort column | a request param, path variable or DTO field reaches the string |
| `SB-CFG-SECRET` | dev-only profile, value overwritten by the environment in every deployment (check compose, Dockerfile, k8s) | the default profile ships it, or it is a real key |
| `REPO-SECRET-TOKEN` (JWT) | a fixture in a test or a mock server, expired, signed with a test key | it validates against a real issuer |
| `TOOL-GITLEAKS` | the same fixture as above | anything in a prod config, or a real key in history |
| `SB-AUTHZ-PUBLIC-WRITE` | login, register, webhook, token-link pages | anything that changes data of someone else |
| `SB-HEADER-TRUST` | a gateway removes the client's header and sets its own, and the service has no other way in | the port is reachable directly, or the gateway passes client headers through |
| `HTTP-X-PREFIX` | a platform or a partner dictates the name, or existing clients already send it | a header the app introduces now |
| `SB-AUTHZ-INCONSISTENT` | the URL rule already demands the stronger role | the URL rule is only `authenticated` |
| `SB-NO-VALID` | the DTO has no constraints by design and the service validates | constraints exist but never run |
| `SB-EAGER` | a small lookup entity, never loaded in a list | an entity that shows up in a paged list |
| `SB-EVENT-ORPHAN` | the listener lives in another service (Kafka, Modulith externalized) | one side was deleted |
| `NG-ROUTE-UNGUARDED` | public by design, often a `:token` path | the backend behind it trusts the UI |
| `NG-INTERCEPTOR-BYPASS` | SSE, a health check, a public file | the call needs the token, tenant or error handling the interceptor adds |
| `NG-SUBSCRIBE-LEAK` | the component lives as long as the app | it is created per navigation |
| `NG-COMPONENT-SIZE` | static content - legal pages, a showcase | logic, state and template grew together |
| `KC-NO-AUDIENCE` | the converter only accepts roles from `resource_access.<this client>` and every endpoint needs one | `authenticated()` endpoints exist |
| `KC-MUTABLE-USER-KEY` | display name, log line | ownership is stored or looked up by it |
| `NG-TOKEN-ALL-HOSTS` | the app only ever calls its own API | any third-party URL in a service or `httpResource` |
| `DEPS-FLOOR` marked `verify` | the advisory does not cover the used feature | confirmed by npm audit, osv-scanner or the advisory page |
| `SB-TENANT-CONTEXT-LOST` | the job loops over tenants and sets the context itself, or reads no tenant data | tenant tables are read on the pool thread |
| `SB-CACHE-NO-TENANT` | global reference data: holidays, countries, feature flags | the cached value comes from a tenant table |
| `SB-TENANT-NATIVE-SQL` | a join to a tenant-scoped parent filters it, or an operator report across tenants | it answers a tenant's request |
| `DB-TENANT-NO-RLS` | outbox, audit or operator tables read across tenants on purpose | tenant requests read the table |
| `DB-TENANT-CONSTRAINT` | the value is global by nature: a slug in a URL, an external id | a business key like an invoice number |
| `SB-AUTHZ-FAIL-OPEN` (`?: true`) | a config default next to the decision | the default answers "may this caller" |
| `SB-TOKEN-RELAY` | every target checks its own audience | the target accepts any token of the realm |
| `KC-ORG-FIRST` | the client requests the plain `organization` scope | `organization:*` in the frontend or the realm |
| `SB-HOST-HEADER-LINK` | the link base comes from config, or the proxy sets a fixed `Host` | the proxy passes the client's `Host` or `X-Forwarded-Host` |
| `SB-GET-SIDE-EFFECT` | the write is an audit row or a last-seen timestamp | the GET consumes a token, confirms or deletes |
| `AUTH-NO-RATELIMIT` | the gateway or ingress limits the path (check its config) | nothing in front of the app limits it |
| `PUBLIC-MAIL-TO-INPUT` | the recipient is the logged-in user or a fixed address | any address from the body gets the mail |
| `SB-RESOURCE-UNTRACKED` | the build excludes the file (`processResources`, a profile filter) | the jar on disk contains it |
| `NG-TOKEN-HOST-PREFIX` | the base ends with `/` or the code compares `new URL(url).origin` | the base is a bare host |
| `NG-TOKEN-IN-PATH` | capability links of a public API by design - they still end up in access logs | a session, refresh or reset token in the path |
| `NG-IFRAME-WRITE` | the written HTML is a fixed template without user data | user or backend content reaches it with `allow-scripts` |
| `DEPS-UNUSED` | a CLI or script outside the repo uses it, or a config the scanner did not read | nothing references it - one less package to patch |

## Beyond security

The design passes have their own references: `references/architecture.md` for calls, module cut,
Nx libs and reuse, `references/quality.md` for database design, test gaps and usability,
`references/privacy.md` for personal data and the privacy profile, `references/keycloak.md`
whenever the digest has a `keycloak` line, `references/authorization.md` for the `authz` line.
