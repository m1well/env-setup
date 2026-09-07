# Section 7 - Security and configuration

Security findings are blockers by default. Downgrade one only when you can say why it
cannot be reached.

## SEC-1 / SEC-2 / SEC-3 - The filter chain

**Wrong** - a 5.x tutorial that survived the migration, plus a blanket `permitAll()`:

```java
@Configuration
public class SecurityConfig extends WebSecurityConfigurerAdapter {   // gone in Spring Security 6

    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http.csrf().disable()
            .authorizeRequests()
            .anyRequest().permitAll();                               // the whole API is open
    }
}
```

**Right (Java)** - a bean, the lambda DSL, default deny at the end:

```java
@Configuration
@EnableMethodSecurity
public class SecurityConfig {

    @Bean
    SecurityFilterChain apiFilterChain(HttpSecurity http) throws Exception {
        return http
            // stateless JWT API: no session, no cookie, so no CSRF vector
            .csrf(AbstractHttpConfigurer::disable)
            .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/actuator/health/**").permitAll()
                .requestMatchers(HttpMethod.GET, "/api/v1/orders/**").hasAuthority("SCOPE_orders:read")
                .requestMatchers("/api/v1/orders/**").hasAuthority("SCOPE_orders:write")
                .anyRequest().authenticated())
            .oauth2ResourceServer(oauth -> oauth.jwt(Customizer.withDefaults()))
            .build();
    }
}
```

**Right (Kotlin)** - same chain in the Kotlin DSL:

```kotlin
@Configuration
@EnableMethodSecurity
class SecurityConfig {

    @Bean
    fun apiFilterChain(http: HttpSecurity): SecurityFilterChain {
        http {
            csrf { disable() }
            sessionManagement { sessionCreationPolicy = SessionCreationPolicy.STATELESS }
            authorizeHttpRequests {
                authorize("/actuator/health/**", permitAll)
                authorize(HttpMethod.GET, "/api/v1/orders/**", hasAuthority("SCOPE_orders:read"))
                authorize("/api/v1/orders/**", hasAuthority("SCOPE_orders:write"))
                authorize(anyRequest, authenticated)
            }
            oauth2ResourceServer { jwt { } }
        }
        return http.build()
    }
}
```

Three things a review checks on every chain:

- is there an `anyRequest()` rule, and is it `authenticated()`
- is `csrf().disable()` paired with `STATELESS` - if a session or a cookie login exists
  anywhere, disabling CSRF is a blocker
- does a `permitAll()` cover a mutating method. `permitAll` on `POST /api/v1/orders` is
  the finding that ends up in the incident review

`@EnableMethodSecurity` replaces `@EnableGlobalMethodSecurity`, and it enables
`@PreAuthorize` by default.

## SEC-4 - CORS

```java
// wrong - on the controller, wildcard, and invalid together with credentials
@CrossOrigin(origins = "*", allowCredentials = "true")
@RestController
public class OrderController { ... }

// right - central, explicit, from configuration
@Bean
CorsConfigurationSource corsConfigurationSource(CorsProperties properties) {
    var config = new CorsConfiguration();
    config.setAllowedOrigins(properties.allowedOrigins());     // from application.yml per environment
    config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE"));
    config.setAllowedHeaders(List.of("Authorization", "Content-Type"));
    config.setAllowCredentials(true);
    var source = new UrlBasedCorsConfigurationSource();
    source.registerCorsConfiguration("/api/**", config);
    return source;
}
```

`allowedOrigins("*")` with `allowCredentials(true)` throws at runtime. The workaround
people reach for - `allowedOriginPatterns("*")` - keeps it running and hands every site
on the internet an authenticated request. Both are blockers.

## SEC-5 - No secrets in the repository

```yaml
# wrong - application.yml, in git, forever
spring:
  datasource:
    url: jdbc:postgresql://prod-db:5432/orders
    username: orders_app
    password: S3cr3t-2024!
app:
  payment:
    api-key: sk_live_9f2c...

# right - the value comes from the environment, the file names it
spring:
  datasource:
    url: ${DATABASE_URL}
    username: ${DATABASE_USERNAME}
    password: ${DATABASE_PASSWORD}
app:
  payment:
    api-key: ${PAYMENT_API_KEY}
```

