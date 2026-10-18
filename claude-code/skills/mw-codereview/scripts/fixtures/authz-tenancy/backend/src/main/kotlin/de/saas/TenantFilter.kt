package de.saas

import jakarta.servlet.FilterChain
import jakarta.servlet.http.HttpServletRequest
import jakarta.servlet.http.HttpServletResponse
import org.springframework.security.core.context.SecurityContextHolder
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken
import org.springframework.web.filter.OncePerRequestFilter
import java.util.UUID

class TenantFilter : OncePerRequestFilter() {
    override fun doFilterInternal(request: HttpServletRequest, response: HttpServletResponse, chain: FilterChain) {
        val jwt = (SecurityContextHolder.getContext().authentication as JwtAuthenticationToken).token
        TenantContext.set(UUID.fromString(jwt.getClaimAsString("tenant_id")))
        chain.doFilter(request, response)
        TenantContext.clear()
    }
}
