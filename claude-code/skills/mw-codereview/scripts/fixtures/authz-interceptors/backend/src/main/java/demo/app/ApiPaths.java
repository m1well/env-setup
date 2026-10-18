package demo.app;

public final class ApiPaths {
    public static final String REPORTS = "/api/reports";
    public static final String REPORT_EXPORT = REPORTS + "/{reportId}/export";

    private ApiPaths() {
    }
}
