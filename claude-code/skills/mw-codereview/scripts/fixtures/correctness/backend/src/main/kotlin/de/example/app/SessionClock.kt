package de.example.app

import java.time.Clock
import java.time.Duration
import java.time.Instant
import java.time.LocalDateTime
import java.time.temporal.ChronoUnit
import org.springframework.stereotype.Service

data class Session(val id: Long, val startedAt: LocalDateTime, val createdAt: Instant)

@Service
class SessionClock(private val timeHelper: TimeHelper, private val clock: Clock) {

  fun elapsedMillis(session: Session): Long = Duration.between(session.startedAt, timeHelper.now()).toMillis()

  fun elapsedMinutes(session: Session): Long {
    val start = session.startedAt
    return ChronoUnit.MINUTES.between(start, LocalDateTime.now(clock))
  }

  fun ageSeconds(session: Session): Long = Duration.between(session.createdAt, Instant.now(clock)).seconds

  fun calendarDays(session: Session, until: LocalDateTime): Long = ChronoUnit.DAYS.between(session.startedAt, until)

  fun unknown(a: Any, b: Any): Long = Duration.between(a.toString().let { LocalDateTime.parse(it) }, b as LocalDateTime).toMillis()
}
