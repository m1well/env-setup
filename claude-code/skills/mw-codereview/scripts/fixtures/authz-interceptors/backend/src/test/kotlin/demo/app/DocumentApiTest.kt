package demo.app

import org.junit.jupiter.api.Test
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc
import org.springframework.boot.test.context.SpringBootTest
import org.springframework.test.web.servlet.MockMvc
import org.springframework.test.web.servlet.get
import java.util.UUID

@SpringBootTest
@AutoConfigureMockMvc
class DocumentApiTest(@Autowired val mockMvc: MockMvc) {
    @Test
    fun `classifies a document`() {
        mockMvc.get("/api/documents/classified") { param("id", UUID(0, 1).toString()) }.andExpect { status { isOk() } }
    }
}
