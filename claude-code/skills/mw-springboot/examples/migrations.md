# Section 6 - Migrations

Flyway and Liquibase side by side. **Pick the one the project already has** - the
`spring-boot-starter` for both on one classpath is a configuration accident, not a
choice. Everything in this file applies to both unless it says otherwise.

The running example: the `customers` table gets the columns of `PersonEmbeddable` from
`examples/entities.md`.

## MIG-1 - The schema comes from migrations, not from Hibernate

```yaml
# wrong - the schema is a side effect of whatever entity model was deployed last
spring:
  jpa:
    hibernate:
      ddl-auto: update

# right - Hibernate checks, the migration tool changes
spring:
  jpa:
    hibernate:
      ddl-auto: validate
```

**Flyway**

```yaml
spring:
  flyway:
    enabled: true
    locations: classpath:db/migration
    baseline-on-migrate: false     # true only once, when adopting Flyway on an existing database
```

```
src/main/resources/db/migration/
├── V20260901_1000__create_customers.sql
├── V20260907_1030__add_person_columns_to_customers.sql
└── R__customer_overview_view.sql        # repeatable: re-runs whenever its checksum changes
```

**Liquibase**

```yaml
spring:
  liquibase:
    enabled: true
    change-log: classpath:db/changelog/db.changelog-master.yaml
    contexts: ${LIQUIBASE_CONTEXTS:prod}
```

```
src/main/resources/db/changelog/
├── db.changelog-master.yaml
└── changes/
    ├── 20260901_1000-create-customers.yaml
    └── 20260907_1030-add-person-columns-to-customers.yaml
```

```yaml
# db.changelog-master.yaml - never edited again after this
databaseChangeLog:
  - includeAll:
      path: changes/
      relativeToChangelogFile: true
```

`includeAll` sorts by filename, which is why MIG-4 matters.

Build wiring, when the CLI tasks are wanted on top of the Boot integration:

| | Gradle | Maven |
| --- | --- | --- |
| Flyway | `id("org.flywaydb.flyway")` + `flyway { url = ... }` | `flyway-maven-plugin` |
| Liquibase | `id("org.liquibase.gradle")` + `liquibase { activities { ... } }` | `liquibase-maven-plugin` |

## MIG-2 - An applied migration is never edited

Both tools store a checksum per applied script. Changing the file means every
environment that already ran it fails on the next startup - and the one that has not run
it yet gets a different schema. **In a review, a diff that modifies an existing
migration file is a blocker.** The fix for a wrong migration is always a new migration.

The escape hatches exist and both are incident tools, not workflow:

```bash
./gradlew flywayRepair          # rewrites the checksum in flyway_schema_history
./mvnw liquibase:clearCheckSums # forgets every checksum, recomputed on next run
```

Liquibase also takes a `validCheckSum` on the changeset, which is the same admission in
a nicer place. If you reach for one of these, the reason belongs in the commit message.

## MIG-3 / MIG-4 - One change per file, named, timestamped

```
V12__changes.sql                              wrong - what changed?
V13__add_column.sql                           wrong - which column, which table?
V20260907_1030__add_person_columns_to_customers.sql   right
```

The counter is the real problem: two branches both write `V13__`, both are green, and
the merge is broken at deploy time. A timestamp cannot collide, and it sorts the way it
happened.

Liquibase changesets carry `id` and `author` instead - the id is unique per file, and
the file name still carries the timestamp because `includeAll` sorts by it.

## The same change, both tools

**Flyway** - `V20260907_1030__add_person_columns_to_customers.sql`:

```sql
alter table customers
    add column first_name varchar(255),
    add column last_name  varchar(255),
    add column birth_date date,
    add column gender     varchar(20);

update customers set gender = 'UNDISCLOSED' where gender is null;

alter table customers
    alter column first_name set not null,
    alter column last_name  set not null,
    alter column birth_date set not null,
    alter column gender     set not null;

create index idx_customers_last_name on customers (last_name);
```

**Liquibase** - `changes/20260907_1030-add-person-columns-to-customers.yaml`:

```yaml
databaseChangeLog:
  - changeSet:
      id: 20260907_1030-add-person-columns
      author: m1well
      preConditions:
        - onFail: MARK_RAN
        - not:
            - columnExists: { tableName: customers, columnName: last_name }
      changes:
        - addColumn:
            tableName: customers
            columns:
              - column: { name: first_name, type: varchar(255) }
              - column: { name: last_name,  type: varchar(255) }
              - column: { name: birth_date, type: date }
              - column: { name: gender,     type: varchar(20), defaultValue: UNDISCLOSED }
        - addNotNullConstraint: { tableName: customers, columnName: gender, columnDataType: varchar(20) }
        - createIndex:
            tableName: customers
            indexName: idx_customers_last_name
            columns:
              - column: { name: last_name }
      rollback:
        - dropIndex: { tableName: customers, indexName: idx_customers_last_name }
        - dropColumn:
            tableName: customers
            columns:
              - column: { name: first_name }
              - column: { name: last_name }
              - column: { name: birth_date }
              - column: { name: gender }
```

