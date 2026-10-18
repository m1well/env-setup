package demo.app;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import java.util.UUID;

@Entity
public class Report {
    @Id
    private UUID id;
    private String ownerName;
    private String title;

    public UUID getId() {
        return id;
    }
}
