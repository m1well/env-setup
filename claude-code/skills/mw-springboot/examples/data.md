# Section 4 - Repositories, transactions, queries

Applies to JPA. With jOOQ, JDBC or MyBatis, DATA-1, DATA-2 and DATA-6 still hold, and so
does all of section 6; the rest does not apply - check the stack before writing code or a
finding.

## DATA-1 - Transactions belong to the service

The service is where a use case starts and ends, so it is the only place that knows
what has to be atomic. On the repository the boundary is one statement wide, on the
controller it stays open across serialization.

```kotlin
// wrong - two writes, two transactions, half-finished state after a failure
@Service
class OrderService(private val orders: OrderRepository, private val stock: StockRepository) {

    fun place(command: PlaceOrder): Order {
        val order = orders.save(Order.from(command))
        stock.reserve(command.items)          // fails -> the order exists without a reservation
        return order
    }
}

// right
@Service
class OrderService(private val orders: OrderRepository, private val stock: StockRepository) {

    @Transactional
    fun place(command: PlaceOrder): Order {
        val order = orders.save(Order.from(command))
        stock.reserve(command.items)
        return order
    }

    @Transactional(readOnly = true)
    fun search(customer: String, pageable: Pageable): Page<OrderResponse> =
        orders.findByCustomer(customer, pageable).map(OrderResponse::of)
}
```

`readOnly = true` is not decoration: Hibernate skips dirty checking and the flush, and
the driver can route the statement to a replica.

## DATA-2 - Self-invocation runs without a transaction

The proxy sits between the caller and the bean. A call from inside the bean never
touches it, so the annotation does nothing - and nothing in the log says so.

```java
// wrong - place() calls a @Transactional method on this, so there is no transaction
@Service
public class OrderService {

    public Order place(PlaceOrder command) {
        return persist(command);
    }

    @Transactional
    public Order persist(PlaceOrder command) { ... }
}

// right - the annotation goes on the entry point
@Service
public class OrderService {

    @Transactional
    public Order place(PlaceOrder command) {
        return persist(command);
    }

    private Order persist(PlaceOrder command) { ... }
}
```

Same trap for `@Cacheable`, `@Async`, `@Retryable` and `@PreAuthorize`. When two
different propagations really are needed, the inner one moves to its own bean.

Kotlin adds a second way to lose it: a `private fun` cannot be proxied either, and
without the `kotlin-spring` plugin (STR-7) neither can the class.

## DATA-3 / DATA-4 - EAGER and the N+1 it hides

**Wrong**

```kotlin
@Entity
class Order(
    @OneToMany(mappedBy = "order", fetch = FetchType.EAGER)   // wrong - loaded on every query, always
    val items: MutableList<OrderItem> = mutableListOf(),
)
```

`EAGER` means every `findAll`, every `findById`, every derived query drags the
collection along - including the ones that only need the total. It also cannot be
turned off at the call site, while `LAZY` can always be turned on with a fetch join.

**Wrong** - lazy, but the loop makes it worse: one query for the orders, then one per
order for the items. 200 orders, 201 queries:

```kotlin
@Transactional(readOnly = true)
fun report(customer: String): List<OrderSummary> =
    orders.findByCustomer(customer).map { OrderSummary(it.id, it.items.sumOf { i -> i.total }) }
```

**Right** - one query, association fetched on purpose:

```kotlin
interface OrderRepository : JpaRepository<Order, Long> {

    @EntityGraph(attributePaths = ["items"])
    fun findByCustomer(customer: String): List<Order>
}
```

or, when the query is explicit anyway:

```kotlin
@Query("select distinct o from Order o join fetch o.items where o.customer = :customer")
fun findWithItems(customer: String): List<Order>
```

**How to prove it in a review**, instead of guessing:

```yaml
logging:
  level:
    org.hibernate.SQL: debug
    org.hibernate.orm.jdbc.bind: trace
```

A finding says "one query per order, see the loop in `OrderService.kt:48` over the lazy
`items`". A finding that says "possible N+1" has not been checked.

## DATA-5 - join fetch plus Pageable paginates in memory

```kotlin
// wrong - Hibernate loads every matching row, then pages the list in the JVM
@Query("select o from Order o join fetch o.items where o.customer = :customer")
fun findWithItems(customer: String, pageable: Pageable): Page<Order>
```

The tell is in the log: `HHH90003004: firstResult/maxResults specified with collection
fetch; applying in memory` (Hibernate 6; `HHH000104` on 5). It works in test and
allocates the whole table in production.

**Right** - page the ids, then fetch:

```kotlin
@Query("select o.id from Order o where o.customer = :customer")
fun findIdsByCustomer(customer: String, pageable: Pageable): Page<Long>

@Query("select distinct o from Order o join fetch o.items where o.id in :ids")
fun findWithItemsByIds(ids: List<Long>): List<Order>
```

Or skip the entity: a projection (DATA-7) has no collection to fetch and pages fine.

## DATA-6 - Parameters, never concatenation

```java
// wrong - JPQL injection, and it defeats the statement cache
@Query("select o from Order o where o.customer = '" + customer + "'")   // not even valid as a constant
List<Order> find(String customer);

// wrong - the same mistake where it actually compiles
public List<Order> search(String customer) {
    return em.createQuery("select o from Order o where o.customer = '" + customer + "'", Order.class)
             .getResultList();
}

// right
@Query("select o from Order o where o.customer = :customer")
List<Order> find(@Param("customer") String customer);

// right - native SQL is no exception
@Query(value = "select * from orders where customer = :customer", nativeQuery = true)
List<Order> findNative(@Param("customer") String customer);
```

Sorting is the sneaky one: a column name coming from a request cannot be a parameter,
so it has to be checked against an allow-list before it reaches the query.

## DATA-7 - Projections for reads

```kotlin
// wrong - three columns needed, the full graph loaded and mapped
fun titles(customer: String): List<String> =
    orders.findByCustomer(customer).map { it.title }

// right - interface projection, Spring Data selects only these columns
interface OrderSummaryView {
    val id: Long
    val customer: String
    val total: BigDecimal
}

fun findSummariesByCustomer(customer: String): List<OrderSummaryView>

// right - DTO query when the shape needs computing
@Query("""
    select new com.example.orders.OrderSummary(o.id, o.customer, sum(i.total))
    from Order o join o.items i
    where o.customer = :customer
    group by o.id, o.customer
""")
fun summaries(customer: String): List<OrderSummary>
```

## Moved out of this file

Entity and embeddable modelling - including why a Kotlin `@Entity` is never a
`data class`, and `@Version` - is section 5, `entities.md`. Migrations are section 6,
`migrations.md`.
