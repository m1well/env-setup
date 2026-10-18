package de.app

import org.springframework.mail.SimpleMailMessage
import org.springframework.mail.javamail.JavaMailSender
import org.springframework.stereotype.Component
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional
import org.springframework.transaction.support.TransactionSynchronization
import org.springframework.transaction.support.TransactionSynchronizationManager
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RestController
import org.springframework.web.servlet.support.ServletUriComponentsBuilder

data class AccessRequest(val email: String, val name: String)

data class Account(val id: String, val email: String)

@Component
class MailGateway(private val sender: JavaMailSender) {
    fun send(to: String, subject: String, text: String) {
        sender.send(SimpleMailMessage().apply {
            setTo(to)
            setSubject(subject)
            setText(text)
        })
    }
}

@Service
class Accounts {
    fun byEmail(email: String): Account? = null
}

@Service
class AccessService(private val mail: MailGateway, private val accounts: Accounts, private val links: LinkRepository) {
    @Transactional
    fun send(address: String, link: String) {
        links.save(LinkEntity(tokenHash = link.reversed()))
        mail.send(address, "Your link", link)
    }

    @Transactional
    fun notify(address: String) {
        val account = accounts.byEmail(address) ?: return
        TransactionSynchronizationManager.registerSynchronization(object : TransactionSynchronization {
            override fun afterCommit() = mail.send(account.email, "Hello", "Someone asked for your account")
        })
    }
}

@RestController
class AccessController(private val access: AccessService) {
    @PostMapping("/public/access")
    fun request(@RequestBody req: AccessRequest) {
        val base = ServletUriComponentsBuilder.fromCurrentContextPath()
        access.send(req.email, base.path("/links/{t}").buildAndExpand("t").toUriString())
    }

    @PostMapping("/public/notify")
    fun notify(@RequestBody req: AccessRequest) = access.notify(req.email)
}
