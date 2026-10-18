package de.praxis

import org.slf4j.LoggerFactory
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.web.bind.annotation.*
import java.util.UUID

interface PatientRepository : JpaRepository<Patient, UUID> {
    fun findByEmail(email: String): Patient?
}

@RestController
@RequestMapping("/api/patienten")
class PatientController(private val patients: PatientRepository) {
    private val log = LoggerFactory.getLogger(javaClass)

    @GetMapping("/suche/{email}")
    fun byEmail(@PathVariable email: String): PatientDto? {
        val p = patients.findByEmail(email) ?: return null
        log.info("Patient gefunden: ${p.email}, iban {}", p.iban)
        return PatientDto(p.id, p.email, p.iban, null)
    }

    @GetMapping
    fun all(): List<PatientDto> = patients.findAll().map { PatientDto(it.id, it.email, it.iban, null) }
}
