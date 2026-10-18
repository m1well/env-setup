package de.beispiel

import jakarta.servlet.http.HttpServletRequest
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Value
import org.springframework.http.ProblemDetail
import org.springframework.mail.SimpleMailMessage
import org.springframework.mail.javamail.JavaMailSender
import org.springframework.stereotype.Component
import org.springframework.stereotype.Service
import org.springframework.web.bind.annotation.ExceptionHandler
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.RestController
import org.springframework.web.bind.annotation.RestControllerAdvice
import org.springframework.web.client.RestClient

interface Meldung {
    fun fehler(text: String)
}

@Component
class ChatMeldung(private val client: RestClient, @Value("\${app.meldung.slack-webhook}") private val webhook: String) :
    Meldung {
    override fun fehler(text: String) {
        client.post().uri(webhook).body(mapOf("text" to text)).retrieve().toBodilessEntity()
    }
}

@RestController
class ZugangController {
    @GetMapping("/zugang/{token}")
    fun einloesen(@PathVariable token: String): String = "ok"
}

@RestControllerAdvice
class Fehlerbehandlung(private val meldung: Meldung) {
    private val log = LoggerFactory.getLogger(javaClass)

    @ExceptionHandler(Exception::class)
    fun unerwartet(e: Exception, request: HttpServletRequest): ProblemDetail {
        log.error("Fehler bei {}", request.requestURI, e)
        meldung.fehler("Fehler bei ${request.requestURI}")
        return ProblemDetail.forStatus(500)
    }

    fun intern(request: HttpServletRequest): Boolean = request.requestURI.startsWith("/intern")
}

data class AnfrageDto(val kundenEmail: String)

data class DienstEigenschaften(val adresse: String)

@Service
class Benachrichtigung(private val mailSender: JavaMailSender, private val eigenschaften: DienstEigenschaften) {
    private val log = LoggerFactory.getLogger(javaClass)

    fun bestaetigen(anfrage: AnfrageDto) {
        val nachricht = SimpleMailMessage()
        nachricht.setTo(anfrage.kundenEmail)
        mailSender.send(nachricht)
        log.info("Bestaetigung an {} gesendet", anfrage.kundenEmail)
        log.info("Kopie an {}", maskiert(anfrage.kundenEmail))
        log.warn("Dienst {} nicht erreichbar", eigenschaften.adresse)
    }

    private fun maskiert(wert: String) = wert.take(2) + "***"
}
