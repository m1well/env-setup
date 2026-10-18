package de.saas

import java.util.UUID

object TenantContext {
    private val holder = ThreadLocal<UUID?>()

    fun set(tenant: UUID) = holder.set(tenant)

    fun current(): UUID? = holder.get()

    fun clear() = holder.remove()
}

object CurrentUser {
    private val user = InheritableThreadLocal<String?>()

    fun set(name: String) = user.set(name)
}
