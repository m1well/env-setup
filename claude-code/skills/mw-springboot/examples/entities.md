# Section 5 - Entities and embeddables

The schema is decided here, so this is the part that is expensive to get wrong. Same
domain as everywhere else: `Order`, `Customer`, `Employee`.

## MODEL-1 - Entity or embeddable

| Question | Entity | Embeddable |
| --- | --- | --- |
| Does it have its own id? | yes | no - it is identified by its owner |
| Can it exist without its owner? | yes | no |
| Is it referenced from somewhere else? | yes | no |
| Is it queried on its own? | yes | only through its owner |
| What is equality? | the id | all the fields |

An address that a customer *has* is an embeddable. An address that gets selected from a
list, shared between customers and edited independently is an entity. The same concept
can be both in two different applications - decide from the behaviour you need, not from
the noun.

## MODEL-2 - Repeating field groups become embeddables

**Wrong** - the same four columns, three times, and the formatting is reimplemented at
every call site:

```kotlin
@Entity
class Customer(
    var street: String,
    var zip: String,
    var city: String,
    var country: String,
)

@Entity
class Supplier(
    var street: String,
    var zip: String,
    var city: String,
    var country: String,
)
```

**Right (Kotlin)** - one type, with the behaviour that belongs to it:

```kotlin
@Embeddable
data class AddressEmbeddable(

    @field:NotBlank
    @Column(name = "street", nullable = false)
    val street: String,

    @field:NotBlank
    @field:Size(max = 10)
    @Column(name = "zip", nullable = false, length = 10)
    val zip: String,

    @field:NotBlank
    @Column(name = "city", nullable = false)
    val city: String,

    @field:NotNull
    @Enumerated(EnumType.STRING)
    @Column(name = "country", nullable = false, length = 2)
    val country: CountryCode,
) {
    fun formatted(): String = "$street, $zip $city, ${country.name}"

    fun isDomestic(): Boolean = country == CountryCode.DE
}
```

```kotlin
@Embeddable
data class PersonEmbeddable(

    @field:NotBlank
    @Column(name = "first_name", nullable = false)
    val firstName: String,

    @field:NotBlank
    @Column(name = "last_name", nullable = false)
    val lastName: String,

    @field:Past
    @Column(name = "birth_date", nullable = false)
    val birthDate: LocalDate,

    @field:NotNull
    @Enumerated(EnumType.STRING)
    @Column(name = "gender", nullable = false, length = 20)
    val gender: Gender,
) {
    val fullName: String get() = "$firstName $lastName"

    fun ageAt(reference: LocalDate): Int = Period.between(birthDate, reference).years

    fun isOfAgeAt(reference: LocalDate): Boolean = ageAt(reference) >= 18
}

enum class Gender { FEMALE, MALE, DIVERSE, UNDISCLOSED }
```

**Right (Java)** - a record works as an embeddable since Hibernate 6.2:

```java
@Embeddable
public record AddressEmbeddable(

    @NotBlank @Column(name = "street", nullable = false) String street,
    @NotBlank @Size(max = 10) @Column(name = "zip", nullable = false, length = 10) String zip,
    @NotBlank @Column(name = "city", nullable = false) String city,
    @NotNull @Enumerated(EnumType.STRING) @Column(name = "country", nullable = false, length = 2) CountryCode country
) {
    public String formatted() {
        return "%s, %s %s, %s".formatted(street, zip, city, country);
    }
}
```

Used like this:

```kotlin
@Entity
@Table(name = "customers")
class Customer(

    @Embedded
    @field:Valid
    var address: AddressEmbeddable,

    @Embedded
    @field:Valid
    var contact: PersonEmbeddable,
) {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    var id: Long? = null
        private set
}
```

`@Valid` on the embedded field is what makes Bean Validation descend into it. Without it
the constraints inside the embeddable are decoration.

The win is not fewer lines. It is that `isOfAgeAt`, `formatted` and the length limits
exist once instead of being reimplemented per entity - and that `Customer.contact` and
`Employee.person` are provably the same shape.

**The one warning:** an embeddable shared across bounded contexts is the canonical data
model sneaking back in. `AddressEmbeddable` in a `shared` module means the billing
context and the shipping context can no longer evolve their address independently.
Inside one module: share it. Across modules: copy it, and be glad you can.

## MODEL-3 vs MODEL-4 - `data class` here, never there

The rule inverts between the two, and that is the point:

```kotlin
@Embeddable
data class AddressEmbeddable(...)     // right - equality over all fields IS the semantics

@Entity
data class Customer(...)              // wrong - see below
```

An embeddable is a value: two addresses with the same street and city *are* the same
address. An entity is an identity: two customers with the same name are two customers.

