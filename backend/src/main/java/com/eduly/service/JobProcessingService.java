/**
 * Service that orchestrates the complete PDF-to-video processing pipeline.
 * 
 * This service runs asynchronously and handles:
 * 1. Downloading PDFs from S3
 * 2. Executing the Python processing script (breakdown, storyboard, animation)
 * 3. Monitoring the rendered videos folder for completion
 * 4. Uploading generated videos back to S3
 * 5. Sending completion/failure email notifications
 * 
 * The service updates job status and current stage throughout the process
 * to enable progress tracking via the API.
 */
package com.eduly.service;

import com.eduly.entity.Job;
import com.eduly.repository.JobRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

@Service
public class JobProcessingService {
    private static final Logger logger = LoggerFactory.getLogger(JobProcessingService.class);
    
    private final JobRepository jobRepository;
    private final S3Service s3Service;
    private final SESService sesService;
    private final String pythonScriptPath;
    private final String workingDirectory;
    private final String renderedVideosPath;
    private final int pollIntervalSeconds;
    private final int maxWaitMinutes;

    public JobProcessingService(
            JobRepository jobRepository,
            S3Service s3Service,
            SESService sesService,
            @Value("${python.processing.script-path}") String pythonScriptPath,
            @Value("${python.processing.working-directory}") String workingDirectory,
            @Value("${python.processing.rendered-videos-path}") String renderedVideosPath,
            @Value("${job.processing.poll-interval-seconds}") int pollIntervalSeconds,
            @Value("${job.processing.max-wait-minutes}") int maxWaitMinutes) {
        this.jobRepository = jobRepository;
        this.s3Service = s3Service;
        this.sesService = sesService;
        this.pythonScriptPath = pythonScriptPath;
        this.workingDirectory = workingDirectory;
        this.renderedVideosPath = renderedVideosPath;
        this.pollIntervalSeconds = pollIntervalSeconds;
        this.maxWaitMinutes = maxWaitMinutes;
    }

    @Async
    public void processJob(String jobId) {
        Job job = jobRepository.findById(jobId)
                .orElseThrow(() -> new RuntimeException("Job not found: " + jobId));

        try {
            // Update status to PROCESSING
            job.setStatus(Job.JobStatus.PROCESSING);
            job.setCurrentStage("Downloading PDF from S3");
            jobRepository.save(job);

            // Download PDF from S3 to a stable local path (inside project directory)
            Path tempDir = Paths.get("tmp");
            try {
                Files.createDirectories(tempDir);
            } catch (IOException e) {
                logger.warn("Could not create tmp directory {}, falling back to system temp", tempDir, e);
            }

            File tempPdfFile;
            if (Files.exists(tempDir)) {
                tempPdfFile = tempDir.resolve("eduly_" + jobId + ".pdf").toFile();
            } else {
                // Fallback to system temp if we couldn't create our own
                tempPdfFile = File.createTempFile("eduly_", ".pdf");
            }
            try {
                logger.info("Downloading PDF from S3: {}", job.getPdfS3Key());
                s3Service.downloadFile(job.getPdfS3Key(), tempPdfFile);
                logger.info("PDF downloaded successfully");

                // Update stage
                job.setCurrentStage("Running Python processing pipeline");
                jobRepository.save(job);

                // Run Python script
                logger.info("Starting Python processing script");
                runPythonScript(tempPdfFile.getAbsolutePath());
                logger.info("Python processing completed");

                // Monitor rendered videos folder
                job.setCurrentStage("Monitoring video generation");
                jobRepository.save(job);

                List<File> videoFiles = waitForVideos(maxWaitMinutes);
                logger.info("Found {} video files", videoFiles.size());

                if (videoFiles.isEmpty()) {
                    throw new RuntimeException("No videos were generated");
                }

                // Upload videos to S3
                job.setCurrentStage("Uploading videos to S3");
                jobRepository.save(job);

                List<String> videoS3Keys = new ArrayList<>();
                List<String> videoDownloadUrls = new ArrayList<>();

                for (File videoFile : videoFiles) {
                    String videoS3Key = String.format("videos/%s/%s", jobId, videoFile.getName());
                    s3Service.uploadFile(videoFile, videoS3Key);
                    videoS3Keys.add(videoS3Key);
                    
                    // Generate presigned download URL (7 days)
                    String downloadUrl = s3Service.generatePresignedDownloadUrl(
                            videoS3Key, Duration.ofDays(7));
                    videoDownloadUrls.add(downloadUrl);
                    
                    logger.info("Uploaded video: {} -> {}", videoFile.getName(), videoS3Key);
                }

                // Update job with video S3 keys
                job.setVideoS3Keys(videoS3Keys);
                job.setStatus(Job.JobStatus.COMPLETED);
                job.setCurrentStage("Completed");
                jobRepository.save(job);

                // Send completion email
                logger.info("Sending completion email to: {}", job.getEmail());
                sesService.sendCompletionEmail(job.getEmail(), videoDownloadUrls);
                logger.info("Completion email sent successfully");

            } finally {
                // Clean up temporary PDF file
                if (tempPdfFile.exists()) {
                    tempPdfFile.delete();
                }
            }

        } catch (Exception e) {
            logger.error("Error processing job {}: {}", jobId, e.getMessage(), e);
            job.setStatus(Job.JobStatus.FAILED);
            job.setErrorMessage(e.getMessage());
            job.setCurrentStage("Failed");
            jobRepository.save(job);

            // Send failure email
            try {
                sesService.sendFailureEmail(job.getEmail(), e.getMessage());
            } catch (Exception emailError) {
                logger.error("Failed to send failure email: {}", emailError.getMessage());
            }
        }
    }

