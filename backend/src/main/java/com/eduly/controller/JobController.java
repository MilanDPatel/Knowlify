/**
 * REST controller for managing job processing operations.
 * 
 * Provides endpoints to:
 * - Start processing a job (triggers async PDF-to-video conversion)
 * - Get the current status and progress of a job
 * 
 * Jobs track the lifecycle of PDF processing from upload through video generation.
 */
package com.eduly.controller;

import com.eduly.dto.JobStatusResponse;
import com.eduly.dto.StartProcessingResponse;
import com.eduly.entity.Job;
import com.eduly.repository.JobRepository;
import com.eduly.service.JobProcessingService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/jobs")
public class JobController {
    private final JobRepository jobRepository;
    private final JobProcessingService jobProcessingService;

    public JobController(JobRepository jobRepository, JobProcessingService jobProcessingService) {
        this.jobRepository = jobRepository;
        this.jobProcessingService = jobProcessingService;
    }

    @PostMapping("/{jobId}/start")
    public ResponseEntity<StartProcessingResponse> startProcessing(@PathVariable String jobId) {
        Job job = jobRepository.findById(jobId)
                .orElseThrow(() -> new RuntimeException("Job not found: " + jobId));

        if (job.getStatus() != Job.JobStatus.PENDING) {
            throw new IllegalStateException("Job is not in PENDING status");
        }

        // Start async processing
        jobProcessingService.processJob(jobId);

        StartProcessingResponse response = new StartProcessingResponse();
        response.setJobId(jobId);
        response.setMessage("Processing started");

        return ResponseEntity.ok(response);
    }

    @GetMapping("/{jobId}")
    public ResponseEntity<JobStatusResponse> getJobStatus(@PathVariable String jobId) {
        Job job = jobRepository.findById(jobId)
                .orElseThrow(() -> new RuntimeException("Job not found: " + jobId));

        JobStatusResponse response = new JobStatusResponse();
        response.setJobId(job.getId());
        response.setStatus(job.getStatus());
        response.setCurrentStage(job.getCurrentStage());
        response.setVideoS3Keys(job.getVideoS3Keys());
        response.setErrorMessage(job.getErrorMessage());

        return ResponseEntity.ok(response);
    }
}

