package de.praxis

import jakarta.servlet.http.HttpServletRequest
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*

const val TOTAL_HEADER = "X-Total-Count"
const val TENANT_HEADER = "X-Tenant-Id"

@RestController
@RequestMapping("/api/termine")
class HeaderController {

    @GetMapping
    fun list(@RequestHeader(TENANT_HEADER) tenant: String, @RequestHeader userId: String,
             request: HttpServletRequest): ResponseEntity<List<String>> {
        val ip = request.getHeader("X-Forwarded-For")
        val requestId = request.getHeader("X-Request-ID")
        return ResponseEntity.ok().header(TOTAL_HEADER, "0").header("X-Frame-Options", "DENY").body(listOf(tenant, userId, ip, requestId))
    }

    @GetMapping("/suche")
    fun search(@RequestParam params: Map<String, String>, @RequestHeader("Accept-Language") lang: String) = params["email"]
}
