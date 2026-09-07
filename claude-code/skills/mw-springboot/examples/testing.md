# Section 8 - Tests

## TEST-1 - The cheapest slice that proves the thing

| What is under test | Slice | Cost per test |
| --- | --- | --- |
| a rule, a calculation, a mapping | plain unit test, no Spring | < 0.1 s |
| a controller: routing, status, validation, serialization | `@WebMvcTest` | ~0.5 s |
| a query, a mapping, a constraint | `@DataJpaTest` + Testcontainers | ~1 s after the container is up |
| a path that has to cross the whole app | `@SpringBootTest` | 5-15 s |

**Wrong** - the whole context booted to check a 400:

```kotlin
@SpringBootTest
@AutoConfigureMockMvc
class OrderControllerTest {

    @Test
    fun `rejects an empty order`() { ... }
}
```

**Right (Kotlin)** - the web slice, the service mocked:

```kotlin
@WebMvcTest(OrderController::class)
class OrderControllerTest(@Autowired val mockMvc: MockMvc) {

    @MockitoBean
    lateinit var service: OrderService

    @Test
    fun `returns 201 and a Location header for a valid order`() {
        given(service.place(any())).willReturn(OrderResponse(42, "ACME", BigDecimal.TEN, OrderStatus.PLACED))

        mockMvc.post("/api/v1/orders") {
            contentType = MediaType.APPLICATION_JSON
            content = """{"customer":"ACME","items":[{"sku":"A-1","quantity":2}]}"""
        }.andExpect {
            status { isCreated() }
            header { string("Location", "/api/v1/orders/42") }
            jsonPath("$.customer") { value("ACME") }
        }
    }

    @Test
    fun `rejects an order without items`() {
        mockMvc.post("/api/v1/orders") {
            contentType = MediaType.APPLICATION_JSON
            content = """{"customer":"ACME","items":[]}"""
        }.andExpect {
            status { isBadRequest() }
            jsonPath("$.title") { value("Invalid request") }
        }

        verify(service, never()).place(any())
    }
}
```

