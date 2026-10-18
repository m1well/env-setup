package de.app

import org.springframework.beans.factory.annotation.Value
import org.springframework.boot.context.properties.ConfigurationProperties
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.web.client.RestClient

@ConfigurationProperties("app.billing")
data class BillingProperties(val baseUrl: String = "")

@Configuration
class HttpConfig(@Value("\${app.auth-server.url}") private val authUrl: String) {
    @Bean
    fun restClientBuilder(): RestClient.Builder = RestClient.builder().baseUrl(authUrl)
}