    private void runPythonScript(String pdfPath) throws IOException, InterruptedException {
        Path scriptPath = Paths.get(pythonScriptPath);
        if (!Files.exists(scriptPath)) {
            throw new IOException("Python script not found: " + pythonScriptPath);
        }

        Path workingDir = Paths.get(workingDirectory);
        if (!Files.exists(workingDir)) {
            throw new IOException("Working directory not found: " + workingDirectory);
        }

        // Build command: python -u process_pdf.py <pdf_path>
        // -u flag makes Python output unbuffered so we see logs in real-time
        List<String> command = new ArrayList<>();
        command.add("/Users/milanpatel/Desktop/Knowlify/AgenticApproach/.venv/bin/python");
        command.add("-u"); // Unbuffered output for real-time logging

        // Use absolute path to script
        if (scriptPath.isAbsolute()) {
            command.add(scriptPath.toString());
        } else {
            Path resolvedScriptPath = workingDir.resolve(scriptPath);
            command.add(resolvedScriptPath.toString());
        }
        command.add(pdfPath);

        ProcessBuilder processBuilder = new ProcessBuilder(command);
        processBuilder.directory(workingDir.toFile());
        processBuilder.redirectErrorStream(true); // Combine stderr into stdout
        
        // Set environment variables (inherit from current process)
        processBuilder.environment().putAll(System.getenv());
        // Force Python to be unbuffered via environment variable as well
        processBuilder.environment().put("PYTHONUNBUFFERED", "1");

        logger.info("Executing command: {} in directory: {}", command, workingDir);
        Process process = processBuilder.start();

        // Read output in a separate thread so it doesn't block
        // This allows us to see logs in real-time while the process runs
        StringBuilder outputBuffer = new StringBuilder();
        Thread outputReader = new Thread(() -> {
            try (var reader = new java.io.BufferedReader(
                    new java.io.InputStreamReader(process.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    outputBuffer.append(line).append("\n");
                    // Log immediately so we see output in real-time
                    logger.info("[Python] {}", line);
                }
            } catch (IOException e) {
                logger.error("[Python ERR] Error reading output: {}", e.getMessage());
            }
        });
        outputReader.setDaemon(true);
        outputReader.start();

        // Wait for process to complete with timeout
        boolean finished = process.waitFor(60, TimeUnit.MINUTES);
        if (!finished) {
            logger.error("[Python ERR] Process timed out after 60 minutes. Terminating...");
            process.destroyForcibly();
            // Wait a bit for the output reader to finish
            outputReader.join(2000);
            throw new RuntimeException("Python script timed out after 60 minutes");
        }

        // Wait for output reader to finish (should be quick since process is done)
        outputReader.join(1000);

        int exitCode = process.exitValue();
        if (exitCode != 0) {
            logger.error("[Python ERR] Process exited with code: {}\nOutput:\n{}", exitCode, outputBuffer.toString());
            throw new RuntimeException("Python script failed with exit code: " + exitCode + 
                    ". Check logs above for details.");
        } else {
            logger.info("[Python] Process completed successfully");
        }
    }

    private List<File> waitForVideos(int maxWaitMinutes) throws InterruptedException {
        Path videosDir = Paths.get(renderedVideosPath);
        
        // Ensure directory exists
        try {
            Files.createDirectories(videosDir);
        } catch (IOException e) {
            logger.warn("Could not create videos directory: {}", e.getMessage());
        }

        long startTime = System.currentTimeMillis();
        long maxWaitMillis = maxWaitMinutes * 60L * 1000L;
        int lastFileCount = 0;

        while (System.currentTimeMillis() - startTime < maxWaitMillis) {
            List<File> videoFiles = getVideoFiles(videosDir.toFile());
            
            if (!videoFiles.isEmpty() && videoFiles.size() == lastFileCount) {
                // Files haven't changed, wait a bit more to ensure they're done
                Thread.sleep(pollIntervalSeconds * 1000L * 2);
                videoFiles = getVideoFiles(videosDir.toFile());
                if (videoFiles.size() == lastFileCount) {
                    // Still no change, assume processing is complete
                    logger.info("Video files stabilized at {} files", videoFiles.size());
                    return videoFiles;
                }
            }
            
            lastFileCount = videoFiles.size();
            Thread.sleep(pollIntervalSeconds * 1000L);
        }

        // Return whatever files we have
        return getVideoFiles(videosDir.toFile());
    }

    private List<File> getVideoFiles(File directory) {
        List<File> videoFiles = new ArrayList<>();
        if (!directory.exists() || !directory.isDirectory()) {
            return videoFiles;
        }

        File[] files = directory.listFiles((dir, name) -> 
                name.toLowerCase().endsWith(".mp4"));
        
        if (files != null) {
            for (File file : files) {
                if (file.isFile() && file.length() > 0) {
                    videoFiles.add(file);
                }
            }
        }

        return videoFiles;
    }
}

