package de.app

import jakarta.servlet.FilterChain
import jakarta.servlet.http.HttpServletRequest
import jakarta.servlet.http.HttpServletResponse
import org.slf4j.LoggerFactory
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken
import org.springframework.security.core.authority.SimpleGrantedAuthority
import org.springframework.security.core.context.SecurityContextHolder
import org.springframework.web.filter.OncePerRequestFilter

class TokenFilter(private val authClient: AuthClient) : OncePerRequestFilter() {
    private val log = LoggerFactory.getLogger(javaClass)

    override fun doFilterInternal(request: HttpServletRequest, response: HttpServletResponse, chain: FilterChain) {
        val token = request.getHeader("Authorization")
        val app = request.getHeader("X-Client-App") ?: "web"
        if (token != null) {
            try {
                val principal = authClient.verify(token, app)
                if (principal != null) {
                    SecurityContextHolder.getContext().authentication = UsernamePasswordAuthenticationToken(
                        principal.name, null, listOf(SimpleGrantedAuthority("ROLE_" + principal.role)),
                    )
                }
            } catch (ex: Exception) {
                log.warn("verify failed: {}", ex.message)
            }
        }
        chain.doFilter(request, response)
    }
}
