/**
 * REST controller for handling PDF file uploads via presigned S3 URLs.
 * 
 * Generates presigned URLs that allow clients to upload PDFs directly to S3,
 * creating a job record to track the processing workflow. This approach
 * offloads file upload bandwidth from the backend server.
 */
package com.eduly.controller;

import com.eduly.dto.PresignedUrlResponse;
import com.eduly.entity.Job;
import com.eduly.repository.JobRepository;
import com.eduly.service.S3Service;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/upload")
// Allow CORS from frontend (you can add multiple URLs or ports if needed)
@CrossOrigin(origins = "*")
public class UploadController {

    private final S3Service s3Service;
    private final JobRepository jobRepository;

    public UploadController(S3Service s3Service, JobRepository jobRepository) {
        this.s3Service = s3Service;
        this.jobRepository = jobRepository;
    }

    @GetMapping("/presigned-url")
    public ResponseEntity<PresignedUrlResponse> getPresignedUrl(
            @RequestParam String filename,
            @RequestParam String email) {

        // Create job record
        Job job = new Job();
        job.setEmail(email);
        job.setStatus(Job.JobStatus.PENDING);
        String s3Key = s3Service.getS3KeyForPresignedUrl(filename, email);
        job.setPdfS3Key(s3Key);
        job = jobRepository.save(job);

        // Generate presigned URL using the same S3 key
        String presignedUrl = s3Service.generatePresignedUrl(s3Key);

        PresignedUrlResponse response = new PresignedUrlResponse();
        response.setJobId(job.getId());
        response.setPresignedUrl(presignedUrl);
        response.setS3Key(s3Key);

        return ResponseEntity.ok(response);
    }
}
