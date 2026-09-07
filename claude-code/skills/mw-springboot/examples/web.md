# Section 3 - Web layer

## WEB-1 - Entities never cross the HTTP boundary

The entity is the database's shape. Publishing it means every column rename is an API
break, lazy associations serialize into surprise queries or `LazyInitializationException`,
and `password` or `internalNote` ships the day someone adds the field.

**Wrong (Java)** - and this is exactly the shape most tutorials show:

```java
@GetMapping
public List<Order> search(@RequestParam String customer) {
    return service.search(customer);
}
```

**Right (Java)** - DTO in, DTO out, mapping in one place:

```java
public record OrderResponse(Long id, String customer, BigDecimal total, OrderStatus status) {

    static OrderResponse of(Order order) {
        return new OrderResponse(order.getId(), order.getCustomer(), order.getTotal(), order.getStatus());
    }
}

@GetMapping
public List<OrderResponse> search(@RequestParam String customer) {
    return service.search(customer);
}
```

**Right (Kotlin)**

```kotlin
data class OrderResponse(
    val id: Long,
    val customer: String,
    val total: BigDecimal,
    val status: OrderStatus,
) {
    companion object {
        fun of(order: Order) = OrderResponse(order.id, order.customer, order.total, order.status)
    }
}
```

"The fields are identical, why duplicate them" is the argument that ends with an API
contract nobody can change. The duplication is the boundary.

## WEB-2 - Validate every mutating request

Two halves, and one without the other does nothing: constraints on the DTO, `@Valid` on
the parameter.

**Wrong** - constraints present, `@Valid` missing. Everything passes:

```kotlin
@PostMapping
fun create(@RequestBody request: OrderRequest): OrderResponse = service.place(request)
```

**Right (Kotlin)**

```kotlin
data class OrderRequest(
    @field:NotBlank val customer: String,
    @field:Size(min = 1, max = 100) val items: List<@Valid OrderItemRequest>,
    @field:Future val deliverAfter: Instant?,
)

data class OrderItemRequest(
    @field:NotBlank val sku: String,
    @field:Positive val quantity: Int,
)

@PostMapping
@ResponseStatus(HttpStatus.CREATED)
fun create(@Valid @RequestBody request: OrderRequest): OrderResponse = service.place(request)
```

Two details that are easy to miss in a review:

- Kotlin needs `@field:` on a constructor property, otherwise the annotation lands on
  the constructor parameter and Hibernate Validator never sees it
- nested elements need `@Valid` on the type argument (`List<@Valid OrderItemRequest>`),
  in Kotlin and in Java alike - `@Valid` on the list only validates the list

**Right (Java)**

```java
public record OrderRequest(
    @NotBlank String customer,
    @Size(min = 1, max = 100) List<@Valid OrderItemRequest> items,
    @Future Instant deliverAfter
) {}
```

## WEB-3 - One advice, ProblemDetail out

**Wrong** - the message goes out raw, so the client gets an SQL constraint name, and
every controller invents its own error shape:

```java
@ExceptionHandler(Exception.class)
public ResponseEntity<String> handle(Exception ex) {
    return ResponseEntity.status(500).body(ex.getMessage());
}
```

**Right (Kotlin)** - RFC 9457, one place, nothing internal leaking:

```kotlin
@RestControllerAdvice
class ApiExceptionHandler {

    private val log = LoggerFactory.getLogger(javaClass)

    @ExceptionHandler(OrderNotFoundException::class)
    fun handleNotFound(ex: OrderNotFoundException): ProblemDetail =
        ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, "Order ${ex.orderId} does not exist").apply {
            type = URI.create("https://api.example.com/problems/order-not-found")
            title = "Order not found"
        }

    @ExceptionHandler(MethodArgumentNotValidException::class)
    fun handleValidation(ex: MethodArgumentNotValidException): ProblemDetail =
        ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, "Request validation failed").apply {
            title = "Invalid request"
            setProperty("errors", ex.bindingResult.fieldErrors.associate { it.field to it.defaultMessage })
        }

    @ExceptionHandler(Exception::class)
    fun handleUnexpected(ex: Exception): ProblemDetail {
        log.error("Unhandled exception", ex)                       // detail stays in the log
        return ProblemDetail.forStatusAndDetail(HttpStatus.INTERNAL_SERVER_ERROR, "Unexpected error")
    }
}
```

The Java version is the same class with `ProblemDetail.forStatusAndDetail(...)` and
setters instead of `apply`.

Alternative worth knowing: a domain exception can extend `ErrorResponseException` and
carry its own status and problem type, which removes the handler entirely for the
simple cases.

## WEB-4 - Typed responses

