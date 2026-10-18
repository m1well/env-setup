package de.example.app;

import java.time.Clock;
import java.time.Duration;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import org.springframework.stereotype.Service;

@Service
public class JobTimer {
    private final Clock clock;

    public JobTimer(Clock clock) {
        this.clock = clock;
    }

    public long waitingSeconds(Job job) {
        return Duration.between(job.getQueuedAt(), LocalDateTime.now(clock)).getSeconds();
    }

    public long waitingSecondsAgain(Job job) {
        LocalDateTime now = LocalDateTime.now(clock);
        return job.getQueuedAt().until(now, ChronoUnit.SECONDS);
    }
}
