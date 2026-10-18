package de.praxis

import jakarta.persistence.Entity
import jakarta.persistence.Id
import java.time.LocalDate
import java.util.UUID

@Entity
data class Patient(
    @Id val id: UUID,
    var vorname: String,
    var nachname: String,
    var email: String?,
    var geburtsdatum: LocalDate?,
    var iban: String?,
    var diagnose: String?,
    var konfession: String?,
    var notiz: String?,
    var geloescht: Boolean = false,
)

@Entity
class NewsletterAbonnent(@Id val id: UUID, var email: String, var newsletter: Boolean = false)

data class PatientDto(val id: UUID, val email: String?, val iban: String?, val passwordHash: String?)
