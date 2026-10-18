package de.beispiel

import org.springframework.boot.ApplicationArguments
import org.springframework.boot.ApplicationRunner
import org.springframework.scheduling.annotation.Scheduled
import org.springframework.stereotype.Component
import java.time.Duration
import java.time.Instant

@Component
class Bereinigung(private val anfragen: AnfrageRepository, private val resets: PasswortResetRepository) {
    @Scheduled(cron = "0 0 3 * * *")
    fun naechtlich() {
        anfragen.alteEntfernen(Instant.now().minus(Duration.ofDays(90)))
        tokensEntfernen()
    }

    private fun tokensEntfernen() = resets.deleteByErstelltAmBefore(Instant.now().minus(Duration.ofHours(2)))
}

@Component
class StammdatenSeed(private val fahrerRepository: FahrerRepository) : ApplicationRunner {
    override fun run(args: ApplicationArguments) {
        fahrerRepository.findByUsername("fahrer1") ?: fahrerRepository.save(Fahrer(1, "fahrer1", "Fahrer Eins"))
    }
}
