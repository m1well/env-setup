package de.app

import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.security.config.annotation.web.builders.HttpSecurity
import org.springframework.security.config.http.SessionCreationPolicy
import org.springframework.security.web.SecurityFilterChain
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter

@Configuration
class SecurityConfig(private val authClient: AuthClient) {
    @Bean
    fun api(http: HttpSecurity): SecurityFilterChain {
        http
            .csrf { it.disable() }
            .sessionManagement { it.sessionCreationPolicy(SessionCreationPolicy.STATELESS) }
            .formLogin { it.disable() }
            .httpBasic { basic -> basic.disable() }
            .authorizeHttpRequests {
                it.requestMatchers("/auth/**", "/public/**", "/links/**").permitAll()
                it.anyRequest().authenticated()
            }
            .addFilterBefore(TokenFilter(authClient), UsernamePasswordAuthenticationFilter::class.java)
        return http.build()
    }
}
