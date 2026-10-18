package demo.app;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.util.Map;
import java.util.UUID;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;
import org.springframework.web.servlet.HandlerMapping;

@Component
public class ReportAccessInterceptor implements HandlerInterceptor {
    private final ReportRepository reports;

    public ReportAccessInterceptor(ReportRepository reports) {
        this.reports = reports;
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        Map<?, ?> variables = (Map<?, ?>) request.getAttribute(HandlerMapping.URI_TEMPLATE_VARIABLES_ATTRIBUTE);
        String user = SecurityContextHolder.getContext().getAuthentication().getName();
        if (reports.existsByIdAndOwnerName(UUID.fromString((String) variables.get("reportId")), user)) {
            return true;
        }
        response.setStatus(HttpServletResponse.SC_FORBIDDEN);
        return false;
    }
}
