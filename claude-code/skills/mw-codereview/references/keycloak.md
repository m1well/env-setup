# Keycloak

Read this when the digest has a `keycloak` line. `KC-*` hits are security hits - they go through
step 2 with the rest. `--show keycloak` lists issuers, realm exports, images and the frontend library.

## Resource server

1. **Roles.** Which claim does the `JwtAuthenticationConverter` read? Client roles
   (`resource_access.<client>.roles`) keep the apps of one realm apart; realm roles mean the same in
   every app of the realm. `ROLE_` prefix consistent with `hasRole` vs `hasAuthority`?
2. **Audience.** The backend checks `aud` (`spring.security.oauth2.resourceserver.jwt.audiences`, an
   audience mapper on the frontend client) or `azp` against the expected client. An empty
   `${X:}` fallback is no check in production.
3. **Identity.** Users are keyed by `sub`. `preferred_username` and `email` change; `email_verified`
   decides whether an email may identify anyone.
4. **Tenant.** Several customers in one realm (groups, Organizations, a custom claim): the tenant
   comes from the token and membership is checked - details in `references/authorization.md`. A
   claim fed from a user attribute needs that attribute admin-only (`KC-USER-ATTR-EDITABLE`).
5. **Admin API.** Service account with `view-users`/`manage-users` only, token cached until expiry,
   timeouts on the client, a Keycloak outage does not block the user's own request.
6. **Issuer.** `issuer-uri` is the public hostname (`KC_HOSTNAME`); a backend that fetches the JWKS
   internally still validates that `iss`.
7. **BFF / oauth2Login.** OIDC logout, back-channel logout, refresh token kept server-side only.
8. **Token size.** Every group, role and Organization lands in the token. Past about 8 KB the
   ingress or Tomcat (`server.max-http-request-header-size`) rejects the request.

## Realm

What `KC-REALM-LOCAL` lists is the checklist for the realm that serves real users. Ask where that
realm comes from - an import in another repo, keycloak-config-cli, clicks in the console - and say
in "Not checked" that the production realm was not seen.

- `sslRequired` external or all, brute force detection on, password policy (`length(12)`,
  `notUsername`, `passwordHistory`), OTP or WebAuthn required for admin roles.
- Clients: exact redirect URIs and web origins, standard flow with PKCE S256 for public clients,
  implicit and direct access grants off (a separate e2e client if tests need the password grant),
  `fullScopeAllowed` off, `offline_access` not a default scope.
- Tokens: access token about 5 minutes, refresh token rotation for SPAs, SSO idle and max matching
  how long a user really works in the app.
- Self-registration only when the app is built for it; `verifyEmail` on when email identifies users.
- User profile: attributes behind a protocol mapper are edit `admin` only, `unmanagedAttributePolicy`
  is not `ENABLED`. Authorization Services (`authorizationSettings`) only for a few coarse resources.
- Login and admin events on, with a retention.

## Server

Current major (26.x) in compose, k8s or the Dockerfile. `start`, not `start-dev`, with a real
database and `KC_HOSTNAME`. The admin console not reachable from the internet (`KC_HOSTNAME_ADMIN`
or a proxy rule on `/admin`), `KC_PROXY_HEADERS` matching the proxy, bootstrap admin replaced by a
named admin with MFA.

## Frontend

Standard flow with PKCE, `onLoad: 'check-sso'` with `silent-check-sso.html` served and allowed by
the CSP `frame-src`. Token in memory, never in storage. Refresh before calls (keycloak-angular's
interceptor or `updateToken`), bearer only to the own API (`NG-TOKEN-ALL-HOSTS`), decided by origin and
not by a string prefix (`NG-TOKEN-HOST-PREFIX`). `isTokenExpired()` throws without a token, so it has
no place in the error path of `updateToken` (`KC-JS-EXPIRED-THROWS`). Route guards use the role names
the backend checks (`KC-ROLE-MISMATCH`).
