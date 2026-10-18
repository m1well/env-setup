package de.saas

import jakarta.servlet.http.HttpServletRequest
import org.springframework.http.HttpHeaders
import org.springframework.http.HttpRequest
import org.springframework.http.client.ClientHttpRequestExecution
import org.springframework.http.client.ClientHttpRequestInterceptor
import org.springframework.http.client.ClientHttpResponse

class RelayInterceptor(private val incoming: HttpServletRequest) : ClientHttpRequestInterceptor {
    override fun intercept(request: HttpRequest, body: ByteArray, execution: ClientHttpRequestExecution): ClientHttpResponse {
        request.headers.set(HttpHeaders.AUTHORIZATION, incoming.getHeader(HttpHeaders.AUTHORIZATION))
        return execution.execute(request, body)
    }
}
