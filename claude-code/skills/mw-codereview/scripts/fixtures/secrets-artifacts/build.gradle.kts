plugins {
    id("org.springframework.boot") version "3.5.7"
    kotlin("jvm") version "2.2.20"
}

tasks.bootJar {
    exclude("application-ci.yaml")
}
