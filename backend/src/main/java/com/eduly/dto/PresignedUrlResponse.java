/**
 * Data Transfer Object for presigned URL API responses.
 * 
 * Contains the presigned S3 URL for uploading a PDF, along with
 * the associated job ID and S3 key for tracking the upload.
 */
package com.eduly.dto;

public class PresignedUrlResponse {
    private String jobId;
    private String presignedUrl;
    private String s3Key;

    public PresignedUrlResponse() {
    }

    public PresignedUrlResponse(String jobId, String presignedUrl, String s3Key) {
        this.jobId = jobId;
        this.presignedUrl = presignedUrl;
        this.s3Key = s3Key;
    }

    public String getJobId() {
        return jobId;
    }

    public void setJobId(String jobId) {
        this.jobId = jobId;
    }

    public String getPresignedUrl() {
        return presignedUrl;
    }

    public void setPresignedUrl(String presignedUrl) {
        this.presignedUrl = presignedUrl;
    }

    public String getS3Key() {
        return s3Key;
    }

    public void setS3Key(String s3Key) {
        this.s3Key = s3Key;
    }
}