Grep the scope before calling section 7 done:

```bash
grep -rEn '(password|secret|token|api[-_]?key|private[-_]?key)\s*[:=]\s*[^$\s].{6,}' \
  --include='*.yml' --include='*.yaml' --include='*.properties' \
  --include='*.kt' --include='*.java' src/ | grep -v '\${'
```

A secret that was ever committed counts as leaked even after the fix commit - the
finding says "rotate", not "remove".

## SEC-6 - SpEL takes what you give it

```java
// wrong - user input parsed as an expression. This is the Spring4Shell family
public boolean check(String rule, Order order) {
    return new SpelExpressionParser().parseExpression(rule)
        .getValue(new StandardEvaluationContext(order), Boolean.class);
}

// wrong - an annotation value built from a variable is either a compile error or a constant
//         you did not intend; either way, filters do not belong in the annotation string
@PreAuthorize("hasRole('" + ROLE_FROM_SOMEWHERE + "')")

// right - static expression, dynamic values as method arguments
@PreAuthorize("hasAuthority('SCOPE_orders:write') and #command.customer == authentication.name")
public Order place(PlaceOrder command) { ... }
```

If a rule genuinely has to be dynamic, it is a lookup against an allow-list of known
rules, never a parsed string.

## SEC-7 - Deserialization and XML

```java
// wrong - remote code execution as a feature
var in = new ObjectInputStream(request.getInputStream());
var payload = (OrderPayload) in.readObject();

// right - a data format that does not instantiate arbitrary classes
var payload = objectMapper.readValue(request.getInputStream(), OrderPayload.class);
```

Jackson is only safe as long as polymorphic typing stays off - `activateDefaultTyping`
or `@JsonTypeInfo(use = Id.CLASS)` on untrusted input is the same hole in a nicer
format.

```java
// wrong - Java's XML parsers resolve external entities by default (XXE)
var factory = DocumentBuilderFactory.newInstance();

// right
var factory = DocumentBuilderFactory.newInstance();
factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
factory.setXIncludeAware(false);
factory.setExpandEntityReferences(false);
```

## SEC-8 - Logs are not a dumping ground

```kotlin
// wrong - concatenated, unbounded, and it prints the token
log.info("Login for " + username + " with token " + token)

// better, still not enough on its own
log.info("Login for {}", username)

// right - parameterized, no secrets, and a JSON encoder so a newline cannot forge a line
log.info("Login attempt for user id {}", user.id)
```

Two separate problems, and reviews mix them up:

- **secrets and personal data** in the log - tokens, passwords, full names, addresses,
  card numbers. Parameterizing does not help here; removing the value does
- **log injection** - a `\n` in user input writes a second, fake log line.
  Parameterizing does not fix that either. A structured encoder (logstash JSON encoder,
  `logging.structured.format.console=ecs` since Spring Boot 3.4) does, because the value
  ends up escaped inside a field

## SEC-9 - Actuator

```yaml
# wrong - every endpoint, including heapdump, env and threaddump, on the app port
management:
  endpoints:
    web:
      exposure:
        include: "*"
  endpoint:
    health:
      show-details: always

# right
management:
  endpoints:
    web:
      exposure:
        include: health,info,prometheus
  endpoint:
    health:
      show-details: when-authorized
      probes:
        enabled: true
  server:
    port: 8081          # separate port, not reachable from outside the cluster
```

`env`, `configprops`, `heapdump` and `threaddump` hand out configuration values and
memory contents. On a public port that is a blocker regardless of what else is in the
chain.

## SEC-10 - Password storage

```java
// blocker
@Bean
PasswordEncoder passwordEncoder() {
    return NoOpPasswordEncoder.getInstance();
}

// right - delegating, so the prefix records the algorithm and a future migration is possible
@Bean
PasswordEncoder passwordEncoder() {
    return PasswordEncoderFactories.createDelegatingPasswordEncoder();   // bcrypt by default
}
```

MD5, SHA-1 and plain SHA-256 are the same finding: fast hashes are the wrong tool for
passwords, whatever the salt.
