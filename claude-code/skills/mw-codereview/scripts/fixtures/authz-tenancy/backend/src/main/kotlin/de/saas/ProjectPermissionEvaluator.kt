package de.saas

import org.springframework.security.access.PermissionEvaluator
import org.springframework.security.core.Authentication
import java.io.Serializable

class ProjectPermissionEvaluator(private val remote: PolicyClient) : PermissionEvaluator {
    override fun hasPermission(auth: Authentication, target: Any?, permission: Any): Boolean =
        try {
            remote.check(auth.name, target, permission)
        } catch (e: Exception) {
            true
        }

    override fun hasPermission(auth: Authentication, id: Serializable?, type: String?, permission: Any): Boolean =
        runCatching { remote.check(auth.name, id, permission) }.getOrDefault(true)
}

interface PolicyClient {
    fun check(user: String, target: Any?, permission: Any): Boolean
}
