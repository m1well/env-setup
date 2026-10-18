# Database design, test gaps, usability

## Database design - `DB-*`, `--show entities`

- Sketch the aggregates from `--show entities`: cascade and `orphanRemoval` only from an owner to
  its parts; across aggregates and modules a reference by id, not an association.
- Mandatory `@ManyToOne`: `optional = false` and `NOT NULL` in the migration agree.
- Bidirectional relations: is the collection side used at all, or does it only load rows?
- Delete semantics: `ON DELETE` in the migration and JPA cascade say the same. Personal data and
  its erasure path belong to the privacy pass (`references/privacy.md`).
- Tenant column on every tenant-owned table, inside every unique constraint, with an index.
- Money is `numeric(p, s)` plus a currency; enums are strings with a check constraint.
- Usually harmless: `DB-FK-NO-INDEX` on a small lookup table, `DB-NO-VERSION` on append-only rows,
  `DB-NO-UNIQUE-KEY` when a partial or expression index the parser missed covers it.

## Correctness - `SB-DST-DURATION`, `SEED-INSERT-ONLY`, `DB-NATIVE-COUNTER-OVERWRITE`, `SB-LIMIT-UNUSED`

- `SB-DST-DURATION`: a duration between two `LocalDateTime`s in a non-UTC zone is an hour off across a
  switch; the note names the zone, where it comes from and the next switch. `Instant` or
  `ZonedDateTime` fixes it. It is the concrete case behind an aggregated `DB-TIMESTAMP-NO-TZ`.
- `SEED-INSERT-ONLY`: a correction in the seed code never reaches the database, and a deleted row
  comes back on the next start. On personal data that defeats erasure. One finding per `entity`;
  the fix is an upsert or a repeatable migration.
- `DB-NATIVE-COUNTER-OVERWRITE`: a native or JPQL bulk update skips `@Version`; the next flush of an
  entity loaded before writes the old value back. `@Column(updatable = false)` on the counter, or
  the statement bumps the version too.
- `SB-LIMIT-UNUSED`: a `*_MAX` nobody reads is usually a validation someone forgot.
- **Shutdown against job duration.** `spring.lifecycle.timeout-per-shutdown-phase` shorter than the
  longest job's time limit or `join(...)` means a deploy kills the job halfway. Is the job
  idempotent and does it resume?

## Test gaps - `TESTGAP-*`

- The scanner matches paths, handlers and service methods in test code. A name match, not
  coverage: confirm the top five by opening the test that seems to cover a neighbour.
- Rank by what breaks for the business: money, deletion and GDPR, permissions, state transitions,
  imports, scheduled jobs. A list of 60 untested endpoints is one finding; the five that matter are
  its detail.
- For each name the behaviour and the missing negative case (TEST-4): rejected input, foreign
  tenant, missing entity, wrong role.
- A coverage report under `build/reports` (Kover, JaCoCo) or `coverage/` beats the name match - use
  it when it is there, never run the build for it.
- Frontend: state services and validation first; e2e covers create, edit and delete of each main
  object once. `TESTGAP-E2E-ROUTE` counts per app - an app with no e2e route at all is the finding,
  not the workspace ratio.

## Usability - `UX-*`

The users are not technical. The bar: someone using the app for the first time finishes the task
without asking. Open three to five pages with forms and every delete the scanner lists.

- **Next step.** One primary action per view, named after what it does ("Rechnung speichern", not
  "OK"); after saving a visible confirmation and the obvious way on.
- **Save button.** Visible without scrolling on long forms (sticky action bar); disabled with a
  reason, never silently.
- **Delete.** Every delete or irreversible action asks first, names the object and the consequence,
  and the destructive button looks destructive. Removing an unsaved row from a form is the one
  case where an undo is enough.
- **Hardened forms.** Required fields marked; email, IBAN, PLZ, dates and amounts validated in the
  form; messages say how to fix it ("Fünf Ziffern, etwa 80331"), not "ungültig".
- **Hints.** Every field a layperson could misread gets a hint: abbreviations, tax and accounting
  terms, what happens with the data.
- **States.** Every list from the backend shows loading, empty and error; backend errors appear in
  plain language next to the field, never as a status code.
- Usually harmless: `UX-FORM-NO-VALIDATION` on a search or filter form, `UX-INPUT-NO-LABEL` on a
  table cell input - which still needs an `aria-label`.
