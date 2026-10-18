# Architecture and reuse

Most of this ends as recommendations, not findings (see `references/report.md`). A boundary that
leaks data or a call that can lose work is a finding.

## Calls between systems - `--show calls`

- Write each edge as one sentence: who calls whom, sync or async, what the caller does when the
  other side is down or slow. An edge nobody can answer that for is the finding.
- Sync chains (frontend -> A -> B): latency adds up, availability multiplies down. Name the call
  that could be an event or a read model instead.
- Every outbound HTTP call: timeout, retry only for idempotent operations, auth token cached, the
  base URL from configuration (`ARCH-HARDCODED-URL`). A call in a filter or interceptor runs on
  every request (`ARCH-CALL-PER-REQUEST`) - cache it or move it.
- How the caller maps the other side's 4xx and 5xx. A 403 caused by a wrong server secret must not
  reach the user as "code invalid": configuration errors are 5xx and get logged.
- Calls inside a transaction (`SB-TX-REMOTE-CALL`, mails included, up to two bean hops deep, chain in the evidence) or a loop
  (`ARCH-REMOTE-IN-LOOP`). A mail goes out after the commit (`afterCommit`,
  `@TransactionalEventListener`); an event that must not get lost needs an outbox.
- One writer per table. `ARCH-SHARED-DB` and foreign keys into another app's schema: who migrates,
  who may write, what breaks when only one of them deploys.
- `ARCH-API-UNMATCHED`: a typo, a removed endpoint, or a second backend. A frontend that talks to two
  backends needs auth and CORS on both. A frontend-only repo cannot match its calls - name the
  backends it talks to in one line instead.

## Backend modules - `--show modules`

- A good module is one business capability with its own tables, a small API package, few
  dependencies. `classes/tests` per module is in the digest.
- Read the hints together: `ARCH-MODULE-TINY` (merge, or say why it stands alone - a comment in
  `settings.gradle.kts` counts), `ARCH-MODULE-HUGE` (the package groups in the evidence are the
  split), `ARCH-MODULE-SHARED-DOMAIN`, `ARCH-MODULE-FANOUT`, `ARCH-MODULE-LAYERED`.
- `ARCH-ENTITY-SHARED` is a finding: another module works on this module's tables.
- Do not recommend splitting what always changes together. At most three module recommendations,
  each with what gets cheaper afterwards.

## Nx workspace - `--show projects`

- Tags `scope:*` and `type:*` on every project, depConstraints for both (`NX-NO-BOUNDARIES`,
  `NX-NO-TYPE-RULES`).
- Apps are shells (`NX-APP-FAT`); libs per domain, split into feature, ui, data-access, util.
- Shared means two scopes use it (`NX-SHARED-SINGLE-USER`) and it imports no feature
  (`NX-SHARED-UPWARD`).
- Size: many tiny libs (`NX-LIB-TINY`) cost config and build targets; one huge lib (`NX-LIB-HUGE`)
  makes every change "affected".

## Duplication and shared candidates - `DUP-*`, `REUSE-*`

- Open the five largest `DUP-BLOCK` clusters. Same logic: one function. Same markup: one
  component with an input. Name the input or flag that covers the difference.
- `REUSE-SIMILAR`: diff the two files. One or two differing conditions or texts make a shared
  version with a flag; different domains that only look alike stay apart.
- Across separately deployed repositories a shared library costs a release dependency. A copy is
  fine for small stable code - not for security code (token converters, tenant filters, error
  advice), which belongs in one place.
- Tests and generated code are never a reuse finding.
