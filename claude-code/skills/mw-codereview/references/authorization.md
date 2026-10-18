# Authorization model and tenant isolation

Read this in step 3 whenever the digest has an `authz` line. `--show authz` lists the concepts with
their first location, the tenant model, the isolation, the context holders and the endpoints whose
handler never takes the caller. Order of reading: token validation and default deny, then tenant
isolation, then object-level access, then function-level roles, then design.

Keycloak gives identity and coarse rights. Fine-grained decisions and data isolation belong to the
app. A finding where that split is broken names the decision and the place it should live.

## Per concept

- **rbac** - good: one tested converter that keeps `sub` as principal name (`preferred_username`
  there makes every `authentication.name` a mutable key), coarse roles, fine rights as authorities
  (`invoice:read`). Smell: role `if`s in controllers, one role per customer or feature, the same
  string in twenty places. Better: meta-annotations (`@IsAdmin`) or a policy bean.
- **groups** - groups say who belongs where, roles say what they may do. Map groups to roles in
  Keycloak and check roles; path parsing (`split("/")`) in code is a smell.
- **scopes** - describe what a client may do. On user tokens a scope never replaces the role check.
- **abac** - rules in one policy bean with unit tests; attributes from the token or the database,
  never from the body or a header. Plan and entitlements change often - database or cache, not claims.
- **uma** - only for a few coarse resource types, decisions cached, fail-closed, policies in the
  versioned realm export. One resource per row or one Keycloak call per request is the wrong tool.
- **ownership** - the owner and tenant go into the query (`findByIdAndOwnerId`) or are checked before
  the write, on every path: CRUD, bulk, export, search, jobs. Owner from the principal, never the body.
  The count is queries that combine an id with the caller and are reachable from a handler.
- **membership / rebac** - the first location is the table a guard or interceptor checks.
  Membership tables are enough for teams and guilds. OpenFGA or SpiceDB only
  for sharing, delegation or hierarchies, and then with an outbox, not a dual write.

## Tenant and isolation

1. **Source.** The tenant comes from the validated token (claim, Organization, issuer). A header or
   path variable needs a membership check against the token. Multi-org users (`organization:*`) pick
   the tenant per request; with the plain `organization` scope Keycloak makes them choose at login.
   The `organization` claim is a list of aliases or a map keyed by alias - parse both.
2. **Realm per tenant.** Fixed issuer list, JWKS cached. Only for a handful of tenants that need
   their own config; otherwise Organizations (Keycloak 26+, Organization Groups 26.6+).
3. **Enforced centrally.** `@TenantId` (Hibernate 6) or RLS, not a parameter every query has to
   remember. `@Filter` misses load by id unless `applyToLoadByKey` (Hibernate 6.6+).
4. **RLS details.** App role is not the owner (or `FORCE`), migrations run as another role.
   `set_config('app.tenant_id', ?, true)` inside the transaction - set in a filter before
   `@Transactional`, it is gone before the first query. Policies read
   `NULLIF(current_setting('app.tenant_id', true), '')`: a pooled connection returns `''` afterwards.
5. **Platform access.** Support or operator access across tenants has its own role, an audit log
   and ideally a time limit.

## Opaque token or external verify service

A filter that sends the token to another service instead of validating a JWT itself:

- Is `valid`, `active` or the status of the answer evaluated, or does any 200 count?
- Audience, client and source come from the configuration, never from a request header
  (`SB-HEADER-RELAY`).
- Upstream 4xx means 401. Upstream 5xx or a timeout means 503 - never an anonymous request
  (`SB-AUTH-FILTER-SWALLOW`), and never "code invalid" when the server's own secret is wrong.
- A cache keyed by a hash of the token, TTL below the token lifetime. Without one every request
  waits for the call (`ARCH-CALL-PER-REQUEST`).

## Object-level access (IDOR)

Sample from the `object` list of `--show authz`, up to eight, in its order: endpoints that take the
caller but load without it (`[caller]`) first, writes before reads, admin-only (`[admin]`) last. In
a tenant app admin-only endpoints stay in the list - decide whether that admin is a tenant admin or
a platform admin. Open the service: is the row loaded for this caller? A role check is not an ownership check. With RLS or `@TenantId` the
cross-tenant case is covered; ownership inside the tenant is still open. Foreign rows answer 404
when their existence is a secret.

Endpoints `covered by <Interceptor>` in `--show endpoints` leave the list. Open each such
interceptor once: its path patterns, whether it checks the path id against the caller, whether it
lets ASYNC dispatches through.

## Reader checks

- **Two sources for write permission.** A flag in a DTO (`readOnly`, `canEdit`, `writable`) is
  computed from the same predicate the write path enforces, and the URL rule and the service guard
  demand the same roles. Two places answering "may edit" drift apart.
- **Paths that move money.** Changing an IBAN, a payout account or the billing address notifies the
  owner (a mail to the old address). Otherwise a taken-over session redirects payouts silently.

## Expected but missing

Name concepts the project type needs and the code lacks: a SaaS without isolation or without a
cross-tenant test, no difference between tenant admin and platform admin; a game without ownership
on player, guild and inventory objects, without rate limits or idempotent critical actions. Suggest
the simplest concept that covers it - roles plus ownership before a policy engine.
