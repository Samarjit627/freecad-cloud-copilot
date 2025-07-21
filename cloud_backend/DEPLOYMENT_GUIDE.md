# FreeCAD Manufacturing Co-Pilot Cloud Backend Deployment Guide

This guide walks through deploying the FreeCAD Manufacturing Co-Pilot backend to Google Cloud Run.

## Prerequisites

1. [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed
2. [Docker](https://docs.docker.com/get-docker/) installed
3. Google Cloud account with billing enabled
4. OpenAI API key

## Step 1: Set Up Google Cloud Project

```bash
# Login to Google Cloud
gcloud auth login

# Create a new project (or use an existing one)
gcloud projects create freecad-copilot --name="FreeCAD Manufacturing Co-Pilot"

# Set the project as active
gcloud config set project freecad-copilot

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

## Step 2: Create Docker Repository

```bash
# Create a Docker repository in Artifact Registry
gcloud artifacts repositories create freecad-copilot-repo \
    --repository-format=docker \
    --location=asia-south1 \
    --description="Docker repository for FreeCAD Manufacturing Co-Pilot"

# Configure Docker to use Google Cloud as a registry
gcloud auth configure-docker asia-south1-docker.pkg.dev
```

## Step 3: Configure Environment Variables

1. Copy `.env.example` to `.env` and fill in your actual values:

```bash
cp .env.example .env
```

2. Edit the `.env` file with your actual API keys and configuration.

## Step 4: Build and Push the Docker Image

```bash
# Build the Docker image
docker build -t freecad-copilot-backend .

# Tag the image for Google Cloud Artifact Registry
docker tag freecad-copilot-backend asia-south1-docker.pkg.dev/freecad-copilot/freecad-copilot-repo/backend:v1

# Push the image to Google Cloud
docker push asia-south1-docker.pkg.dev/freecad-copilot/freecad-copilot-repo/backend:v1
```

## Step 5: Deploy to Cloud Run

```bash
# Deploy the container to Cloud Run
gcloud run deploy freecad-copilot-backend \
    --image=asia-south1-docker.pkg.dev/freecad-copilot/freecad-copilot-repo/backend:v1 \
    --platform=managed \
    --region=asia-south1 \
    --allow-unauthenticated \
    --port=8080
```

## Step 6: Set Environment Variables in Cloud Run

```bash
# Set environment variables securely in Cloud Run
gcloud run services update freecad-copilot-backend \
    --region=asia-south1 \
    --set-env-vars="OPENAI_API_KEY=your_openai_api_key,API_KEY=your_secure_api_key"
```

## Step 7: Test the Deployment

After deployment, Cloud Run will provide a URL for your service. You can test it with:

```bash
# Test the root endpoint
curl https://freecad-copilot-backend-xxxxx.run.app/

# Test the health check endpoint
curl https://freecad-copilot-backend-xxxxx.run.app/api/health
```

## Step 8: Update FreeCAD Frontend

Update your FreeCAD macro to point to the new Cloud Run URL:

```python
# In your FreeCAD macro
CLOUD_API_URL = "https://freecad-copilot-backend-xxxxx.run.app"
API_KEY = "your_secure_api_key"

# Example API call
def call_cloud_api(endpoint, data):
    headers = {"X-API-Key": API_KEY}
    response = requests.post(f"{CLOUD_API_URL}{endpoint}", json=data, headers=headers)
    return response.json()
```

## Monitoring and Scaling

- **View logs**: `gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=freecad-copilot-backend"`
- **View metrics**: Visit the Google Cloud Console > Cloud Run > freecad-copilot-backend > Metrics

## Updating the Deployment

When you make changes to your code:

1. Build a new Docker image with an incremented tag (e.g., v2)
2. Push the new image to Artifact Registry
3. Update the Cloud Run service with the new image

```bash
# Deploy the updated container
gcloud run deploy freecad-copilot-backend \
    --image=asia-south1-docker.pkg.dev/freecad-copilot/freecad-copilot-repo/backend:v2 \
    --platform=managed \
    --region=asia-south1
```

## Security Considerations

1. Restrict the API key to specific IP addresses if possible
2. Consider implementing more robust authentication for production use
3. Set up Cloud Armor for additional protection
4. Configure appropriate IAM permissions for the service
