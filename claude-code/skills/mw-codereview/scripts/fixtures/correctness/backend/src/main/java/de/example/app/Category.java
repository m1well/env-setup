package de.example.app;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

@Entity
public class Category {
    @Id
    private String code;

    protected Category() {
    }

    public Category(String code) {
        this.code = code;
    }
}

interface CategoryRepository extends JpaRepository<Category, String> {
    Optional<Category> findByCode(String code);
}
