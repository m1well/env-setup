package demo.app

import jakarta.servlet.http.HttpServletRequest
import jakarta.servlet.http.HttpServletResponse
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.security.access.AccessDeniedException
import org.springframework.security.config.annotation.web.builders.HttpSecurity
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity
import org.springframework.security.core.context.SecurityContextHolder
import org.springframework.security.web.SecurityFilterChain
import org.springframework.stereotype.Component
import org.springframework.web.servlet.HandlerInterceptor
import org.springframework.web.servlet.HandlerMapping
import org.springframework.web.servlet.config.annotation.InterceptorRegistry
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer
import java.util.UUID

@Configuration
@EnableWebSecurity
class SecurityConfig {
    @Bean
    fun chain(http: HttpSecurity): SecurityFilterChain =
        http
            .authorizeHttpRequests { auth ->
                auth.requestMatchers("/api/admin/**").hasRole("ADMIN")
                auth.requestMatchers("/api/support/**").hasAnyRole("ADMIN", "SUPPORT")
                auth.anyRequest().authenticated()
            }
            .oauth2ResourceServer { it.jwt { } }
            .build()
}

@Component
class ProjectMemberInterceptor(private val projects: ProjectRepository) : HandlerInterceptor {
    override fun preHandle(request: HttpServletRequest, response: HttpServletResponse, handler: Any): Boolean {
        val variables = request.getAttribute(HandlerMapping.URI_TEMPLATE_VARIABLES_ATTRIBUTE) as? Map<*, *>
        val id = variables?.get("projectId") as? String ?: return true
        val user = SecurityContextHolder.getContext().authentication?.name ?: return false
        if (projects.existsByIdAndMembers_Username(UUID.fromString(id), user)) {
            return true
        }
        throw AccessDeniedException("not a member of this project")
    }
}

class RequestLogInterceptor : HandlerInterceptor {
    override fun preHandle(request: HttpServletRequest, response: HttpServletResponse, handler: Any): Boolean {
        request.setAttribute("started", System.nanoTime())
        return true
    }
}

@Configuration
class WebConfig(private val memberInterceptor: ProjectMemberInterceptor) : WebMvcConfigurer {
    override fun addInterceptors(registry: InterceptorRegistry) {
        registry.addInterceptor(RequestLogInterceptor())
        registry
            .addInterceptor(memberInterceptor)
            .addPathPatterns("$PROJECTS/{projectId}", "$PROJECTS/{projectId}/**")
            .excludePathPatterns("$PROJECTS/{projectId}/public")
    }

    companion object {
        const val PROJECTS = "/api/projects"
    }
}
