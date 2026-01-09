# ManiFlow Backend

A comprehensive system for converting academic PDFs into animated educational videos using AI-powered document analysis and Manim animation generation.

## Project Overview

ManiFlow Backend consists of two main components:
1. **Backend API** (Java/Spring Boot) - RESTful API for managing PDF uploads, job processing, and video delivery
2. **AgenticApproach** (Python) - AI-powered pipeline that breaks down PDFs into topics, generates storyboards, and creates Manim animations

## Project Structure

```
knowlify-backend/
├── backend/                    # Spring Boot REST API
│   ├── src/main/java/com/eduly/
│   │   ├── config/             # Configuration classes (async, CORS)
│   │   ├── controller/      # REST controllers (Job, Upload)
│   │   ├── dto/             # Data Transfer Objects
│   │   ├── entity/          # JPA entities (Job)
│   │   ├── repository/      # JPA repositories
│   │   └── service/         # Business logic (JobProcessing, S3, SES)
│   └── src/main/resources/
│       └── application.properties  # Application configuration
│
└── AgenticApproach/          # Python AI processing pipeline
    ├── src/maniflow/         # Main Python package
    │   ├── client.py         # Animation and breakdown clients
    │   ├── models.py         # Pydantic data models
    │   └── prompts/          # AI prompts for document processing
    └── examples/             # Example scripts and workspace
        ├── process_pdf.py    # Main PDF processing script
        └── agent_workspace/  # Manim workspace with docs and rendered videos
```

## Components

### Backend (Java/Spring Boot)

The backend provides a RESTful API for:
- **PDF Upload**: Generate presigned S3 URLs for secure file uploads
- **Job Management**: Track processing jobs from upload to completion
- **Video Delivery**: Upload rendered videos to S3 and provide download URLs
- **Email Notifications**: Send completion/failure emails via AWS SES

**Key Files:**
- `JobController.java` - Job status and processing endpoints
- `UploadController.java` - Presigned URL generation for PDF uploads
- `JobProcessingService.java` - Orchestrates the PDF-to-video pipeline
- `S3Service.java` - AWS S3 operations (upload, download, presigned URLs)
- `SESService.java` - AWS SES email notifications

### AgenticApproach (Python)

The Python pipeline processes PDFs through three stages:

1. **Breakdown**: Analyzes PDFs and extracts atomic, self-contained topics
2. **Storyboard**: Creates visual storyboards for each topic with narration
3. **Animation**: Generates Manim code and renders educational videos

**Key Files:**
- `maniflow/client.py` - `ManiflowBreakdownClient` and `ManiflowAnimationClient`
- `maniflow/models.py` - Data models (Breakdown, AtomicTopic, TopicStoryboard, etc.)
- `maniflow/prompts/` - AI prompts for each processing stage
- `examples/process_pdf.py` - Main entry point for PDF processing

## Prerequisites

### Backend Requirements
- Java 17+
- Maven 3.6+
- PostgreSQL 12+
- AWS Account with:
  - S3 bucket configured
  - SES service configured (for email notifications)
  - IAM credentials with S3 and SES permissions

### Python Requirements
- Python 3.12+
- `uv` package manager (recommended) or `pip`
- LaTeX distribution (for Manim text rendering)
- AWS credentials configured (for S3 access if needed)

## Setup Instructions

### 1. Backend Setup

#### Database Configuration
1. Create a PostgreSQL database:
   ```sql
   CREATE DATABASE eduly;
   ```

2. Update `backend/src/main/resources/application.properties`:
   ```properties
   spring.datasource.url=jdbc:postgresql://localhost:5432/eduly
   spring.datasource.username=your_username
   spring.datasource.password=your_password
   ```

#### AWS Configuration
1. Set up AWS credentials (via `~/.aws/credentials` or environment variables)
2. Update `application.properties`:
   ```properties
   aws.s3.bucket-name=your-bucket-name
   aws.s3.region=us-east-1
   aws.ses.region=us-east-1
   aws.ses.from-email=your-email@example.com
   ```

#### Python Script Paths
Update the Python processing paths in `application.properties`:
```properties
python.processing.script-path=/absolute/path/to/AgenticApproach/examples/process_pdf.py
python.processing.working-directory=/absolute/path/to/AgenticApproach/examples
python.processing.rendered-videos-path=/absolute/path/to/AgenticApproach/examples/agent_workspace/rendered_videos
```

#### Build and Run
```bash
cd backend
mvn clean install
mvn spring-boot:run
```

The API will be available at `http://localhost:8080`

### 2. Python Pipeline Setup

#### Install Dependencies
Using `uv` (recommended):
```bash
cd AgenticApproach
uv sync
```

Or using `pip`:
```bash
cd AgenticApproach
pip install -r examples/requirements.txt
```

#### Environment Variables
Create a `.env` file in `AgenticApproach/examples/`:
```env
GOOGLE_API_KEY=your_google_gemini_api_key
```

#### Verify Setup
Test the processing script:
```bash
cd AgenticApproach/examples
python process_pdf.py path/to/test.pdf
```

## API Endpoints

### Upload PDF
```http
GET /api/v1/upload/presigned-url?filename=document.pdf&email=user@example.com
```
Returns a presigned S3 URL and job ID for uploading the PDF.

### Start Processing
```http
POST /api/v1/jobs/{jobId}/start
```
Starts the async processing pipeline for a job.

### Get Job Status
```http
GET /api/v1/jobs/{jobId}
```
Returns the current status, stage, and video S3 keys for a job.

## Workflow

1. **Upload**: Frontend requests presigned URL → Uploads PDF to S3
2. **Start Processing**: Backend receives start request → Creates job record
3. **Processing Pipeline**:
   - Download PDF from S3
   - Run Python script (`process_pdf.py`) which:
     - Breaks down PDF into atomic topics
     - Generates storyboards for each topic
     - Creates Manim animations with voiceover
   - Monitor rendered videos folder
   - Upload videos to S3
4. **Completion**: Update job status → Send email with video download URLs

## Configuration

### Backend Configuration
- `server.port`: API server port (default: 8080)
- `job.processing.poll-interval-seconds`: How often to check for videos (default: 2)
- `job.processing.max-wait-minutes`: Maximum wait time for video generation (default: 60)

### Python Configuration
The Python script uses Google Gemini API for:
- Document breakdown and topic extraction
- Storyboard generation
- Manim code generation (via coding agent)

Model configuration is in `process_pdf.py` (default: `gemini-3-pro-preview`).

## Development

### Backend Development
- Uses Spring Boot 3.2.0
- JPA/Hibernate for database operations
- Async processing with `@Async` for job processing
- Lombok for reducing boilerplate

### Python Development
- Uses `uv` for dependency management
- Pydantic for data validation
- DeepAgents for coding agent functionality
- Manim for animation rendering

## Troubleshooting

### Backend Issues
- **Database connection errors**: Verify PostgreSQL is running and credentials are correct
- **S3 upload failures**: Check AWS credentials and bucket permissions
- **Python script not found**: Verify paths in `application.properties` are absolute and correct

### Python Issues
- **Manim rendering errors**: Ensure LaTeX is installed and in PATH
- **API key errors**: Verify `GOOGLE_API_KEY` is set in environment
- **Import errors**: Run `uv sync` or `pip install -r requirements.txt`
