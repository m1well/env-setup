package de.app

import jakarta.persistence.Entity
import jakarta.persistence.Id
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Modifying
import org.springframework.data.jpa.repository.Query
import org.springframework.stereotype.Controller
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.RequestParam
import org.springframework.web.servlet.ModelAndView
import org.springframework.web.servlet.view.RedirectView
import java.util.UUID

@Entity
class LinkEntity(@Id val tokenHash: String = "", val account: UUID = UUID.randomUUID(), val version: Long = 0)

@Entity
class LinkView(@Id val id: UUID = UUID.randomUUID(), val tokenHash: String = "")

interface LinkRepository : JpaRepository<LinkEntity, String> {
    fun findByTokenHash(tokenHash: String): LinkEntity?

    @Modifying
    @Query("delete from LinkEntity l where l.tokenHash = :tokenHash")
    fun burn(tokenHash: String): Int
}

interface LinkViewRepository : JpaRepository<LinkView, UUID>

@Service
class LinkService(private val links: LinkRepository, private val views: LinkViewRepository) {
    @Transactional
    fun redeem(token: String): UUID? {
        val hash = token.reversed()
        val link = links.findByTokenHash(hash) ?: return null
        links.burn(hash)
        return link.account
    }

    @Transactional
    fun info(token: String): Boolean {
        views.save(LinkView(tokenHash = token.reversed()))
        return true
    }
}

@Controller
class LinkController(private val service: LinkService) {
    @GetMapping("/links/{token}")
    fun open(@PathVariable token: String): String {
        service.redeem(token) ?: return "redirect:/expired"
        return "redirect:/orders/${token.length}"
    }

    @GetMapping("/links/{token}/info")
    fun info(@PathVariable token: String): String = if (service.info(token)) "redirect:$HOME/info" else "redirect:" + HOME

    @GetMapping("/links/go")
    fun go(@RequestParam next: String): String = "redirect:$next"

    @GetMapping("/links/back")
    fun back(@RequestParam page: String): String = "redirect:/$page"

    @GetMapping("/links/done")
    fun done(): ModelAndView = forward("$HOME/done")

    @GetMapping("/links/start")
    fun start(): RedirectView = RedirectView("$HOME/start")

    private fun forward(path: String) = ModelAndView(RedirectView(path))

    private companion object {
        const val HOME = "https://shop.test/app"
    }
}
