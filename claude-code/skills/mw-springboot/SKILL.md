---
name: mw-springboot
description: How Spring Boot code is written in my projects - constructor injection and one-way layering, DTOs at the HTTP boundary with ProblemDetail errors, transactions on the service, entities and embeddables as a deliberate model, versioned migrations with Flyway or Liquibase, default-deny security, the cheapest test slice that proves the thing. Language- and build-agnostic - Kotlin or Java, Gradle or Maven. Apply whenever writing, reviewing or refactoring Spring Boot code - a controller, a service, an entity, a query, a migration, a security config or a test - and whenever deciding where a new class belongs. Also invoked via /mw-springboot.
argument-hint: [optional - file, feature, module or "review" plus a scope]
---

# Spring Boot

These are house rules, not a tutorial. Follow them when producing Spring Boot code;
when reviewing, flag every violation with the rule it breaks. Every rule carries an ID
so it can be pointed at in a review, in a commit message, or in an ArchUnit test.

**Baseline is Spring Boot 3.5 or 4.0.** Read the build file before you write. On an
older major say so in one line, then apply the closest thing that version supports
instead of generating code that does not compile - the version-sensitive spots are
marked below.

**Language and build tool do not change the rules.** Everything here holds for Kotlin
and Java, for Gradle and Maven. What differs is how a rule *looks* in code and how you
*run* things - sections 9 and 10. Code that assumes the wrong one of the four is worse
than no code at all.

**Consistency beats these rules in existing code.** If a project already does something
differently across the board, match it and mention the divergence once. Don't convert a
codebase as a side effect of an unrelated task.

## 1. Read the stack before the first line

Four commands, one round trip, and never assume:

```bash
ls -1 pom.xml build.gradle build.gradle.kts settings.gradle settings.gradle.kts 2>/dev/null
find . \( -name '*.kt' -o -name '*.java' \) -not -path '*/build/*' -not -path '*/target/*' | sed 's/.*\.//' | sort -u
grep -rEn 'spring-boot|kotlin.jvm|plugin.spring|plugin.jpa|<java.version>|jvmToolchain|flyway|liquibase' --include='pom.xml' --include='build.gradle*' . | head -30
ls -1 src/main/resources/application*.y*ml src/main/resources/application*.properties src/main/resources/db 2>/dev/null
```

| Fact | Where from | What it decides |
| --- | --- | --- |
| Kotlin, Java or both | file extensions in `src/main` | which shape a rule takes - section 9 |
| Gradle or Maven | `build.gradle(.kts)` vs `pom.xml` | every command you run - section 10 |
| Spring Boot version | build file, `spring-boot-starter-parent` | 3.4 replaced `@MockBean`, 3.5 goes EOL 2026-06-30, 4.0 needs Java 17+ |
| Web stack | `-web` vs `-webflux` | MVC and WebFlux have opposite rules on blocking |
| Persistence | `-data-jpa`, `-data-jdbc`, jOOQ, MyBatis | sections 4 and 5 are JPA-shaped |
| Migration tool | `flyway-core` vs `liquibase-core`, `db/migration` vs `db/changelog` | section 6 - never introduce the second one |
| Kotlin compiler plugins | `plugin.spring`, `plugin.jpa` | missing ones silently break AOP and entities - STR-7, MODEL-3 |
| Modularity | `settings.gradle*` includes, `<modules>`, Spring Modulith | whether module boundaries are a rule or an opinion |

## 2. Structure and wiring

- **STR-1 Constructor injection, always.** No field injection, no setter injection, no
  `@Autowired` on a property. A class that cannot be constructed without a container
  cannot be tested without one either, and a constructor that grows past four
  parameters is the class telling you it does too much. Java: an explicit constructor,
  no `@Autowired` needed when there is only one. Kotlin: the primary constructor is the
  whole thing.
- **STR-2 The stereotype says what the class is.** `@Service` for business logic,
  `@Repository` for data access, `@RestController` for HTTP, `@Configuration` for
  wiring. `@Component` only when none of them fits - it is the "I didn't decide" of
  annotations, and it skips the exception translation `@Repository` brings.
- **STR-3 Dependencies point one way**: controller to service to repository. A
  controller that injects a repository is wrong no matter how small the endpoint, and a
  service that injects a controller is a design accident. Make it mechanical with
  ArchUnit (TEST-7) instead of catching it in reviews forever.
