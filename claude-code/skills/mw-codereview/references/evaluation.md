# Evaluating the scan

## Reading a Spring security chain

- **Which chain.** Chains are tried in `@Order` order; one with a `securityMatcher` only sees its
  paths. The inventory's `chain` column says which one matched an endpoint.
- **Which rule.** Inside a chain the first matching rule wins. A broad `permitAll()` above a
  specific `hasRole()` beats it - read the order, not the set.
- **`method=?` in a rule** means `requestMatchers(someVariable, ...)`, usually a loop over
  `HttpMethod`s. The rule then covers only those methods; read the loop.
- **Normal and not a finding:** `dispatcherTypeMatchers(ASYNC, ERROR).permitAll()`, `/error`
  permitted, `health`/`info` public, CSRF off on a `STATELESS` bearer-token chain.
- **The auth filter.** Open the `OncePerRequestFilter` that reads the token. What happens on a
  missing or invalid token - 401, or the chain continues unauthenticated? Is the signature checked,
  `exp`, issuer and audience? Which paths does `shouldNotFilter` skip?
- **CSRF off plus a cookie** - session, `formLogin`, `oauth2Login`, a refresh-token cookie, a BFF -
  is critical. Look at the frontend: `withCredentials`, cookie names, the XSRF config. Spring
  Security 7 has `csrf { spa() }` for exactly this case.
- **Method security.** `@PreAuthorize` without `@EnableMethodSecurity` is dead code. On a Kotlin
  class without the all-open plugin it is dead too. The scanner flags both.

## What only a reader sees

Do these on every run. They are where the real holes are, and no regex finds them.

1. **Object-level access (IDOR).** Take up to eight endpoints with a path id (`{id}`, `{uniqueId}`)
   behind `authenticated` or a role rule, writes first. Open the service method: is the object
   loaded for *this caller* - `findByIdAndOwnerId`, a tenant filter, an explicit membership check?
   A role check is not an ownership check. A finding names the endpoint and the missing check.
2. **Tenant isolation.** If the code has a tenant (`tenant`, `mandant`, `organisation`): is every
   query constrained - `@TenantId`, a Hibernate filter, a parameter on every repository method?
   Sample three repositories, including one native `@Query`.
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
7. **Secrets.** For each one: tracked or only on disk, prod-like profile or local, used anywhere,
   and does gitleaks see it in history. Once committed it is leaked - after the fix commit too.

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

## Beyond security

The design passes have their own references: `references/architecture.md` for calls, module cut,
Nx libs and reuse, `references/quality.md` for database design, test gaps and usability,
`references/privacy.md` for personal data and the privacy profile, `references/keycloak.md`
whenever the digest has a `keycloak` line.
