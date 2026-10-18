plugins { id("org.springframework.boot") version "3.5.6"; kotlin("jvm") version "2.2.0"; kotlin("plugin.spring") version "2.2.0" }
dependencies {
  implementation("org.springframework.boot:spring-boot-starter-web")
  implementation("org.springframework.boot:spring-boot-starter-security")
  implementation("org.springframework.boot:spring-boot-starter-oauth2-resource-server")
  implementation("org.springframework.boot:spring-boot-starter-data-jpa")
  implementation("org.flywaydb:flyway-core")
  implementation("org.postgresql:postgresql")
}
