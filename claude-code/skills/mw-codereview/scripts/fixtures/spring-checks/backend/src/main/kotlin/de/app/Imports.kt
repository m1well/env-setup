package de.app

import org.springframework.stereotype.Service
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestParam
import org.springframework.web.bind.annotation.RestController
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.time.Duration

@Service
class ImportService {
    private val http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(3)).build()

    fun fetch(source: String): String {
        val request = HttpRequest.newBuilder(URI.create(source)).GET().build()
        return http.send(request, HttpResponse.BodyHandlers.ofString()).body()
    }

    fun shared(link: String): String = link.uppercase()
}

@RestController
class ImportController(private val imports: ImportService) {
    @PostMapping("/api/import")
    fun import(@RequestParam url: String): String = imports.fetch(url)

    @GetMapping("/api/share")
    fun share(@RequestParam link: String): String = imports.shared(link)
}
