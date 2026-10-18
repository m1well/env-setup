package de.saas

import jakarta.persistence.Entity
import jakarta.persistence.Id
import org.hibernate.annotations.Filter
import org.hibernate.annotations.FilterDef
import org.hibernate.annotations.ParamDef
import java.util.UUID

@Entity
@FilterDef(name = "tenantFilter", parameters = [ParamDef(name = "tenantId", type = UUID::class)])
@Filter(name = "tenantFilter", condition = "tenant_id = :tenantId")
class Project(
    @Id val id: UUID,
    val tenantId: UUID,
    var name: String,
)
