/**
 * Data Transfer Object for job start API responses.
 * 
 * Confirms that job processing has been initiated and provides
 * the job ID for status tracking.
 */
package com.eduly.dto;

public class StartProcessingResponse {
    private String jobId;
    private String message;

    public StartProcessingResponse() {
    }

    public StartProcessingResponse(String jobId, String message) {
        this.jobId = jobId;
        this.message = message;
    }

    public String getJobId() {
        return jobId;
    }

    public void setJobId(String jobId) {
        this.jobId = jobId;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }
}