Note what the embeddable did to this migration: four columns in one table today, and
`MODEL-5` means the same rename later touches every table that embeds it. That is the
cost side of MODEL-2, and it is worth knowing before the second embedding.

Liquibase also speaks SQL when the YAML gets in the way - same rules, same file naming:

```sql
--liquibase formatted sql
--changeset m1well:20260907_1030-add-person-columns
alter table customers add column first_name varchar(255);
--rollback alter table customers drop column first_name;
```

## MIG-5 - Answer the rollback question on purpose

- **Liquibase** generates a rollback for the simple changes and takes an explicit
  `rollback:` block for the rest. Write it for anything destructive - a `dropColumn`
  without one is a one-way door.
- **Flyway** undo scripts (`U__`) are a paid feature. In the community edition the honest
  answer is: there is no rollback, only a forward fix. That changes how the migration is
  written - additive first, destructive later, never both in one release (MIG-6).

Either way, the rollback that actually happens in production is usually a restored
backup plus a forward fix. Write migrations so that is survivable: no `drop` of anything
still holding data the old release needs.

## MIG-6 - Expand and contract

Renaming `zip` to `postal_code` in one migration means the old pod and the new pod cannot
both be right during the rollout. Three releases instead:

| Release | Migration | Code |
| --- | --- | --- |
| 1 - expand | `add column postal_code`, backfill from `zip`, trigger or dual write | writes both, reads `zip` |
| 2 - switch | none | writes both, reads `postal_code` |
| 3 - contract | `drop column zip` | reads and writes `postal_code` only |

The same shape covers a type change, a table split, and a not-null constraint on an
existing column: add nullable, backfill, then constrain - never in the deploy that also
starts writing it.

The tell in a review: one migration that renames or drops a column that the currently
deployed release still reads. That is not a style question, that is a failed rollout.

## MIG-7 - No long locks

`CREATE INDEX` locks the table against writes for as long as it takes. On Postgres the
concurrent variant does not, but it cannot run inside a transaction - and both tools wrap
migrations in one by default.

**Flyway** - a script config file next to the script, `V..._add_index.sql.conf`:

```properties
executeInTransaction=false
```

**Liquibase** - on the changeset:

```yaml
  - changeSet:
      id: 20260907_1100-index-orders-customer
      author: m1well
      runInTransaction: false
      changes:
        - sql:
            sql: create index concurrently idx_orders_customer on orders (customer_id)
```

Same class of problem, same answer: `alter table ... set not null` on a big table, adding
a column with a volatile default, a backfill `update` over millions of rows. Batch the
backfill in its own migration and keep the DDL short.

## MIG-8 - Seed data is not schema

```yaml
# Liquibase: contexts keep it out of production
  - changeSet:
      id: 20260907_1200-demo-customers
      author: m1well
      context: dev or test
      changes:
        - insert: { tableName: customers, columns: [ ... ] }
```

```yaml
# Flyway: a second location, only active in the profiles that want it
spring:
  flyway:
    locations: classpath:db/migration,classpath:db/testdata   # dev/test profile only
```

Reference data that production genuinely needs - country codes, tax rates - is a normal
migration. A demo user is not, and it will end up in production exactly once.

## MIG-9 / MIG-10 - Test the migrations, then let Hibernate check them

`create-drop` in tests plus Flyway in production means the tests validate a schema that
exists nowhere. Run the real thing:

```kotlin
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Import(ContainerConfig::class)
class MigrationTest(@Autowired val jdbc: JdbcClient) {

    @Test
    fun `migrations bring the schema to the expected shape`() {
        val columns = jdbc.sql(
            """
            select column_name from information_schema.columns
            where table_name = 'customers'
            """
        ).query(String::class.java).list()

        assertThat(columns).contains("first_name", "last_name", "birth_date", "gender")
    }
}
```

```yaml
# src/test/resources/application.yml
spring:
  jpa:
    hibernate:
      ddl-auto: validate     # the free check that entities and migrated schema agree
  flyway:
    enabled: true
```

That combination is the point of writing both: the migration builds the schema, and
`validate` fails the build the moment an entity and the schema drift apart - which is
exactly the bug that otherwise surfaces at the first production request.

For a database that already has data shapes worth keeping, the stronger test restores a
sanitized dump into the container before running the migration. Slow, so it belongs in a
nightly job, not in `check`.
