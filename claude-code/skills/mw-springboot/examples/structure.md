# Section 2 - Structure and wiring

Same domain in every example file: an `orders` feature with `Order`, `OrderService`,
`OrderRepository` and `OrderController`.

## STR-1 - Constructor injection only

Field injection hides the dependency from the constructor, so the class cannot be
built in a test without a container, and a growing constructor never gets a chance to
tell you the class does too much.

**Wrong (Java)**

```java
@Service
public class OrderService {

    @Autowired
    private OrderRepository repository;

    @Autowired
    private PaymentClient paymentClient;
}
```

**Wrong (Kotlin)** - the same mistake, and it needs `lateinit var` to compile, which
also throws the null safety away:

```kotlin
@Service
class OrderService {

    @Autowired
    lateinit var repository: OrderRepository
}
```

**Right (Java)** - no `@Autowired` needed with a single constructor since Spring 4.3:

```java
@Service
public class OrderService {

    private final OrderRepository repository;
    private final PaymentClient paymentClient;

    public OrderService(OrderRepository repository, PaymentClient paymentClient) {
        this.repository = repository;
        this.paymentClient = paymentClient;
    }
}
```

**Right (Kotlin)** - the primary constructor is the whole thing:

```kotlin
@Service
class OrderService(
    private val repository: OrderRepository,
    private val paymentClient: PaymentClient,
)
```

## STR-2 - The stereotype says what the class is

`@Component` on a service compiles and works. It also tells the next reader nothing,
skips the persistence exception translation that `@Repository` brings, and makes
`@ComponentScan` filters and ArchUnit rules useless.

```kotlin
@Component                       // wrong - it is business logic
class OrderService(...)

@Component                       // wrong - it is data access
interface OrderRepository : JpaRepository<Order, Long>

@Service                         // right
class OrderService(...)

@Repository                      // right - Spring Data adds it implicitly, be explicit on custom impls
class OrderJdbcRepository(private val jdbc: JdbcClient)
```

## STR-3 - One-way dependency direction

Controller to service to repository. Nothing skips a layer, nothing points back.

**Wrong** - the endpoint is small, so the repository goes straight into the controller.
Six months later the same query lives in three controllers with three different
transaction boundaries:

```java
@RestController
@RequestMapping("/api/v1/orders")
public class OrderController {

    private final OrderRepository repository;   // wrong - skips the service layer

    @GetMapping("/{id}")
    public Order find(@PathVariable Long id) {
        return repository.findById(id).orElseThrow();
    }
}
```

**Right** - the service owns the transaction, the exception and the mapping:

```java
@RestController
@RequestMapping("/api/v1/orders")
public class OrderController {

    private final OrderService service;

    @GetMapping("/{id}")
    public OrderResponse find(@PathVariable Long id) {
        return service.findById(id);
    }
}
```

Make the rule mechanical instead of repeating it in reviews - see TEST-7 in
`testing.md` for the ArchUnit version.

## STR-4 - No circular bean dependencies

```yaml
spring:
  main:
    allow-circular-references: true   # a finding on its own
```

The flag makes the context start again; the cycle is still there, and one of the two
beans is now half-initialized at the moment the other uses it. Fix the design: pull the
shared part into a third bean, or invert the direction with an event.

```kotlin
// wrong - OrderService needs InvoiceService, InvoiceService needs OrderService
@Service
class OrderService(private val invoiceService: InvoiceService)

@Service
class InvoiceService(private val orderService: OrderService)

// right - the writer publishes, the reader listens, and neither knows the other
@Service
class OrderService(
    private val repository: OrderRepository,
    private val events: ApplicationEventPublisher,
) {

    @Transactional
    fun place(command: PlaceOrder): Order {
        val order = repository.save(Order.from(command))
        events.publishEvent(OrderPlaced(order.id))
        return order
    }
}

@Service
class InvoiceService {

    @TransactionalEventListener
    fun on(event: OrderPlaced) { ... }
}
```