**Why `data class` breaks an entity**, in three silent ways:

```kotlin
@Entity
data class Order(
    @Id @GeneratedValue val id: Long? = null,
    val customer: String,
    @OneToMany(mappedBy = "order") val items: List<OrderItem> = emptyList(),
)
```

- generated `hashCode` covers `id`, which is `null` before the flush and a number after -
  the instance is lost inside a `HashSet` it was put in five lines earlier
- generated `equals` touches `items`, initializing the lazy proxy, or throwing outside a
  session
- `copy()` produces a second instance with the same id, past every invariant the entity has

**Right**

```kotlin
@Entity
@Table(name = "orders")
class Order(
    @Embedded @field:Valid var billingAddress: AddressEmbeddable,
) {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    var id: Long? = null
        private set

    override fun equals(other: Any?): Boolean =
        this === other || (other is Order && id != null && id == other.id)

    override fun hashCode(): Int = javaClass.hashCode()
}
```

`hashCode` is deliberately constant per class, so the instance keeps working in a
collection across the flush that assigns its id.

In Java the same rule reads: Lombok `@Data` on an entity is wrong for exactly these
reasons, plus `@ToString` walking every association.

**Immutability**: an embeddable has `val` / final fields and is replaced, not mutated.

```kotlin
// wrong - and with a data class it does not even compile, which is the feature
customer.address.city = "Berlin"

// right - the entity owns the change, so it can validate or record it
fun relocate(newAddress: AddressEmbeddable) {
    require(newAddress.country == address.country) { "cross-border move needs a new contract" }
    address = newAddress
}
```

**Kotlin needs `kotlin("plugin.jpa")`** for both: it generates the no-arg constructor
Hibernate requires for `@Entity`, `@Embeddable` and `@MappedSuperclass`.

## MODEL-5 - Two of the same type need `@AttributeOverride`

Two `AddressEmbeddable` fields both want a column called `street`. Hibernate fails at
startup, which is the good case; with a bad naming strategy it silently maps both to one
column, which is not.

```kotlin
@Entity
@Table(name = "orders")
class Order(

    @Embedded
    @AttributeOverrides(
        AttributeOverride(name = "street", column = Column(name = "billing_street")),
        AttributeOverride(name = "zip", column = Column(name = "billing_zip")),
        AttributeOverride(name = "city", column = Column(name = "billing_city")),
        AttributeOverride(name = "country", column = Column(name = "billing_country")),
    )
    @field:Valid
    var billingAddress: AddressEmbeddable,

    @Embedded
    @AttributeOverrides(
        AttributeOverride(name = "street", column = Column(name = "shipping_street")),
        AttributeOverride(name = "zip", column = Column(name = "shipping_zip")),
        AttributeOverride(name = "city", column = Column(name = "shipping_city")),
        AttributeOverride(name = "country", column = Column(name = "shipping_country")),
    )
    @field:Valid
    var shippingAddress: AddressEmbeddable?,
)
```

Verbose, and worth it: the column names are the schema contract. Leave them to the
naming strategy and the next embeddable field silently renames half a table.

**This is where MODEL-5 meets MIG-2**: renaming `zip` to `postalCode` inside the
embeddable touches `customers`, `suppliers` and both address blocks on `orders`. One
field, four tables, one migration that has to list all of them.

## MODEL-6 - All columns null means the whole thing is null

Hibernate's default: if every column of an embedded value is `NULL`, the field comes back
as `null` - not as an instance full of nulls. In Kotlin that is an NPE on a
non-nullable property, at read time, in production.

Decide per embeddable, and make the schema say the same thing:

```kotlin
// mandatory: every column NOT NULL, the field non-nullable
@Embedded @field:Valid
var address: AddressEmbeddable

// optional: the field is nullable and the code says what absence means
@Embedded @field:Valid
var shippingAddress: AddressEmbeddable? = null

fun deliveryAddress(): AddressEmbeddable = shippingAddress ?: billingAddress
```

What does not work is a half-optional embeddable - three columns nullable, one not. Then
a partially filled address loads fine and a completely empty one comes back `null`, and
the difference is invisible in the code.

## MODEL-7 - `EnumType.STRING`, always

```kotlin
// wrong - and the default, which is why it keeps happening
@Enumerated
var gender: Gender

// wrong, explicitly
@Enumerated(EnumType.ORDINAL)
var status: OrderStatus

// right
@Enumerated(EnumType.STRING)
@Column(name = "status", nullable = false, length = 20)
var status: OrderStatus
```

