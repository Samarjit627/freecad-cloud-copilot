#!/bin/bash
# Deployment script for FreeCAD Manufacturing Co-Pilot Unified Server

# Set default values
PROJECT_ID=${PROJECT_ID:-"freecad-manufacturing-copilot"}
SERVICE_NAME=${SERVICE_NAME:-"unified-server"}
REGION=${REGION:-"us-central1"}

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
else
    echo "No .env file found. Please create one from .env.template"
    exit 1
fi

# Check if required environment variables are set
if [ -z "$ANTHROPIC_API_KEY" ] || [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: Required environment variables are not set."
    echo "Please make sure ANTHROPIC_API_KEY and OPENAI_API_KEY are set in .env file."
    exit 1
fi

# Build the Docker image
echo "Building Docker image..."
docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME .

# Push the image to Google Container Registry
echo "Pushing image to Google Container Registry..."
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy to Google Cloud Run
echo "Deploying to Google Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY,OPENAI_API_KEY=$OPENAI_API_KEY,API_KEY=$API_KEY"

echo "Deployment completed successfully!"
echo "Your unified server is now available at the URL provided above."