- **STR-4 No circular bean dependencies.** `spring.main.allow-circular-references=true`
  is a finding in itself: it makes the context start again while leaving one of the two
  beans half-initialized when the other uses it. Pull the shared part into a third
  bean, or invert the direction with an application event.
- **STR-5 Configuration is bound type-safe** into a `@ConfigurationProperties` record or
  data class, with `@Validated` and real types - `Duration`, not `long timeoutSeconds`.
  Scattered `@Value` strings turn a typo into a runtime failure at the first request
  instead of a startup failure. `@ConstructorBinding` has not been needed since 3.0.
- **STR-6 Logic lives in the service layer.** Not in the controller, not in an entity
  setter, not in a `@Configuration` class. The controller maps and delegates; that is
  the whole job.
- **STR-7 Kotlin needs the `kotlin-spring` plugin.** Without allOpen every class is
  final, CGLIB cannot proxy it, and `@Transactional`, `@Cacheable`, `@Async`,
  `@Retryable` and `@PreAuthorize` compile, start and silently do nothing. This is the
  most expensive silent failure in this document - grep the build file for it before
  writing the first `@Transactional`.
- **STR-8 Modules talk through their published API.** In a multi-module build or with
  Spring Modulith, reaching into another module's internal service turns two modules
  back into one while the build file still claims otherwise. Use the module's interface,
  or react to its event.

Details and wrong/right pairs: `examples/structure.md`.

## 3. Web layer

- **WEB-1 Entities never cross the HTTP boundary.** Request and response are DTOs - a
  record or data class - even when the fields are identical today. The duplication *is*
  the boundary: without it every column rename breaks the API, lazy associations
  serialize into surprise queries, and the `internalNote` someone adds next month ships
  to every client.
- **WEB-2 Every mutating endpoint validates.** Constraints on the DTO *and* `@Valid` on
  the parameter - one without the other validates nothing. Nested elements need `@Valid`
  on the type argument (`List<@Valid ItemRequest>`), and Kotlin needs `@field:` on
  constructor properties or the annotation never reaches the validator.
- **WEB-3 Errors leave as `ProblemDetail`** (RFC 9457) from one `@RestControllerAdvice`.
  No stack traces, no exception messages, no internal ids in the response - the detail
  goes to the log, the client gets a type, a title and a status.
- **WEB-4 Return types are concrete.** `ResponseEntity<Object>`, `Map<String, Object>`
  and `Any` turn the API contract into folklore and the generated OpenAPI schema into
  `object`.
- **WEB-5 Status and headers are correct**: 201 with `Location` on create, 204 on
  delete, 409 on a version conflict. The 404 comes from the domain exception through the
  advice, not from a null check in the controller.
- **WEB-6 Collections are paged**, with a global `max-page-size`. An unbounded
  `findAll()` behind an endpoint works until the table grows, and then it takes the
  service down.
- **WEB-7 Paths are versioned** (`/api/v1/...`) so the first breaking change has
  somewhere to go.
- **WEB-8 Outbound HTTP has timeouts.** `RestClient` (MVC) or `WebClient` (WebFlux),
  never `RestTemplate` in new code, and never without an explicit connect and read
  timeout - a missing read timeout turns a slow dependency into your outage.
- **WEB-9 WebFlux blocks nowhere**: no `.block()`, no JDBC, no `Thread.sleep`, and in
  Kotlin no `runBlocking` in a request path. If something genuinely has to block it goes
  to `boundedElastic` or `Dispatchers.IO`, and that decision is worth a comment.

Details: `examples/web.md`.

## 4. Persistence: repositories, transactions, queries

- **DATA-1 Transactions belong to the service**, never the controller, never the
  repository - the service is the only layer that knows what has to be atomic. Reads are
  `@Transactional(readOnly = true)`, which is not decoration: Hibernate skips dirty
  checking and the flush.
- **DATA-2 No self-invocation.** A `@Transactional` method called from inside the same
  class never touches the proxy, so the transaction is not there and nothing says so.
  Same trap for `@Cacheable`, `@Async` and `@Retryable`; in Kotlin a `private fun` and a
  non-open class lose it too.
- **DATA-3 Associations are `LAZY`.** `FetchType.EAGER` cannot be turned off at the call
  site; `LAZY` can always be turned on with `@EntityGraph` or `join fetch`.
