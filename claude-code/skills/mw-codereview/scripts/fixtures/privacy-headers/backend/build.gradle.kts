plugins { id("org.springframework.boot") version "4.0.1"; kotlin("jvm") version "2.2.0"; kotlin("plugin.spring") version "2.2.0" }
dependencies {
  implementation("org.springframework.boot:spring-boot-starter-web")
  implementation("org.springframework.boot:spring-boot-starter-data-jpa")
  implementation("org.flywaydb:flyway-core")
  implementation("org.postgresql:postgresql")
  implementation("com.stripe:stripe-java:28.0.0")
  implementation("org.springframework.ai:spring-ai-openai")
}
