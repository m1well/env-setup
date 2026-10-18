package de.beispiel

import jakarta.persistence.Entity
import jakarta.persistence.Id
import jakarta.persistence.Table
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Modifying
import org.springframework.data.jpa.repository.Query
import org.springframework.stereotype.Service
import java.time.Instant
import java.util.UUID

@Entity
@Table(name = "kunde")
class Kunde(@Id val id: UUID, var name: String, var email: String, val erstelltAm: Instant)

interface KundeRepository : JpaRepository<Kunde, UUID>

@Service
class KundenService(private val kunden: KundeRepository) {
    fun loeschen(id: UUID) = kunden.deleteById(id)
}

@Entity
@Table(name = "anfrage")
class Anfrage(@Id val id: UUID, val email: String, val erstelltAm: Instant)

interface AnfrageRepository : JpaRepository<Anfrage, UUID> {
    @Modifying
    @Query("delete from Anfrage a where a.erstelltAm < :grenze")
    fun alteEntfernen(grenze: Instant): Int
}

@Entity
@Table(name = "passwort_reset")
class PasswortReset(@Id val id: UUID, val resetToken: String, val erstelltAm: Instant)

interface PasswortResetRepository : JpaRepository<PasswortReset, UUID> {
    fun deleteByErstelltAmBefore(grenze: Instant)
}

@Entity
@Table(name = "fahrer")
class Fahrer(@Id val id: Long, val username: String, var displayName: String?)

interface FahrerRepository : JpaRepository<Fahrer, Long> {
    fun findByUsername(username: String): Fahrer?
}
