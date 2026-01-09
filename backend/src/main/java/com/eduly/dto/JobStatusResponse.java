/**
 * Data Transfer Object for job status API responses.
 * 
 * Contains the current state of a processing job including:
 * - Job ID and status (PENDING, PROCESSING, COMPLETED, FAILED)
 * - Current processing stage description
 * - List of generated video S3 keys
 * - Error message if processing failed
 */
package com.eduly.dto;

import com.eduly.entity.Job;

import java.util.List;

public class JobStatusResponse {
    private String jobId;
    private Job.JobStatus status;
    private String currentStage;
    private List<String> videoS3Keys;
    private String errorMessage;

    public JobStatusResponse() {
    }

    public JobStatusResponse(String jobId, Job.JobStatus status, String currentStage, List<String> videoS3Keys, String errorMessage) {
        this.jobId = jobId;
        this.status = status;
        this.currentStage = currentStage;
        this.videoS3Keys = videoS3Keys;
        this.errorMessage = errorMessage;
    }

    public String getJobId() {
        return jobId;
    }

    public void setJobId(String jobId) {
        this.jobId = jobId;
    }

    public Job.JobStatus getStatus() {
        return status;
    }

    public void setStatus(Job.JobStatus status) {
        this.status = status;
    }

    public String getCurrentStage() {
        return currentStage;
    }

    public void setCurrentStage(String currentStage) {
        this.currentStage = currentStage;
    }

    public List<String> getVideoS3Keys() {
        return videoS3Keys;
    }

    public void setVideoS3Keys(List<String> videoS3Keys) {
        this.videoS3Keys = videoS3Keys;
    }

    public String getErrorMessage() {
        return errorMessage;
    }

    public void setErrorMessage(String errorMessage) {
        this.errorMessage = errorMessage;
    }
}