- **DATA-4 No N+1.** A loop over a lazy association is one query per row. Prove it with
  the fetch type plus the call site and the Hibernate SQL log - "possible performance
  issue" without a call site is an opinion, not a finding.
- **DATA-5 `join fetch` and `Pageable` do not mix** - Hibernate pages in memory and says
  so (`HHH90003004`). Page the ids, then fetch, or use a projection.
- **DATA-6 Queries take parameters**, never string concatenation - in `@Query`, in
  `createQuery`, in a `Specification`, in native SQL. A sort column that comes from a
  request cannot be a parameter, so it goes through an allow-list.
- **DATA-7 Reads that need three columns use a projection**, not the whole entity graph.

Details: `examples/data.md`.

## 5. Persistence: modelling entities and embeddables

This is where a schema is decided, so it is the part that is expensive to change later.

- **MODEL-1 Identity decides entity or embeddable.** Something with its own id, its own
  lifecycle, or that is referenced from elsewhere is an `@Entity`. A group of values
  that only exists as part of its owner - an address, a name, an amount with its
  currency, a date range - is an `@Embeddable`.
- **MODEL-2 Repeating field groups become embeddables.** The second time `street`,
  `zip`, `city`, `country` appear as loose columns on an entity, they are an
  `AddressEmbeddable`. The same for a person's `firstName`, `lastName`, `birthDate`,
  `gender`. The win is not fewer lines - it is that validation, formatting and equality
  live in one place instead of being reimplemented per entity.
- **MODEL-3 Embeddables are immutable value objects**, and here the Kotlin rule inverts:
  a `data class` is exactly right for an `@Embeddable` (equality over all fields is the
  point) and exactly wrong for an `@Entity` (MODEL-4). Java: a `record` works as an
  embeddable since Hibernate 6.2. Change by replacing: `person.moveTo(newAddress)`, not
  `person.address.setCity(...)`.
- **MODEL-4 An entity is never a `data class`** (Kotlin) and never `@Data` (Java
  Lombok). Generated `equals`/`hashCode` cover every field, so the hash changes when the
  id is assigned on flush and the instance is lost inside a `HashSet`; they also touch
  lazy associations, and `copy()` walks straight past every invariant. Equality is on
  the id, `hashCode` is stable for the class.
- **MODEL-5 Embed the same type twice with `@AttributeOverride`**, and name the columns
  explicitly - `billing_street` and `shipping_street`, not two things called `street`
  colliding at startup. The column names of an embeddable are the schema contract: a
  field renamed inside it touches every table that embeds it (MIG-2).
- **MODEL-6 An embedded value where every field is null comes back as `null`.** That is
  Hibernate's default and it hits Kotlin non-nullable properties hard. Decide per
  embeddable: either the columns are `NOT NULL` and the field is non-nullable, or the
  field is declared nullable and the code handles absence.
- **MODEL-7 Enums are `@Enumerated(EnumType.STRING)`.** The default is `ORDINAL`, which
  stores a position - insert a value in the middle of the enum and every existing row
  changes meaning silently. This is the cheapest data corruption in JPA to cause and the
  most expensive to undo.
- **MODEL-8 Lists of value objects are `@ElementCollection`** with an explicit
  `@CollectionTable` and join column - not a separate entity with an artificial id, and
  not a comma-joined string. Know the cost: without an `@OrderColumn` Hibernate deletes
  and reinserts the whole collection on every change, so a large one belongs in its own
  entity after all.
- **MODEL-9 Money is `BigDecimal` plus a currency**, never `double`, and ideally a
  `MoneyEmbeddable` so the two can never drift apart. Time is `Instant` for a moment,
  `LocalDate` for a calendar day; storing a birth date as a timestamp is how it moves a
  day per timezone.
- **MODEL-10 Rows that concurrent requests can write carry a `@Version`.** Optimistic
  locking turns an invisible lost update into a 409 the client can retry.
- **MODEL-11 Entities expose behaviour, not setters.** `order.markAsShipped()` instead
  of `setStatus(SHIPPED)` plus `setShippedAt(now)` at the call site - an invariant that
  lives in the entity cannot be forgotten by the third caller.

Details, with a full `AddressEmbeddable` and `PersonEmbeddable`: `examples/entities.md`.

## 6. Migrations - Flyway or Liquibase, never both

