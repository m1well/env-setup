package demo.app;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class ReportWebConfig implements WebMvcConfigurer {
    private static final String[] REPORT_PATHS = {ApiPaths.REPORTS + "/{reportId}", ApiPaths.REPORTS + "/{reportId}/**"};

    private final ReportAccessInterceptor reportAccess;

    public ReportWebConfig(ReportAccessInterceptor reportAccess) {
        this.reportAccess = reportAccess;
    }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        InterceptorRegistration registration = registry.addInterceptor(reportAccess);
        registration.addPathPatterns(REPORT_PATHS);
        registration.excludePathPatterns(ApiPaths.REPORT_EXPORT);
    }
}