## STR-5 - Type-safe configuration

**Wrong** - the same prefix spread over four classes, every value a string, no
validation, and a typo shows up at the first request instead of at startup:

```kotlin
@Service
class PaymentClient(
    @Value("\${payment.base-url}") private val baseUrl: String,
    @Value("\${payment.timeout-seconds}") private val timeoutSeconds: Long,
)
```

**Right (Kotlin)**

```kotlin
@ConfigurationProperties(prefix = "payment")
@Validated
data class PaymentProperties(
    @field:NotBlank val baseUrl: String,
    val timeout: Duration = Duration.ofSeconds(2),
)
```

**Right (Java)**

```java
@ConfigurationProperties(prefix = "payment")
@Validated
public record PaymentProperties(@NotBlank String baseUrl, @DefaultValue("2s") Duration timeout) {}
```

Enable it once - `@EnableConfigurationProperties(PaymentProperties::class)` or
`@ConfigurationPropertiesScan` on the application class. `@ConstructorBinding` has not
been needed since Spring Boot 3.0 when there is a single constructor.

Note the type: `Duration` parses `2s` and `500ms` and fails at startup on garbage. A
`Long` named `timeoutSeconds` moves that question to every call site.

## STR-6 - Logic belongs in the service

```kotlin
// wrong - the controller decides business rules
@PostMapping
fun create(@RequestBody request: OrderRequest): OrderResponse {
    if (request.items.isEmpty()) throw IllegalArgumentException("empty")
    val total = request.items.sumOf { it.price * it.quantity.toBigDecimal() }
    if (total > BigDecimal("10000")) throw IllegalStateException("needs approval")
    return service.create(request, total)
}

// right - the controller maps and delegates, the rule lives where it can be unit tested
@PostMapping
@ResponseStatus(HttpStatus.CREATED)
fun create(@Valid @RequestBody request: OrderRequest): OrderResponse =
    service.place(request.toCommand())
```

## STR-7 - Kotlin: the allOpen plugin, or half your annotations do nothing

Kotlin classes are final. Spring's CGLIB proxies subclass the target, so without the
plugin `@Transactional`, `@Cacheable`, `@Async`, `@PreAuthorize` and `@Retryable`
compile, start, and quietly do nothing. This is the single most expensive Kotlin
finding in this catalogue, because nothing fails - the transaction just is not there.

**Gradle Kotlin DSL**

```kotlin
plugins {
    kotlin("jvm") version kotlinVersion
    kotlin("plugin.spring") version kotlinVersion   // allOpen for @Component, @Transactional, ...
    kotlin("plugin.jpa") version kotlinVersion      // no-arg constructor for @Entity/@Embeddable - see MODEL-3
}
```

**Maven**

```xml
<plugin>
  <groupId>org.jetbrains.kotlin</groupId>
  <artifactId>kotlin-maven-plugin</artifactId>
  <configuration>
    <compilerPlugins>
      <plugin>spring</plugin>
      <plugin>jpa</plugin>
    </compilerPlugins>
  </configuration>
</plugin>
```

How to check it in a review: grep the build file. If the plugin is missing and the code
uses `@Transactional` anywhere, that is one blocker for the build file, not one finding
per annotation.

## STR-8 - Modules talk through their API

In a multi-module build or with Spring Modulith, the boundary is the point. Reaching
past it turns two modules back into one, and the build file still claims otherwise.

```kotlin
// wrong - the shipping module injects an internal service of the order module
@Service
class ShipmentService(private val orderService: OrderService)

// right - it uses the published interface of that module
@Service
class ShipmentService(private val orders: OrderApi)

// or, better where it fits, it does not call at all - it reacts
@Service
class ShipmentService {

    @ApplicationModuleListener
    fun on(event: OrderPlaced) { ... }
}
```

With Spring Modulith the rule is enforced, not reviewed:

```kotlin
@Test
fun `modules stay within their boundaries`() {
    ApplicationModules.of(OrderApplication::class.java).verify()
}
```
