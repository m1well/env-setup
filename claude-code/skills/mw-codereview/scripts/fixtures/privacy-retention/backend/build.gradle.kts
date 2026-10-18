plugins { id("org.springframework.boot") version "4.0.1"; kotlin("jvm") version "2.2.0"; kotlin("plugin.spring") version "2.2.0" }
dependencies {
  implementation("org.springframework.boot:spring-boot-starter-web")
  implementation("org.springframework.boot:spring-boot-starter-data-jpa")
  implementation("org.springframework.boot:spring-boot-starter-mail")
  implementation("org.flywaydb:flyway-core")
  implementation("org.postgresql:postgresql")
}
