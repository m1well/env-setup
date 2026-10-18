package demo.app

import org.springframework.security.access.AccessDeniedException
import org.springframework.security.access.prepost.PreAuthorize
import org.springframework.security.core.context.SecurityContextHolder
import org.springframework.stereotype.Component
import org.springframework.stereotype.Service
import java.util.UUID

@Service
class DocumentService(private val documents: DocumentRepository, private val access: DocumentAccess) {
    fun get(id: UUID, owner: UUID): Document = documents.findByIdAndOwnerId(id, owner) ?: throw NoSuchElementException()

    fun rename(id: UUID, title: String, caller: UUID): Document {
        val document = documents.findById(id).orElseThrow()
        document.title = title
        return document
    }

    fun delete(id: UUID) {
        val document = documents.findById(id).orElseThrow()
        access.assertCanDelete(document)
        documents.delete(document)
    }

    fun mine(id: UUID): Document? = documents.mine(id, currentUser())

    fun archive(id: UUID) {
        documents.findById(id).orElseThrow().title += " (archived)"
    }

    @PreAuthorize("@documentPolicy.canRead(#id, authentication)")
    fun history(id: UUID): List<String> = emptyList()

    fun classify(id: UUID): String {
        val document = documents.findById(id).orElseThrow()
        if (document.title.isBlank()) return "empty"
        if (document.title.length > 100) return "long"
        if (document.title.startsWith("draft")) return "draft"
        if (document.customerId == null) return "internal"
        if (document.title.contains("invoice")) return "invoice"
        return if (document.title.endsWith("!")) "urgent" else "plain"
    }

    private fun currentUser(): UUID = UUID.fromString(SecurityContextHolder.getContext().authentication.name)
}

@Component
class DocumentAccess {
    fun assertCanDelete(document: Document) {
        if (document.ownerId.toString() != SecurityContextHolder.getContext().authentication.name) {
            throw AccessDeniedException("not yours")
        }
    }

    fun level(document: Document): Int {
        if (document.title.isEmpty()) return 0
        if (document.customerId == null) return 1
        if (document.title.length < 10) return 2
        if (document.title.length < 50) return 3
        if (document.title.length < 100) return 4
        return if (document.title.contains("secret")) 6 else 5
    }
}
