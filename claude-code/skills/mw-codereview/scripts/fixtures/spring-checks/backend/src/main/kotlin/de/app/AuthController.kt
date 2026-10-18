package de.app

import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestHeader
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController

object ApiPaths {
    const val AUTH = "/auth"
}

@RestController
@RequestMapping(ApiPaths.AUTH)
class AuthController(private val authClient: AuthClient) {
    @PostMapping(LOGIN)
    fun login(@RequestHeader("X-Login-Code") code: String): String? = authClient.login(code)

    @GetMapping("/status")
    fun status(@RequestHeader("X-Region") region: String): String? {
        require(region in REGIONS) { "unknown region" }
        return authClient.status(region)
    }

    private companion object {
        const val LOGIN = "/login"
        val REGIONS = setOf("eu", "us")
    }
}
