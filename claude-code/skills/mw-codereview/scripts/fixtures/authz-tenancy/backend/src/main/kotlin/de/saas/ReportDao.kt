package de.saas

import org.springframework.jdbc.core.JdbcTemplate
import org.springframework.stereotype.Repository
import java.util.UUID

@Repository
class ReportDao(private val jdbc: JdbcTemplate) {

    fun invoices(number: String): List<Map<String, Any>> =
        jdbc.queryForList("select id, number from invoice where number = ?", number)

    fun scoped(tenant: UUID) {
        jdbc.execute("SET app.tenant_id = '$tenant'")
        jdbc.queryForObject("select set_config('app.tenant_id', ?, false)", String::class.java, tenant.toString())
    }
}
