package de.praxis

import jakarta.servlet.http.HttpServletResponse
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.security.config.annotation.web.builders.HttpSecurity
import org.springframework.security.config.annotation.web.invoke
import org.springframework.security.web.SecurityFilterChain
import org.springframework.security.web.header.writers.XXssProtectionHeaderWriter

@Configuration
class SecurityConfig {
    @Bean
    fun chain(http: HttpSecurity): SecurityFilterChain {
        http {
            authorizeHttpRequests { authorize(anyRequest, authenticated) }
            headers { xssProtection { headerValue = XXssProtectionHeaderWriter.HeaderValue.ENABLED_MODE_BLOCK } }
        }
        return http.build()
    }

    fun legacy(response: HttpServletResponse) {
        response.setHeader("X-XSS-Protection", "1; mode=block")
        response.setHeader("X-XSS-Protection", "0")
    }
}