```kotlin
fun find(id: Long): ResponseEntity<Any>          // wrong - contract is folklore
fun find(id: Long): Map<String, Any>             // wrong - and it kills the OpenAPI schema
fun find(id: Long): OrderResponse                // right
fun find(id: Long): ResponseEntity<OrderResponse> // right when you need headers or a dynamic status
```

`ResponseEntity` is not the smell - the raw type parameter is. Return the plain type
when the status is static and set it with `@ResponseStatus`.

## WEB-5 - Status codes and Location

```kotlin
// wrong - 200 on create, no Location, 404 assembled by hand in the controller
@PostMapping
fun create(@Valid @RequestBody request: OrderRequest) = service.place(request)

@GetMapping("/{id}")
fun find(@PathVariable id: Long): ResponseEntity<OrderResponse> {
    val order = service.findOrNull(id) ?: return ResponseEntity.notFound().build()
    return ResponseEntity.ok(order)
}

// right
@PostMapping
fun create(@Valid @RequestBody request: OrderRequest): ResponseEntity<OrderResponse> {
    val created = service.place(request)
    return ResponseEntity.created(URI.create("/api/v1/orders/${created.id}")).body(created)
}

@GetMapping("/{id}")
fun find(@PathVariable id: Long): OrderResponse = service.findById(id)   // throws, advice turns it into 404

@DeleteMapping("/{id}")
@ResponseStatus(HttpStatus.NO_CONTENT)
fun delete(@PathVariable id: Long) = service.delete(id)
```

The 404 comes from the domain exception through the advice (WEB-3), so the rule lives
once instead of in every controller method.

## WEB-6 - Paged collections

```kotlin
// wrong - fine on the dev database with 40 rows
@GetMapping
fun all(): List<OrderResponse> = service.findAll()

// right
@GetMapping
fun search(
    @RequestParam(required = false) customer: String?,
    @PageableDefault(size = 20, sort = ["createdAt"], direction = Sort.Direction.DESC) pageable: Pageable,
): Page<OrderResponse> = service.search(customer, pageable)
```

Cap the page size globally so a client cannot ask for 10 000:

```yaml
spring:
  data:
    web:
      pageable:
        max-page-size: 100
        default-page-size: 20
```

## WEB-7 - Versioned paths and a usable contract

```kotlin
@RequestMapping("/orders")          // wrong - no version, so the first breaking change has nowhere to go
@RequestMapping("/api/v1/orders")   // right
```

The version is not there to be incremented eagerly - it is there so that the day a
field has to change type, v2 can exist next to v1 instead of breaking every client at
once. Together with it, the response type has to be concrete (WEB-4), otherwise the
generated OpenAPI schema says `object` and the contract only lives in people's heads.

## WEB-8 - Outbound calls need timeouts

A client without a read timeout waits forever, holds its thread, and turns a slow
dependency into your outage. This is a blocker, not a nice-to-have.

**Right, and the shortest version** - Spring Boot 3.4+ applies these to every client
built from the auto-configured `RestClient.Builder`:

```yaml
spring:
  http:
    client:
      connect-timeout: 2s
      read-timeout: 5s
```

**Right (Kotlin, MVC)** - per client, when one dependency needs its own budget:

```kotlin
@Configuration
class PaymentClientConfig {

    @Bean
    fun paymentRestClient(builder: RestClient.Builder, properties: PaymentProperties): RestClient {
        val factory = SimpleClientHttpRequestFactory().apply {
            setConnectTimeout(Duration.ofSeconds(2))
            setReadTimeout(properties.timeout)
        }
        return builder.baseUrl(properties.baseUrl).requestFactory(factory).build()
    }
}
```

`RestTemplate` in new code is a finding - `RestClient` has been the replacement since
Spring Framework 6.1 and has the same synchronous semantics.

## WEB-9 - WebFlux: nothing blocks

```kotlin
// wrong - one blocking call poisons the event loop for every request on that thread
@GetMapping("/{id}")
fun find(@PathVariable id: Long): OrderResponse =
    orderRepository.findById(id).block()!!

// wrong in Kotlin too - runBlocking on a request thread is the same mistake with nicer syntax
@GetMapping("/{id}")
fun find(@PathVariable id: Long): OrderResponse = runBlocking { service.findById(id) }

// right - stay reactive
@GetMapping("/{id}")
fun find(@PathVariable id: Long): Mono<OrderResponse> = service.findById(id)

// right in Kotlin - suspend all the way down
@GetMapping("/{id}")
suspend fun find(@PathVariable id: Long): OrderResponse = service.findById(id)
```

If something genuinely has to block - a JDBC call, a legacy client - it goes to
`Schedulers.boundedElastic()` or `Dispatchers.IO`, and that is a decision worth a
comment. JPA in a WebFlux application is a design finding, not a line finding.