**Right (Java)** - same slice:

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired MockMvc mockMvc;
    @MockitoBean OrderService service;

    @Test
    void returnsCreatedForAValidOrder() throws Exception {
        given(service.place(any())).willReturn(new OrderResponse(42L, "ACME", BigDecimal.TEN, PLACED));

        mockMvc.perform(post("/api/v1/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"customer":"ACME","items":[{"sku":"A-1","quantity":2}]}
                    """))
            .andExpect(status().isCreated())
            .andExpect(header().string("Location", "/api/v1/orders/42"))
            .andExpect(jsonPath("$.customer").value("ACME"));
    }
}
```

`@WebMvcTest` does not load the security config unless you import it. When the endpoint
has authorization rules, add `@Import(SecurityConfig.class)` and
`spring-security-test`'s `@WithMockUser` - otherwise the test proves the happy path of
an unprotected controller.

## TEST-2 - `@MockitoBean`, not `@MockBean`

`@MockBean` and `@SpyBean` are deprecated since Spring Boot 3.4 and gone in 4.0. The
replacements sit in `org.springframework.test.context.bean.override.mockito`:

```java
@MockitoBean     OrderService service;      // was @MockBean
@MockitoSpyBean  AuditService auditService; // was @SpyBean
```

In Kotlin with MockK the equivalents are `@MockkBean` / `@SpykBean` from
`springmockk` - the same rule applies, the bean is replaced in the context, not
constructed by hand.

## TEST-3 - Testcontainers instead of H2

H2 in Postgres mode is not Postgres: no `jsonb`, different upsert, different locking,
different index behaviour. A green test against H2 says nothing about the query that
runs in production.

**Kotlin**

```kotlin
@TestConfiguration(proxyBeanMethods = false)
class ContainerConfig {

    @Bean
    @ServiceConnection
    fun postgres(): PostgreSQLContainer<*> =
        PostgreSQLContainer("postgres:17-alpine").withReuse(true)
}

@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Import(ContainerConfig::class)
class OrderRepositoryTest(@Autowired val repository: OrderRepository) {

    @Test
    fun `finds orders by customer, newest first`() { ... }
}
```

`@ServiceConnection` (Spring Boot 3.1+) wires url, user and password itself - no
`@DynamicPropertySource` block any more. `@AutoConfigureTestDatabase(replace = NONE)`
is the part people forget: without it `@DataJpaTest` swaps in an embedded database and
the container just idles.

**Java** - same thing:

```java
@TestConfiguration(proxyBeanMethods = false)
class ContainerConfig {

    @Bean
    @ServiceConnection
    PostgreSQLContainer<?> postgres() {
        return new PostgreSQLContainer<>("postgres:17-alpine").withReuse(true);
    }
}
```

Reuse across runs turns the second run from 8 seconds into 0.2 - `~/.testcontainers.properties`:

```properties
testcontainers.reuse.enable=true
```

The same config class runs the app locally against real infrastructure:

```kotlin
fun main(args: Array<String>) {
    fromApplication<OrderApplication>().with(ContainerConfig::class).run(*args)
}
```

`./gradlew bootTestRun` or `./mvnw spring-boot:test-run` starts it.

## TEST-4 / TEST-5 - Negative cases and real assertions

```kotlin
// wrong - proves that something came back
@Test
fun testPlace() {
    val result = service.place(command)
    assertNotNull(result)
}

// right - one test per behaviour, asserting the value and the effect
@Test
fun `places an order and reserves the stock`() {
    val order = service.place(PlaceOrder("ACME", listOf(Item("A-1", 2))))

    assertThat(order.status).isEqualTo(OrderStatus.PLACED)
    assertThat(order.total).isEqualByComparingTo("19.98")
    verify(stock).reserve(listOf(Item("A-1", 2)))
}

@Test
fun `rejects an order for an unknown customer`() {
    assertThatThrownBy { service.place(PlaceOrder("nobody", listOf(Item("A-1", 1)))) }
        .isInstanceOf(CustomerNotFoundException::class.java)

    verify(stock, never()).reserve(any())
}
```

The negative case is where the code is usually wrong, and it is the one that gets
skipped. `verify(..., never())` is what makes "and nothing else happened" a test rather
than a hope.

## TEST-6 - No `Thread.sleep`

```kotlin
// wrong - flaky and slow at the same time
service.placeAsync(command)
Thread.sleep(2000)
assertThat(repository.count()).isEqualTo(1)

// right
service.placeAsync(command)
await().atMost(Duration.ofSeconds(5)).untilAsserted {
    assertThat(repository.count()).isEqualTo(1)
}
```

For `@TransactionalEventListener`, `ApplicationEvents` (`@RecordApplicationEvents`) or
Spring Modulith's `Scenario` API assert the event directly and skip the waiting.

## TEST-7 - ArchUnit carries the structural rules

Section 2 rules that get repeated in reviews belong in a test instead.

**Java**

```java
@AnalyzeClasses(packages = "com.example.orders", importOptions = DoNotIncludeTests.class)
class ArchitectureTest {

    @ArchTest
    static final ArchRule layers = layeredArchitecture().consideringAllDependencies()
        .layer("Web").definedBy("..web..")
        .layer("Service").definedBy("..service..")
        .layer("Persistence").definedBy("..persistence..")
        .whereLayer("Web").mayNotBeAccessedByAnyLayer()
        .whereLayer("Service").mayOnlyBeAccessedByLayers("Web")
        .whereLayer("Persistence").mayOnlyBeAccessedByLayers("Service");

    @ArchTest
    static final ArchRule noFieldInjection = noFields()
        .should().beAnnotatedWith(Autowired.class)
        .because("constructor injection only - STR-1");

    @ArchTest
    static final ArchRule controllersReturnDtos = noMethods()
        .that().areDeclaredInClassesThat().areAnnotatedWith(RestController.class)
        .should().haveRawReturnType(resideInAPackage("..domain.."))
        .because("entities do not cross the HTTP boundary - WEB-1");
}
```

**Kotlin** - the method form, because `@ArchTest` on a static field needs
`companion object` plus `@JvmField` and breaks quietly when someone drops it:

```kotlin
@AnalyzeClasses(packages = ["com.example.orders"], importOptions = [DoNotIncludeTests::class])
class ArchitectureTest {

    @ArchTest
    fun `controllers do not use repositories`(classes: JavaClasses) {
        noClasses()
            .that().resideInAPackage("..web..")
            .should().dependOnClassesThat().resideInAPackage("..persistence..")
            .because("STR-3")
            .check(classes)
    }
}
```

Dependency, both build tools:

```kotlin
testImplementation("com.tngtech.archunit:archunit-junit5:$archunitVersion")   // Gradle
```

```xml
<dependency>
  <groupId>com.tngtech.archunit</groupId>
  <artifactId>archunit-junit5</artifactId>
  <version>${archunit.version}</version>
  <scope>test</scope>
</dependency>
```

## TEST-8 - Names say the behaviour

```
testCreate2                              wrong
shouldWork                               wrong
placesAnOrderAndReservesTheStock         right (Java)
`rejects an order without items`         right (Kotlin, backticks)
`returns 409 when the version is stale`  right
```

The name is what you read in the CI output when it fails at 2am, without the code next
to it.
