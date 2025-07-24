#!/bin/bash
# Deploy Text-to-CAD Agent to Google Cloud Run

# Configuration
PROJECT_ID="freecad-cloud-copilot"
SERVICE_NAME="text-to-cad-agent"
REGION="us-central1"
MAX_INSTANCES=10
MEMORY="2Gi"
CPU="1"
TIMEOUT="300s"

echo "Building and deploying $SERVICE_NAME to Google Cloud Run..."

# Build and push the container
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --memory $MEMORY \
  --cpu $CPU \
  --timeout $TIMEOUT \
  --max-instances $MAX_INSTANCES \
  --set-env-vars="ANTHROPIC_API_KEY=$(cat .env | grep ANTHROPIC_API_KEY | cut -d '=' -f2)" \
  --set-env-vars="OPENAI_API_KEY=$(cat .env | grep OPENAI_API_KEY | cut -d '=' -f2)"

echo "Deployment complete!"
