/**
 * Main Spring Boot application entry point for the Knowlify Backend API.
 * 
 * This application provides REST endpoints for PDF upload, job management, and video processing.
 * It orchestrates the conversion of PDF documents into animated educational videos through
 * integration with the Python processing pipeline.
 */
package com.eduly;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAsync
public class EdulyApplication {
    public static void main(String[] args) {
        SpringApplication.run(EdulyApplication.class, args);
    }
}

