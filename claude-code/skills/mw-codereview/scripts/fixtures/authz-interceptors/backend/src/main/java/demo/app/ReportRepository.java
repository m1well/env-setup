package demo.app;

import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface ReportRepository extends JpaRepository<Report, UUID> {
    boolean existsByIdAndOwnerName(UUID id, String ownerName);
}
