# Section 9 - Operations

## OPS-1 - SLF4J, nothing else

`System.out.println` and `printStackTrace` bypass every appender, level, format and
correlation id. In a container they land on stdout without a timestamp and without the
trace id, which is exactly when you need one.

**Java**

```java
public class OrderService {
    private static final Logger log = LoggerFactory.getLogger(OrderService.class);
}
```

**Kotlin** - either form, one per project:

```kotlin
class OrderService {
    private val log = LoggerFactory.getLogger(javaClass)
}

// or, with kotlin-logging on the classpath
private val log = KotlinLogging.logger {}
```

Catch it in the pre-commit hook rather than in the next review:

```bash
grep -rn -E 'System\.out\.print|printStackTrace\(\)' src/main --include='*.java' --include='*.kt'
```

## OPS-2 - Levels mean something, and log once

```kotlin
// wrong - logged here, rethrown, logged again by the advice. Two stack traces, one problem
try {
    paymentClient.charge(order)
} catch (ex: PaymentException) {
    log.error("Payment failed", ex)
    throw ex
}

// wrong - the level is a lie. A rejected input is not an error, it is Tuesday
catch (ex: ValidationException) {
    log.error("Invalid order", ex)
}

// wrong, and the worst of the three - the exception is gone
catch (ex: PaymentException) {
    // ignored
}

// right - handle and log, or rethrow and let the handler log. Not both
catch (ex: PaymentException) {
    log.warn("Payment declined for order {}, falling back to invoice", order.id, ex)
    order.markForInvoice()
}
```

The scale: `error` means someone gets paged, `warn` means degraded but running, `info`
means a business event worth reading in production, `debug` means for a developer.
`log.error` on an expected outcome trains everyone to ignore errors.

## OPS-3 - Probes and shutdown

```yaml
management:
  endpoint:
    health:
      probes:
        enabled: true          # /actuator/health/liveness and /readiness
  health:
    livenessstate:
      enabled: true
    readinessstate:
      enabled: true

server:
  shutdown: graceful

spring:
  lifecycle:
    timeout-per-shutdown-phase: 30s
```

Without graceful shutdown a rolling deploy kills in-flight requests and half-processed
messages. With it, the container stops accepting new work and finishes what it has.

In Kubernetes the two probes point at the two endpoints - liveness restarts the pod,
readiness takes it out of the load balancer. Pointing both at `/actuator/health` means
a temporarily unavailable dependency restarts your pod in a loop.

## OPS-4 - Timeouts, bounded retries, a breaker where it counts

```kotlin
// wrong - no timeout, and a retry that hammers a dependency that is already down
@Retryable(maxAttempts = 10)
fun charge(order: Order): Receipt = restClient.post()...

// right - bounded, backed off, and it gives up into a fallback
@Retryable(
    retryFor = [ResourceAccessException::class],
    maxAttempts = 3,
    backoff = Backoff(delay = 200, multiplier = 2.0),
)
@CircuitBreaker(name = "payment", fallbackMethod = "chargeFallback")
fun charge(order: Order): Receipt = restClient.post()...

private fun chargeFallback(order: Order, ex: Exception): Receipt {
    log.warn("Payment provider unavailable, queueing order {}", order.id, ex)
    return Receipt.pending(order.id)
}
```

```yaml
resilience4j:
  circuitbreaker:
    instances:
      payment:
        slidingWindowSize: 20
        failureRateThreshold: 50
        waitDurationInOpenState: 30s
```

Retrying a non-idempotent POST without an idempotency key is its own finding - it turns
one timeout into two charges.

## OPS-5 - Configuration, not constants

```kotlin
// wrong
private val baseUrl = "https://payments.internal:8443"
private val timeout = 30_000L
if (order.total > BigDecimal("10000")) requireApproval(order)

// right - environment-dependent values in properties, business thresholds named
@ConfigurationProperties(prefix = "orders")
data class OrderProperties(
    val approvalThreshold: BigDecimal,
    val payment: PaymentProperties,
)
```

The test is not "is it a string" but "would this differ between staging and
production, or would a business person want to change it". Both answers mean
configuration.

## OPS-6 - Make an error traceable

```kotlin
// wrong - which order? which customer? the log line is unusable
log.error("Could not save", ex)

// right - identifiers in the message, exception as the last argument
log.error("Could not save order {} for customer {}", order.id, order.customer, ex)
```

With `spring-boot-starter-actuator` plus Micrometer Tracing the trace id is in the MDC
already - the pattern only has to print it:

```yaml
logging:
  pattern:
    level: "%5p [${spring.application.name:},%X{traceId:-},%X{spanId:-}]"
```

Or drop the pattern and emit structured logs, which is what a log aggregator wants
anyway:

```yaml
logging:
  structured:
    format:
      console: ecs        # Spring Boot 3.4+, also: logstash, gelf
```
