/**
 * Web configuration for CORS (Cross-Origin Resource Sharing) settings.
 * 
 * Configures CORS to allow cross-origin requests from frontend applications.
 * Currently allows all origins, methods, and headers - should be restricted
 * to specific frontend domains in production.
 */
package com.eduly.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOrigins("*")
                .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
                .allowedHeaders("*");
    }
}

