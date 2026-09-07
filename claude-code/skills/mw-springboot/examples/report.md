# Example report

A real review of a feature branch, in the format of SKILL.md section 12. Section
headings, rule IDs and severity labels stay as they are; the prose follows the language
of the session - German here, because that is how this one ran.

---

**Stack** - Kotlin / Gradle Kotlin DSL / Spring Boot 3.5.6 / Spring MVC / Spring Data JPA + PostgreSQL 17 / Flyway

**Scope** - `git diff HEAD` gegen `main`: 9 Dateien im Modul `order-service` - 3 in
`web/`, 2 in `service/`, `Order.kt`, `OrderRepository.kt`, eine Migration und
`OrderControllerTest.kt`. Nicht angesehen: `shipping-service` (unverändert) und die
generierten OpenAPI-Klassen unter `build/`.

## Findings

### 1 - blocker - `SecurityConfig.kt:34` (SEC-2)

**Rule** - default deny, `anyRequest().authenticated()` am Ende der Chain.

**What happens** - der neue Matcher `authorize("/api/v1/orders/**", permitAll)` steht
vor der `anyRequest`-Regel und deckt auch `POST` und `DELETE` ab. Jeder ohne Token kann
Bestellungen anlegen und löschen. Mit `curl -X DELETE http://localhost:8080/api/v1/orders/1`
reproduzierbar, Antwort 204.

**Fix**

```kotlin
authorize(HttpMethod.GET, "/api/v1/orders/**", hasAuthority("SCOPE_orders:read"))
authorize("/api/v1/orders/**", hasAuthority("SCOPE_orders:write"))
authorize(anyRequest, authenticated)
```

### 2 - blocker - `OrderService.kt:61` (DATA-2)

**Rule** - Self-invocation umgeht den Proxy, die Transaktion existiert nicht.

**What happens** - `place()` ruft `persistWithStock()` in derselben Klasse auf. Die
`@Transactional`-Annotation an `persistWithStock` wirkt nicht, also laufen `orders.save`
und `stock.reserve` in getrennten Transaktionen. Schlägt die Reservierung fehl, bleibt
die Bestellung ohne Reservierung in der Datenbank. Der Test deckt das nicht ab, weil er
`persistWithStock` direkt aufruft.

**Fix** - Annotation an den Einstiegspunkt, innere Methode privat:

```kotlin
@Transactional
fun place(command: PlaceOrder): Order = persistWithStock(command)

private fun persistWithStock(command: PlaceOrder): Order { ... }
```

### 3 - blocker - `V20260812_0900__create_orders.sql:14` (MIG-2)

**Rule** - eine bereits angewandte Migration wird nie geändert.

**What happens** - der Branch ändert die Zeile `status varchar(20)` in `varchar(32)` in
einer Migration, die auf Staging und Produktion längst gelaufen ist. Flyway vergleicht
die Checksumme beim Start: beide Umgebungen fahren beim nächsten Deploy nicht mehr
hoch. Lokal fällt es nicht auf, weil die Datenbank dort frisch aufgebaut wird.

**Fix** - Änderung zurücknehmen, neue Migration daneben:

```sql
-- V20260907_1145__widen_orders_status.sql
alter table orders alter column status type varchar(32);
```

### 4 - major - `Order.kt:38` (MODEL-7)

**Rule** - Enums werden als `@Enumerated(EnumType.STRING)` gespeichert.

**What happens** - `status: OrderStatus` hat keine `@Enumerated`-Annotation, also gilt
der Default `ORDINAL` und die Spalte enthält 0..4. Der Branch fügt `CANCELLED` an
Position 2 ein - ab dem Deploy bedeutet jede bestehende Zeile mit 2, 3 oder 4 etwas
anderes als vorher. Ohne Fehler, ohne Migration, ohne Weg das hinterher zu erkennen.

**Fix** - Annotation setzen, Spalte auf `varchar` migrieren und die vorhandenen Zahlen
in einer Migration in Werte übersetzen, bevor `CANCELLED` eingebaut wird:

