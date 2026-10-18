package demo.app;

import java.util.UUID;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/reports")
public class ReportController {
    private final ReportRepository reports;

    public ReportController(ReportRepository reports) {
        this.reports = reports;
    }

    @GetMapping("/{reportId}")
    public Report get(@PathVariable UUID reportId) {
        return reports.findById(reportId).orElseThrow();
    }

    @GetMapping("/{reportId}/export")
    public String export(@PathVariable UUID reportId) {
        return reports.findById(reportId).map(Report::getId).map(UUID::toString).orElseThrow();
    }
}