`ORDINAL` stores the position. Insert `DIVERSE` between `MALE` and `UNDISCLOSED` and
every existing row changes meaning - no error, no migration, no way to tell afterwards
which rows were written before the change. Length the column generously; a new enum
value is a code change, a longer column is a migration.

For a fixed vocabulary that also needs a foreign key, a lookup table beats an enum -
but then it is an entity (MODEL-1).

## MODEL-8 - Lists of value objects: `@ElementCollection`

```kotlin
// wrong - a comma-joined string that every reader has to parse
@Column(name = "tags")
var tags: String

// wrong - an entity with an artificial id for something that has no identity
@OneToMany(cascade = [CascadeType.ALL])
var tags: MutableList<TagEntity>

// right
@ElementCollection(fetch = FetchType.LAZY)
@CollectionTable(
    name = "customer_addresses",
    joinColumns = [JoinColumn(name = "customer_id")],
)
@OrderColumn(name = "position")
private val _addresses: MutableList<AddressEmbeddable> = mutableListOf()
val addresses: List<AddressEmbeddable> get() = _addresses.toList()
```

The trade-off, and it decides the design: an element collection has no ids, so on every
change Hibernate deletes the whole collection and reinserts it. Fine for five addresses,
wrong for five thousand rows or for anything another table points at. `@OrderColumn`
makes the order stable and reduces the churn; past a few dozen elements it belongs in
its own entity after all.

## MODEL-9 - Money and time

```kotlin
// wrong - binary floating point cannot represent 0.10, and the currency lives elsewhere
var price: Double

// right
@Embeddable
data class MoneyEmbeddable(
    @Column(name = "amount", nullable = false, precision = 19, scale = 4)
    val amount: BigDecimal,

    @Column(name = "currency", nullable = false, length = 3)
    val currency: Currency,
) {
    operator fun plus(other: MoneyEmbeddable): MoneyEmbeddable {
        require(currency == other.currency) { "cannot add $currency and ${other.currency}" }
        return copy(amount = amount + other.amount)
    }
}
```

`precision` and `scale` are not optional - without them the DDL and the migration
disagree about what fits, and rounding shows up as a cent that goes missing once a week.

Time: `Instant` for a moment in time (an audit timestamp), `LocalDate` for a calendar
day (a birth date), `LocalDateTime` almost never - it is a timestamp without the
information needed to interpret it. A birth date stored as a timestamp moves by a day
every time a timezone changes.

## MODEL-10 - `@Version` where writes collide

```kotlin
@Entity
class Order(...) {

    @Version
    var version: Long = 0
}
```

Two requests read the same order, both write, the second silently wins. With `@Version`
the second gets an `OptimisticLockingFailureException`, the advice turns it into 409,
and the client can retry with fresh data (WEB-5).

## MODEL-11 - Behaviour, not setters

```kotlin
// wrong - the invariant lives at the call site, so the third caller forgets it
order.status = OrderStatus.SHIPPED
order.shippedAt = Instant.now()

// right
fun markAsShipped(clock: Clock) {
    check(status == OrderStatus.PAID) { "only a paid order can ship, was $status" }
    status = OrderStatus.SHIPPED
    shippedAt = Instant.now(clock)
}
```

Setters that exist only because a mapper needs them are how an entity turns into a
struct. Keep the fields `private set` (Kotlin) or package-private (Java) and let the
entity offer the transitions it actually has.

## Querying through an embeddable

Path expressions work, and so does the index you have to remember:

```kotlin
interface CustomerRepository : JpaRepository<Customer, Long> {

    fun findByContactLastName(lastName: String): List<Customer>

    @Query("select c from Customer c where c.address.city = :city and c.address.country = :country")
    fun findInCity(city: String, country: CountryCode): List<Customer>

    @Query("select c from Customer c where c.contact.birthDate < :date")
    fun findOlderThan(date: LocalDate): List<Customer>
}
```

The derived name is `findByContactLastName` - property path `contact.lastName`, not the
column name. And the index is on the physical column, so it belongs in the migration:

```sql
create index idx_customers_last_name on customers (last_name);
create index idx_customers_city_country on customers (city, country);
```

## Embeddables and the API boundary

An embeddable is a persistence type, so WEB-1 still applies - it does not go on the wire.
What it does give you is a mapping that is written once:

```kotlin
data class AddressDto(val street: String, val zip: String, val city: String, val country: String) {

    fun toEmbeddable() = AddressEmbeddable(street, zip, city, CountryCode.valueOf(country))

    companion object {
        fun of(address: AddressEmbeddable) =
            AddressDto(address.street, address.zip, address.city, address.country.name)
    }
}
```

Every DTO that carries an address reuses `AddressDto`, and the JSON shape stays the same
across endpoints - which is the API-side version of the same win.
