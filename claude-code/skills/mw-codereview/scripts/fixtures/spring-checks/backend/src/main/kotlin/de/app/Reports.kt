package de.app

import org.springframework.stereotype.Component
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional
import org.springframework.web.reactive.function.client.WebClient

@Component
class BillingClient(props: BillingProperties) {
    private val webClient = WebClient.builder().baseUrl(props.baseUrl).build()

    fun push(id: String) {
        webClient.post().uri("/reports/{id}", id).retrieve().toBodilessEntity().block()
    }
}

@Service
@Transactional
class ReportService(private val billing: BillingClient, private val links: LinkRepository) {
    fun publish(id: String) {
        links.save(LinkEntity(tokenHash = id))
        billing.push(id)
    }
}
