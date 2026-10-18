package demo.app

import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Query
import org.springframework.stereotype.Repository
import java.util.UUID

@Repository
interface ProjectRepository : JpaRepository<Project, UUID> {
    fun existsByIdAndMembers_Username(id: UUID, username: String): Boolean
}

@Repository
interface DocumentRepository : JpaRepository<Document, UUID> {
    fun findByIdAndOwnerId(id: UUID, ownerId: UUID): Document?

    fun findAllByOwnerId(ownerId: UUID): List<Document>

    @Query("select d from Document d where d.id = :id and d.ownerId = :owner")
    fun mine(id: UUID, owner: UUID): Document?
}

@Repository
interface InviteRepository : JpaRepository<Invite, UUID> {
    fun findByToken(token: String): Invite?
}

@Repository
interface AppUserRepository : JpaRepository<AppUser, UUID> {
    fun findByUsername(username: String): AppUser?
}
