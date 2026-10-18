package de.example.app

import java.time.Clock
import java.time.LocalDateTime
import java.time.ZoneId
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.stereotype.Component

@Configuration
class TimeConfig {
  @Bean fun clock(): Clock = Clock.system(ZoneId.of("Europe/Berlin"))
}

@Component
class TimeHelper(private val clock: Clock) {
  fun now(): LocalDateTime = LocalDateTime.now(clock)
}
