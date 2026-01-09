/**
 * JPA entity representing a processing job in the system.
 * 
 * Tracks the lifecycle of PDF-to-video conversion jobs:
 * - Job status (PENDING, PROCESSING, COMPLETED, FAILED)
 * - Current processing stage for progress tracking
 * - S3 keys for uploaded PDFs and generated videos
 * - User email for notifications
 * - Error messages if processing fails
 * 
 * Includes automatic timestamp management for created/updated times.
 */
package com.eduly.entity;

import jakarta.persistence.*;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "jobs")
public class Job {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private String id;

    @Column(nullable = false)
    private String email;

    @Column(nullable = false)
    @Enumerated(EnumType.STRING)
    private JobStatus status = JobStatus.PENDING;

    @Column(name = "pdf_s3_key")
    private String pdfS3Key;

    @ElementCollection
    @CollectionTable(name = "job_videos", joinColumns = @JoinColumn(name = "job_id"))
    @Column(name = "video_s3_key")
    private List<String> videoS3Keys = new ArrayList<>();

    @Column(name = "current_stage")
    private String currentStage;

    @Column(name = "error_message", length = 2000)
    private String errorMessage;

    @Column(name = "created_at")
    private LocalDateTime createdAt = LocalDateTime.now();

    @Column(name = "updated_at")
    private LocalDateTime updatedAt = LocalDateTime.now();

    @PreUpdate
    public void preUpdate() {
        this.updatedAt = LocalDateTime.now();
    }

    // Constructors
    public Job() {
    }

    // Getters and Setters
    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public JobStatus getStatus() {
        return status;
    }

    public void setStatus(JobStatus status) {
        this.status = status;
    }

    public String getPdfS3Key() {
        return pdfS3Key;
    }

    public void setPdfS3Key(String pdfS3Key) {
        this.pdfS3Key = pdfS3Key;
    }

    public List<String> getVideoS3Keys() {
        return videoS3Keys;
    }

    public void setVideoS3Keys(List<String> videoS3Keys) {
        this.videoS3Keys = videoS3Keys;
    }

    public String getCurrentStage() {
        return currentStage;
    }

    public void setCurrentStage(String currentStage) {
        this.currentStage = currentStage;
    }

    public String getErrorMessage() {
        return errorMessage;
    }

    public void setErrorMessage(String errorMessage) {
        this.errorMessage = errorMessage;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }

    public enum JobStatus {
        PENDING,
        PROCESSING,
        COMPLETED,
        FAILED
    }
}

