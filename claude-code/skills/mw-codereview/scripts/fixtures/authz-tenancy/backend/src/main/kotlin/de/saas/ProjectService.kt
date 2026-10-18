package de.saas

import org.springframework.cache.annotation.Cacheable
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.scheduling.annotation.Async
import org.springframework.scheduling.annotation.Scheduled
import org.springframework.security.access.prepost.PostAuthorize
import org.springframework.security.access.prepost.PostFilter
import org.springframework.security.access.prepost.PreAuthorize
import org.springframework.stereotype.Service
import java.util.UUID
import java.util.concurrent.CompletableFuture

interface ProjectRepository : JpaRepository<Project, UUID>

@Service
class ProjectService(private val projects: ProjectRepository) {

    @Cacheable("projects")
    fun get(id: UUID): Project = projects.findById(id).orElseThrow()

    @PostAuthorize("returnObject.tenantId == authentication.details.tenant")
    fun update(id: UUID, name: String): Project = projects.save(get(id).apply { this.name = name })

    @PostFilter("filterObject.tenantId == authentication.details.tenant")
    fun all(): List<Project> = projects.findAll()

    @PreAuthorize("hasRole('ADMIN') or (hasRole('MANAGER') and #id != null) or hasRole('OWNER') or hasRole('AUDITOR')")
    fun archive(id: UUID) = projects.deleteById(id)

    @Async
    fun reindex(id: UUID) = get(id)

    fun export(): CompletableFuture<List<Project>> = CompletableFuture.supplyAsync { projects.findAll() }
}

@Service
class NightlyCleanup(private val projects: ProjectRepository) {
    @Scheduled(cron = "0 0 3 * * *")
    fun run() = projects.deleteAll()
}
