/**
 * Service for AWS S3 operations including file uploads, downloads, and presigned URL generation.
 * 
 * Handles:
 * - Generating presigned PUT URLs for client-side PDF uploads
 * - Generating presigned GET URLs for video downloads
 * - Uploading rendered videos from the backend
 * - Downloading PDFs from S3 for processing
 * - Generating unique S3 keys for organizing uploaded files
 */
package com.eduly.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import software.amazon.awssdk.auth.credentials.DefaultCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;
import software.amazon.awssdk.services.s3.presigner.S3Presigner;
import software.amazon.awssdk.services.s3.presigner.model.PresignedPutObjectRequest;
import software.amazon.awssdk.services.s3.presigner.model.PutObjectPresignRequest;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.core.sync.ResponseTransformer;

import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.time.Duration;
import java.util.UUID;

@Service
public class S3Service {
    private final String bucketName;
    private final Region region;
    private final S3Client s3Client;
    private final S3Presigner presigner;

    public S3Service(
            @Value("${aws.s3.bucket-name}") String bucketName,
            @Value("${aws.s3.region}") String regionStr) {
        this.bucketName = bucketName;
        this.region = Region.of(regionStr);
        this.s3Client = S3Client.builder()
                .region(this.region)
                .credentialsProvider(DefaultCredentialsProvider.create())
                .build();
        this.presigner = S3Presigner.builder()
                .region(this.region)
                .credentialsProvider(DefaultCredentialsProvider.create())
                .build();
    }

    // Generate presigned PUT URL for frontend upload
    public String generatePresignedUrl(String s3Key) {
        PutObjectPresignRequest presignRequest = PutObjectPresignRequest.builder()
                .signatureDuration(Duration.ofMinutes(10))
                .putObjectRequest(b -> b
                        .bucket(bucketName)
                        .key(s3Key)
                        .contentType("application/pdf"))
                .build();

        PresignedPutObjectRequest presignedRequest = presigner.presignPutObject(presignRequest);
        return presignedRequest.url().toString();
    }

    // Upload file directly from backend (used for rendered videos)
    public String uploadFile(File file, String s3Key) {
        try (InputStream inputStream = new FileInputStream(file)) {
            PutObjectRequest putObjectRequest = PutObjectRequest.builder()
                    .bucket(bucketName)
                    .key(s3Key)
                    .contentType("video/mp4")
                    .build();

            s3Client.putObject(putObjectRequest, RequestBody.fromInputStream(inputStream, file.length()));
            return s3Key;
        } catch (Exception e) {
            throw new RuntimeException("Failed to upload file to S3: " + e.getMessage(), e);
        }
    }

    // Fixed download using ResponseTransformer.toFile
    public void downloadFile(String s3Key, File destinationFile) {
        try {
            s3Client.getObject(
                    b -> b.bucket(bucketName).key(s3Key),
                    ResponseTransformer.toFile(destinationFile.toPath())
            );
        } catch (Exception e) {
            throw new RuntimeException(
                    "Failed to download file from S3: " + e.getMessage(), e
            );
        }
    }

    

    // Generate presigned GET URL for frontend download
    public String generatePresignedDownloadUrl(String s3Key, Duration expiration) {
        software.amazon.awssdk.services.s3.model.GetObjectRequest getObjectRequest =
                software.amazon.awssdk.services.s3.model.GetObjectRequest.builder()
                        .bucket(bucketName)
                        .key(s3Key)
                        .build();

        software.amazon.awssdk.services.s3.presigner.model.PresignedGetObjectRequest presignedGetRequest =
                presigner.presignGetObject(b -> b
                        .signatureDuration(expiration)
                        .getObjectRequest(getObjectRequest));

        return presignedGetRequest.url().toString();
    }

    // Generate S3 key for storing uploaded PDFs
    public String getS3KeyForPresignedUrl(String filename, String email) {
        return String.format("pdfs/%s/%s", email, UUID.randomUUID() + "_" + filename);
    }
}
