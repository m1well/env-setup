package demo.app

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.Id
import jakarta.persistence.JoinColumn
import jakarta.persistence.ManyToOne
import jakarta.persistence.OneToMany
import jakarta.persistence.Table
import jakarta.persistence.Version
import java.util.UUID

@Entity
@Table(name = "app_user")
class AppUser(@Id val id: UUID, val username: String)

@Entity
class Project(
    @Id val id: UUID,
    val ownerId: UUID,
    var customerId: UUID?,
    var name: String,
    var budget: Int?,
    var leadId: UUID?,
    @OneToMany(mappedBy = "project") val members: MutableSet<ProjectMember> = mutableSetOf(),
)

@Entity
@Table(name = "project_member")
class ProjectMember(
    @Id val id: UUID,
    @ManyToOne @JoinColumn(name = "project_id") val project: Project,
    val username: String,
)

@Entity
@Table(name = "team_member")
class TeamMember(@Id val id: UUID, val name: String)

@Entity
class Document(
    @Id val id: UUID,
    val projectId: UUID,
    val ownerId: UUID,
    var customerId: UUID?,
    var title: String,
) {
    @Column(name = "version")
    private var token: String = UUID.randomUUID().toString()

    @Version
    private var lock: Long = 0
}

@Entity
class Invite(@Id val id: UUID, val projectId: UUID, var token: String = UUID.randomUUID().toString())
