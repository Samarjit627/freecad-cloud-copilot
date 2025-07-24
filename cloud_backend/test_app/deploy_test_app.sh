#!/bin/bash

# Enhanced deployment script for FreeCAD Cloud Copilot test service
# This script builds and deploys a minimal test service to Google Cloud Run

set -e  # Exit on error

echo "=== Starting Deployment of Test API $(date) ==="

# Set project ID and service name
PROJECT_ID="manufacturing-co-pilot-465510"
SERVICE_NAME="freecad-test-service"
REGION="asia-south1"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

echo "Using Google Cloud Project: $PROJECT_ID"
echo "Service Name: $SERVICE_NAME"
echo "Region: $REGION"
echo "Timestamp: $TIMESTAMP"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Error: Docker is not running. Please start Docker and try again."
  exit 1
fi

# Build the Docker image for amd64 architecture
echo "Building Docker image for amd64 architecture..."
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME:$TIMESTAMP"
echo "Image name: $IMAGE_NAME"

docker buildx build --platform linux/amd64 -t $SERVICE_NAME .
if [ $? -ne 0 ]; then
  echo "Error: Docker build failed."
  exit 1
fi

# Tag the Docker image
echo "Tagging Docker image..."
docker tag $SERVICE_NAME $IMAGE_NAME
if [ $? -ne 0 ]; then
  echo "Error: Docker tag failed."
  exit 1
fi

# Push the Docker image to Google Container Registry
echo "Pushing Docker image to Google Container Registry..."
docker push $IMAGE_NAME
if [ $? -ne 0 ]; then
  echo "Error: Docker push failed. Make sure you're authenticated with Google Cloud."
  echo "Run: gcloud auth configure-docker"
  exit 1
fi

# Deploy to Cloud Run with increased memory and CPU
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 5 \
  --concurrency 80 \
  --timeout 300s \
  --allow-unauthenticated

if [ $? -ne 0 ]; then
  echo "Error: Deployment to Cloud Run failed."
  exit 1
fi

# Get the URL of the deployed service
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')

echo "=== Deployment Complete $(date) ==="
echo "Service URL: $SERVICE_URL"

# Test the health endpoint
echo "Testing health endpoint..."
curl -v $SERVICE_URL/health

echo ""
echo "Testing debug endpoint..."
curl -v $SERVICE_URL/debug

echo ""
echo "Done!"
