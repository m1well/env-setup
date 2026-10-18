package de.example.app;

import java.util.List;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

@Component
public class CategorySeed {
    public static final int MAX_ITEMS = 20;
    static final int MAX_RETRIES = 3;

    private final CategoryRepository categoryRepository;

    public CategorySeed(CategoryRepository categoryRepository) {
        this.categoryRepository = categoryRepository;
    }

    @EventListener(ApplicationReadyEvent.class)
    public void seed() {
        for (String code : List.of("books", "music")) {
            for (int i = 0; i < MAX_RETRIES; i++) {
                categoryRepository.findByCode(code).orElseGet(() -> categoryRepository.save(new Category(code)));
            }
        }
    }
}
