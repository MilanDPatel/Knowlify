/**
 * Service for sending email notifications via AWS SES (Simple Email Service).
 * 
 * Sends HTML emails to users:
 * - Completion emails with video download links when processing succeeds
 * - Failure emails with error details when processing fails
 * 
 * Email templates are built dynamically with video URLs and error messages.
 */
package com.eduly.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import software.amazon.awssdk.auth.credentials.DefaultCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.ses.SesClient;
import software.amazon.awssdk.services.ses.model.*;

import java.util.List;

@Service
public class SESService {
    private final String fromEmail;
    private final SesClient sesClient;

    public SESService(
            @Value("${aws.ses.from-email}") String fromEmail,
            @Value("${aws.ses.region}") String regionStr) {
        this.fromEmail = fromEmail;
        Region region = Region.of(regionStr);
        this.sesClient = SesClient.builder()
                .region(region)
                .credentialsProvider(DefaultCredentialsProvider.create())
                .build();
    }

    public void sendCompletionEmail(String toEmail, List<String> videoDownloadUrls) {
        String subject = "Your Eduly Videos Are Ready!";
        String body = buildCompletionEmailBody(videoDownloadUrls);

        SendEmailRequest emailRequest = SendEmailRequest.builder()
                .source(fromEmail)
                .destination(Destination.builder().toAddresses(toEmail).build())
                .message(Message.builder()
                        .subject(Content.builder().data(subject).build())
                        .body(Body.builder()
                                .html(Content.builder().data(body).build())
                                .build())
                        .build())
                .build();

        try {
            sesClient.sendEmail(emailRequest);
        } catch (Exception e) {
            throw new RuntimeException("Failed to send completion email: " + e.getMessage(), e);
        }
    }

    public void sendFailureEmail(String toEmail, String errorMessage) {
        String subject = "Eduly Video Processing Failed";
        String body = buildFailureEmailBody(errorMessage);

        SendEmailRequest emailRequest = SendEmailRequest.builder()
                .source(fromEmail)
                .destination(Destination.builder().toAddresses(toEmail).build())
                .message(Message.builder()
                        .subject(Content.builder().data(subject).build())
                        .body(Body.builder()
                                .html(Content.builder().data(body).build())
                                .build())
                        .build())
                .build();

        try {
            sesClient.sendEmail(emailRequest);
        } catch (Exception e) {
            throw new RuntimeException("Failed to send failure email: " + e.getMessage(), e);
        }
    }

    private String buildCompletionEmailBody(List<String> videoDownloadUrls) {
        StringBuilder html = new StringBuilder();
        html.append("<html><body>");
        html.append("<h2>Your educational videos are ready!</h2>");
        html.append("<p>We've successfully processed your PDF and generated the following videos:</p>");
        html.append("<ul>");
        for (int i = 0; i < videoDownloadUrls.size(); i++) {
            html.append(String.format("<li><a href=\"%s\">Video %d</a></li>", videoDownloadUrls.get(i), i + 1));
        }
        html.append("</ul>");
        html.append("<p><strong>Note:</strong> These download links are valid for 7 days.</p>");
        html.append("<p>Thank you for using Eduly!</p>");
        html.append("</body></html>");
        return html.toString();
    }

    private String buildFailureEmailBody(String errorMessage) {
        StringBuilder html = new StringBuilder();
        html.append("<html><body>");
        html.append("<h2>Video Processing Failed</h2>");
        html.append("<p>We encountered an error while processing your PDF:</p>");
        html.append("<p style=\"color: red;\">").append(errorMessage).append("</p>");
        html.append("<p>Please try uploading your PDF again. If the problem persists, please contact support.</p>");
        html.append("<p>Thank you for using Eduly!</p>");
        html.append("</body></html>");
        return html.toString();
    }
}

