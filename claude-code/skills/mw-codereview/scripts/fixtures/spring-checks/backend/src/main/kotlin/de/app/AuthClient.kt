package de.app

import org.springframework.http.HttpHeaders
import org.springframework.stereotype.Service
import org.springframework.web.client.RestClient

@Service
class AuthClient(builder: RestClient.Builder) {
    private val restClient = builder.build()

    fun verify(token: String, app: String): Principal? =
        restClient
            .get()
            .uri("/verify")
            .header(HttpHeaders.AUTHORIZATION, token)
            .header("X-Client-App", app)
            .retrieve()
            .body(Principal::class.java)

    fun login(code: String): String? =
        restClient
            .post()
            .uri("/login")
            .header("X-Login-Code", code)
            .retrieve()
            .body(String::class.java)

    fun status(region: String): String? =
        restClient.get().uri("/status/{region}", region).retrieve().body(String::class.java)
}

data class Principal(val name: String, val role: String)