- **MIG-1 The schema comes from versioned migrations**, and `spring.jpa.hibernate.ddl-auto`
  is `validate` or `none` everywhere including tests. `update` means the schema is
  whatever the last deployed entity model happened to be, on every environment
  separately.
- **MIG-2 An applied migration is never edited.** Both tools store a checksum;
  changing a file breaks every environment that already ran it. The fix for a wrong
  migration is always a new migration. In a review: a diff that *modifies* an existing
  migration file is a blocker, no exceptions.
- **MIG-3 One logical change per file or changeset**, with a name that says what it does
  - `V20260907_1030__add_order_status.sql`, not `V12__changes.sql`.
- **MIG-4 Version by timestamp, not by counter.** `V13__` on two branches merges into a
  conflict that only shows up at deploy time; a timestamp cannot collide.
- **MIG-5 Answer the rollback question deliberately.** Liquibase generates or takes a
  `rollback` block - write it for anything destructive. Flyway's `U__` undo scripts are
  a paid feature, so in the community edition the answer is a forward fix, and that
  changes how you write the migration in the first place.
- **MIG-6 Breaking changes go expand-contract**: add the new column, deploy code that
  writes both, backfill, switch reads, drop the old column in a later release. A rename
  in one migration means the old pod and the new pod cannot both be right during the
  rollout.
- **MIG-7 No long locks.** An index on a large table is `CREATE INDEX CONCURRENTLY`,
  which cannot run inside a transaction - Flyway needs `executeInTransaction=false`,
  Liquibase `runInTransaction="false"`. A migration that locks a hot table for a minute
  is an outage with a version number.
- **MIG-8 Seed and test data are not schema migrations.** Separate location, separate
  Liquibase context. Reference data that production needs is a migration; a demo user is
  not.
- **MIG-9 Tests run the real migrations**, against the real engine via Testcontainers.
  `create-drop` in tests plus Flyway in production means the tests validate a schema
  that does not exist anywhere.
- **MIG-10 `ddl-auto: validate` is the free check** that entity model and migrated
  schema still agree - the whole point of writing both.

Both tools, side by side, with the build wiring: `examples/migrations.md`.

## 7. Security and configuration

- **SEC-1 Security is a `SecurityFilterChain` bean.** `WebSecurityConfigurerAdapter` no
  longer exists in Spring Security 6; code referencing it is a leftover from a 5.x
  tutorial. Method security is `@EnableMethodSecurity`.
- **SEC-2 Default deny.** `anyRequest().authenticated()` closes every chain. A broad
  `permitAll()` needs a reason in a comment and never covers a mutating endpoint.
- **SEC-3 `csrf().disable()` only for a genuinely stateless API** - and then the session
  policy has to actually be `STATELESS`. Any cookie-based login and it is a blocker.
- **SEC-4 CORS is central and explicit.** `allowedOrigins("*")` with
  `allowCredentials(true)` fails at runtime, and the `allowedOriginPatterns("*")`
  workaround hands every site on the internet an authenticated request.
- **SEC-5 No secrets in the repository.** Environment variables or a secret store;
  `application-prod` holds placeholders only. A secret that was ever committed counts as
  leaked after the fix commit too - it gets rotated, not deleted.
- **SEC-6 No user input inside a SpEL expression** - `@PreAuthorize` and `@Value`
  evaluate what you hand them. Dynamic rules are a lookup against an allow-list.
- **SEC-7 No untrusted deserialization** (`ObjectInputStream`, Jackson polymorphic
  typing), and XML parsers get `disallow-doctype-decl` before they see foreign input.
- **SEC-8 Logs carry no secrets and no personal data**, and user input reaches them
  through a structured encoder - parameterizing alone does not stop a `\n` from forging
  a log line.
- **SEC-9 Actuator exposes `health`, `info`, `prometheus`** - on its own port where
  possible. `include: "*"` publishes `env`, `configprops` and `heapdump`, which is
  configuration and memory contents.
- **SEC-10 Passwords use BCrypt or Argon2** through a delegating encoder. `NoOp`, MD5
  and plain SHA are blockers whatever the salt.

Details: `examples/security.md`.

## 8. Tests

- **TEST-1 The cheapest slice that proves the thing**: a plain unit test for logic,
  `@WebMvcTest` for a controller, `@DataJpaTest` for a query, `@SpringBootTest` only for
  a path that has to cross the whole app. `@SpringBootTest` on a controller test costs
  seconds per test, forever, in every CI run.
