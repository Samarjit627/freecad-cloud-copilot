#!/bin/bash

# Enhanced deployment script for FreeCAD Cloud Copilot service
# This script builds and deploys the service to Google Cloud Run with proper error handling

set -e  # Exit on error

echo "=== Starting Enhanced Deployment of FreeCAD Cloud Copilot API ==="
echo "$(date)"

# Set project ID
PROJECT_ID="manufacturing-co-pilot-465510"
SERVICE_NAME="freecad-copilot-service"
REGION="asia-south1"

echo "Using Google Cloud Project: $PROJECT_ID"
echo "Service Name: $SERVICE_NAME"
echo "Region: $REGION"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Error: Docker is not running. Please start Docker and try again."
  exit 1
fi

# Build the Docker image with proper tagging
echo "Building Docker image..."
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME:$(date +%Y%m%d-%H%M%S)"
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
  --memory 1Gi \
  --cpu 1 \
  --min-instances 1 \
  --max-instances 10 \
  --concurrency 80 \
  --timeout 300s \
  --allow-unauthenticated

if [ $? -ne 0 ]; then
  echo "Error: Deployment to Cloud Run failed."
  exit 1
fi

# Get the URL of the deployed service
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')

echo "=== Deployment Complete ==="
echo "Service URL: $SERVICE_URL"
echo "Test the service with: curl -v $SERVICE_URL/health"
echo "$(date)"

# Test the health endpoint
echo "Testing health endpoint..."
curl -v $SERVICE_URL/health

echo ""
echo "Done!"
