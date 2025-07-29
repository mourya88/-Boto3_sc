
# Use Java 21 runtime as the base image
FROM eclipse-temurin:21-jre

# Set the working directory inside the container
WORKDIR /app

# Copy your JAR file into the container and rename it to app.jar
COPY tykonboardingapi-1.0.jar app.jar

# Inform Docker that the container listens on port 8067
EXPOSE 8067

# Define the startup command
ENTRYPOINT ["java", "-jar", "app.jar"]