- **TEST-2 `@MockitoBean` / `@MockitoSpyBean`** since Spring Boot 3.4 - `@MockBean` is
  deprecated and gone in 4.0. With MockK it is `@MockkBean` from springmockk.
- **TEST-3 Database tests use Testcontainers with `@ServiceConnection`.** H2 in Postgres
  mode is not Postgres - different json support, different upsert, different locking.
  `@DataJpaTest` additionally needs `@AutoConfigureTestDatabase(replace = NONE)` or it
  swaps in an embedded database and the container just idles.
- **TEST-4 Every behaviour has its negative case**: rejected validation, missing entity,
  forbidden role, stale version. That is where the code is usually wrong.
- **TEST-5 Assertions are on values.** `assertNotNull(result)` proves that something came
  back, which is not a behaviour. `verify(..., never())` is what makes "and nothing else
  happened" a test.
- **TEST-6 No `Thread.sleep`** - Awaitility, or the framework's own event test support.
- **TEST-7 Structural rules are ArchUnit tests**, not review comments. Everything in
  section 2 that can be expressed as a rule should be.
- **TEST-8 Test names state the behaviour** - `rejects an order without items`, not
  `testCreate2`. It is what you read in the CI output at 2am without the code next to
  it.

Details: `examples/testing.md`.

## 9. Operations

- **OPS-1 SLF4J only.** `System.out.println` and `printStackTrace` bypass every
  appender, level, format and trace id.
- **OPS-2 Levels mean something and an error is logged once.** `error` means someone
  gets paged, `warn` means degraded, `info` means a business event. Log-and-rethrow
  produces two stack traces for one problem; an empty catch produces none.
- **OPS-3 Probes and graceful shutdown are configured** where a rolling deploy, a
  scheduler or a queue is involved. Liveness and readiness point at different endpoints -
  pointing both at `/actuator/health` restarts the pod whenever a dependency blips.
- **OPS-4 Every remote call has a timeout**, every retry is bounded and backed off, and
  a retried non-idempotent POST needs an idempotency key or it charges twice.
- **OPS-5 Environment-dependent values are configuration**, not constants. The test is
  "would this differ between staging and production, or would a business person want to
  change it".
- **OPS-6 Errors carry identifiers** - which order, which customer - and the trace id is
  in the log pattern or, better, the logs are structured.

Details: `examples/operations.md`.

## 10. Where the same rule looks different

| Topic | Java | Kotlin |
| --- | --- | --- |
| Injection | explicit constructor, `@Autowired` unnecessary with a single one | primary constructor: `class OrderService(private val repo: OrderRepository)` |
| Field injection tell | `@Autowired private OrderRepository repo;` | `@Autowired lateinit var repo: OrderRepository` |
| DTO | `record OrderRequest(...)` | `data class OrderRequest(...)` |
| Proxying | classes are open by default | needs `kotlin-spring`, otherwise final and un-proxyable (STR-7) |
| Entity | class, `equals`/`hashCode` on the id, no Lombok `@Data` | normal `class`, never `data class`, plus `kotlin-jpa` (MODEL-4) |
| Embeddable | `record`, or a class with final fields | `data class` - the one place it is right (MODEL-3) |
| Validation on a nested list | `List<@Valid Item> items` | `val items: List<@Valid Item>`, and `@field:` on plain constraints |
| Nullability | `Optional` at the boundary, `@Nullable` inside | the type system; every `!!` in production code is a finding |
| Mocking | Mockito, `@MockitoBean` | MockK with springmockk `@MockkBean`, or mockito-kotlin |
| Reactive | Reactor `Mono` / `Flux` | `suspend` functions; `runBlocking` in a request path is a finding |
| Config binding | `record AppProperties(...)` | `data class AppProperties(...)` |

## 11. Commands

Use the wrapper when it exists. Ask before anything that starts a container, touches a
database or runs longer than a couple of minutes.

