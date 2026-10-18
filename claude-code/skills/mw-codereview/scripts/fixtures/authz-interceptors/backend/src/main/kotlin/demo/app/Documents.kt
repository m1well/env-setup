package demo.app

import org.springframework.boot.CommandLineRunner
import org.springframework.security.core.annotation.AuthenticationPrincipal
import org.springframework.security.oauth2.jwt.Jwt
import org.springframework.stereotype.Component
import org.springframework.web.bind.annotation.DeleteMapping
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.PutMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RequestParam
import org.springframework.web.bind.annotation.RestController
import java.util.UUID

@RestController
@RequestMapping("/api/documents")
class DocumentController(private val documents: DocumentService) {
    @GetMapping("/{id}")
    fun get(@PathVariable id: UUID, @AuthenticationPrincipal jwt: Jwt) = documents.get(id, UUID.fromString(jwt.subject))

    @PutMapping("/{id}")
    fun rename(@PathVariable id: UUID, @RequestBody title: String, @AuthenticationPrincipal jwt: Jwt) =
        documents.rename(id, title, UUID.fromString(jwt.subject))

    @DeleteMapping("/{id}")
    fun delete(@PathVariable id: UUID) = documents.delete(id)

    @GetMapping("/{id}/mine")
    fun mine(@PathVariable id: UUID) = documents.mine(id)

    @PostMapping("/{id}/archive")
    fun archive(@PathVariable id: UUID) = documents.archive(id)

    @GetMapping("/{id}/history")
    fun history(@PathVariable id: UUID) = documents.history(id)

    @GetMapping("/classified")
    fun classify(@RequestParam id: UUID) = documents.classify(id)
}

@Component
class DemoSeeder(private val documents: DocumentRepository, private val users: AppUserRepository) : CommandLineRunner {
    override fun run(vararg args: String) {
        val owner = users.findByUsername("demo") ?: return
        documents.findByIdAndOwnerId(UUID(0, 1), owner.id)
    }
}

@RestController
@RequestMapping("/api/projects")
class ProjectController(private val projects: ProjectRepository) {
    @GetMapping("/{projectId}")
    fun get(@PathVariable projectId: UUID) = projects.findById(projectId)

    @PutMapping("/{projectId}/budget")
    fun budget(@PathVariable projectId: UUID, @RequestBody budget: Int) = projects.findById(projectId).map { it.budget = budget }

    @GetMapping("/{projectId}/public")
    fun teaser(@PathVariable projectId: UUID) = projects.findById(projectId).map { it.name }
}

@RestController
class StaffController(private val projects: ProjectRepository) {
    @DeleteMapping("/api/admin/projects/{projectId}")
    fun remove(@PathVariable projectId: UUID) = projects.deleteById(projectId)

    @GetMapping("/api/support/projects/{projectId}")
    fun inspect(@PathVariable projectId: UUID) = projects.findById(projectId)
}