```kotlin
@Enumerated(EnumType.STRING)
@Column(name = "status", nullable = false, length = 32)
var status: OrderStatus
```

### 5 - major - `OrderController.kt:52` (WEB-1)

**Rule** - Entities kreuzen die HTTP-Grenze nicht.

**What happens** - `search()` gibt `List<Order>` zurück. Die Entity hat seit der
Migration in diesem Branch ein Feld `internalNote`, das damit im JSON steht. Zusätzlich
serialisiert Jackson die lazy `items`, was pro Bestellung eine Nachladeabfrage auslöst -
bei 20 Treffern 21 Queries (Hibernate-Log geprüft).

**Fix** - `OrderResponse` existiert bereits in `web/dto/`, nur der Rückgabetyp fehlt:

```kotlin
@GetMapping
fun search(@RequestParam customer: String, pageable: Pageable): Page<OrderResponse> =
    service.search(customer, pageable)
```

### 6 - major - `OrderRepository.kt:23` (DATA-5)

**Rule** - `join fetch` zusammen mit `Pageable` paginiert im Speicher.

**What happens** - `findWithItems(customer, pageable)` lädt alle Treffer und schneidet
die Seite in der JVM zu. Im Log steht `HHH90003004: firstResult/maxResults specified
with collection fetch; applying in memory`. Bei aktuell 400 Bestellungen unauffällig,
bei einem Großkunden nicht.

**Fix** - zwei Schritte, IDs paginieren, dann laden:

```kotlin
@Query("select o.id from Order o where o.customer = :customer")
fun findIdsByCustomer(customer: String, pageable: Pageable): Page<Long>

@Query("select distinct o from Order o join fetch o.items where o.id in :ids")
fun findWithItemsByIds(ids: List<Long>): List<Order>
```

### 7 - major - `OrderControllerTest.kt:1` (TEST-1)

**Rule** - der günstigste Slice, der die Sache beweist.

**What happens** - `@SpringBootTest` für einen reinen Controller-Test. Die 6 Tests in
der Klasse brauchen 41 s, mit `@WebMvcTest` wären es unter 4 s. Bei jedem CI-Lauf.

**Fix**

```kotlin
@WebMvcTest(OrderController::class)
class OrderControllerTest(@Autowired val mockMvc: MockMvc) {

    @MockitoBean
    lateinit var service: OrderService
}
```

Der Test für den 403-Fall braucht dann zusätzlich `@Import(SecurityConfig::class)`.

### 8 - minor - `OrderControllerTest.kt:88` (TEST-4)

**Rule** - jedes Verhalten hat auch seinen negativen Fall.

**What happens** - für `POST /api/v1/orders` gibt es nur den 201-Test. Weder die leere
Item-Liste (400) noch der unbekannte Kunde (404) sind abgedeckt - und ein Test auf den
403-Fall hätte Finding 1 vor dem Review gefunden.

**Fix** - zwei Tests, Vorlage in `examples/testing.md`, Abschnitt TEST-4.

## Verified

- `./gradlew :order-service:test` - 34 Tests grün, 41 s davon in `OrderControllerTest`
- `./gradlew :order-service:check` - detekt und ktlint sauber
- Findings 5 und 6 am Hibernate-SQL-Log gegengeprüft (`org.hibernate.SQL=debug`)
- Finding 1 lokal mit curl reproduziert, Finding 3 mit `./gradlew flywayInfo` gegen die
  Staging-Historie geprüft
- Testcontainers-Lauf nicht gestartet (Docker lief nicht) - `OrderRepositoryTest` also
  nur gelesen, nicht ausgeführt

## Footnotes

Außerhalb des Scopes, unverändert, aber im Vorbeigehen aufgefallen:

- `ShipmentService.kt:14` injiziert `OrderService` direkt statt über `OrderApi` (STR-8)
- `application.yml:22` hat `management.endpoints.web.exposure.include: "*"` (SEC-9) -
  je nachdem, ob der Actuator-Port nach außen erreichbar ist, ein eigener Blocker

---

Zuerst Finding 1 - offener Schreibzugriff auf `/api/v1/orders`.
