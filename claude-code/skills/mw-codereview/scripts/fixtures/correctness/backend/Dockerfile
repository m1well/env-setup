FROM eclipse-temurin:21-jre
ENV TZ=Europe/Berlin
COPY build/libs/app.jar /app.jar
ENTRYPOINT ["java", "-jar", "/app.jar"]