| Purpose | Gradle | Maven |
| --- | --- | --- |
| Full check | `./gradlew check` | `./mvnw verify` |
| Tests | `./gradlew test` | `./mvnw test` |
| One test | `./gradlew test --tests '*OrderServiceTest'` | `./mvnw test -Dtest=OrderServiceTest` |
| One module | `./gradlew :order-api:test` | `./mvnw -pl order-api test` |
| Run with containers | `./gradlew bootTestRun` | `./mvnw spring-boot:test-run` |
| Dependencies | `./gradlew dependencies` | `./mvnw dependency:tree` |
| Flyway status | `./gradlew flywayInfo` | `./mvnw flyway:info` |
| Liquibase status | `./gradlew status` | `./mvnw liquibase:status` |
| Test report | `build/reports/tests/test/index.html` | `target/surefire-reports/` |
| Coverage | `build/reports/jacoco/test/html/index.html` | `target/site/jacoco/index.html` |

## 12. Reviewing against these rules

When the task is a review rather than writing code, the rules above are the yardstick
and this is the shape of the answer.

**Scope.** `$ARGUMENTS` may name a file, package or module. Empty means the current
change: `git diff HEAD` plus untracked files from `git status --short`; on a clean tree
fall back to the last commit (`git log -1 --no-merges --format=%H`). Read the diff in
its context - the class around the changed method, the caller of a changed signature -
but keep findings inside the scope. A pre-existing problem in an untouched file is a
footnote, not a numbered finding, unless the change makes it worse. Past roughly 40
classes, count first and say what you will leave out.

**Evidence, not suspicion.** N+1 needs the fetch type and the loop. A missing
transaction needs the write path. Run what is cheap (section 11) and say what you ran;
if you did not run anything, say the review is static.

**Not a finding**: anything the formatter, Checkstyle, detekt or ktlint decides; a
different but equivalent way of writing the same thing when the project is consistent
about it; generated code and untouched files; a framework choice that is already made;
missing comments. Three instances of one rule in one file are one finding with the other
locations listed under it.

**Report** straight into the chat. Write a file only when asked, or above roughly ten
findings - then `.claude/reviews/YYYY-MM-DD-<scope-slug>.md`, and say the path. Section
headings, rule IDs and severity labels stay in English so two reviews stay comparable
and greppable; the prose follows the language of the session.

- **Stack** - one line: language, build tool, Spring Boot version, web stack, persistence, migration tool
- **Scope** - what you reviewed, what you left out
- **Findings** - numbered, blockers first. Each: **Where** (`file:line` - a finding
  without a location is not a finding), **Rule** (the ID plus half a sentence), **What
  happens** (the concrete consequence: "every request loads 200 rows to return 20", not
  "possible performance issue"), **Fix** (the code you would write instead, minimal)
- **Verified** - the commands you ran and what came back, or one line saying it was static
- **Footnotes** - out-of-scope observations, one line each. Optional

Severity: **blocker** - wrong in production, do not merge (data loss, security hole, a
transaction that never runs, an edited migration). **major** - works today, will not
later, or breaks a rule that is expensive to unwind (entity on the wire, missing index,
wrong test slice). **minor** - correct but below standard.

Close with the one finding to fix first, and nothing else.

## Examples

Wrong and right for every rule, each in Kotlin **and** Java, with the Gradle and Maven
variants where the build is involved. Read the section's file before writing code of
that shape - what you produce should look like the "right" side in there.

| File | Section | Shows |
| --- | --- | --- |
| `examples/structure.md` | 2 | injection, stereotypes, layering, events instead of cycles, `@ConfigurationProperties`, the Kotlin allOpen trap |
| `examples/web.md` | 3 | DTO boundary, validation, `ProblemDetail` advice, status codes, paging, timeouts, WebFlux |
| `examples/data.md` | 4 | transaction placement and self-invocation, N+1 with the fix, paged fetch joins, parameters, projections |
| `examples/entities.md` | 5 | `AddressEmbeddable` and `PersonEmbeddable` end to end, entity vs embeddable, attribute overrides, enums, element collections, money |
| `examples/migrations.md` | 6 | the same change in Flyway and in Liquibase, expand-contract, concurrent index, migration tests |
| `examples/security.md` | 7 | filter chain, CORS, secrets, SpEL and log injection, actuator, password encoding |
| `examples/testing.md` | 8 | slice per case, `@MockitoBean`, Testcontainers `@ServiceConnection`, MockK next to Mockito, ArchUnit |
| `examples/operations.md` | 9 | logging, probes, timeouts and retries, externalized configuration |
| `examples/report.md` | 12 | a full review report in the format above |

They are reference snippets, not a runnable project. Copy the shape, not the domain.
