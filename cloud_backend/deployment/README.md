# Enhanced DFM Analysis API Deployment Guide

This guide explains how to deploy the enhanced DFM analysis API to Google Cloud Run.

## Deployment Package Contents

The deployment package contains the following files:

1. **Enhanced API Components**:
   - `app/services/enhanced_api_converter.py`: Advanced CAD format converter with manufacturing analysis
   - `app/services/advanced_integration.py`: Integration manager with caching and parallel processing
   - `app/routers/enhanced_analysis.py`: API router for enhanced DFM analysis endpoints

2. **Updated Core Files**:
   - `app/main.py`: Updated to include the enhanced API router

3. **Documentation and Testing**:
   - `docs/enhanced_api_guide.md`: Comprehensive API documentation
   - `app/tests/test_enhanced_api.py`: Test suite for enhanced API components
   - `examples/enhanced_api_example.py`: Example client for testing

## Deployment Steps

### 1. Prepare the Deployment Package

Ensure all the required files are included in your deployment package:

```bash
# Create deployment directory if it doesn't exist
mkdir -p deployment/app/services
mkdir -p deployment/app/routers
mkdir -p deployment/app/models
mkdir -p deployment/docs
mkdir -p deployment/examples

# Copy enhanced API files
cp app/services/enhanced_api_converter.py deployment/app/services/
cp app/services/advanced_integration.py deployment/app/services/
cp app/routers/enhanced_analysis.py deployment/app/routers/
cp app/main.py deployment/app/

# Copy documentation and examples
cp docs/enhanced_api_guide.md deployment/docs/
cp examples/enhanced_api_example.py deployment/examples/

# Copy dependencies
cp app/models/dfm_models.py deployment/app/models/
cp app/services/dfm_engine.py deployment/app/services/

# Copy test suite
mkdir -p deployment/app/tests
cp app/tests/test_enhanced_api.py deployment/app/tests/
```

### 2. Update Dockerfile

Ensure your Dockerfile includes all the necessary dependencies:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "${PORT:-8080}"]
```

### 3. Update Requirements

Make sure your `requirements.txt` includes all necessary dependencies:

```
fastapi>=0.68.0
uvicorn>=0.15.0
pydantic>=1.8.2
python-multipart>=0.0.5
requests>=2.26.0
```

### 4. Deploy to Google Cloud Run

```bash
# Build the container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/freecad-copilot-service

# Deploy to Cloud Run
gcloud run deploy freecad-copilot-service \
  --image gcr.io/YOUR_PROJECT_ID/freecad-copilot-service \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated
```

Replace `YOUR_PROJECT_ID` with your actual Google Cloud project ID.

### 5. Update Client Configuration

After deployment, update the `cloud_config.json` file to use the enhanced API endpoints:

```json
{
  "cloud_api_url": "https://freecad-copilot-service-501520737043.asia-south1.run.app",
  "cloud_api_key": "dev_api_key_for_testing",
  "default_analysis_endpoint": "/api/v2/analysis/dfm",
  "fallback_endpoints": [
    "/health"
  ],
  "dfm_endpoint": "/api/v2/analysis/dfm",
  "use_cloud_backend": true,
  "enable_auto_analysis": true,
  "enable_debug_mode": true,
  "connection_timeout": 30,
  "retry_count": 3,
  "use_dedicated_dfm_endpoint": true
}
```

## Testing the Deployment

After deployment, you can test the API using the provided example client:

```bash
python examples/enhanced_api_example.py --api-url https://freecad-copilot-service-501520737043.asia-south1.run.app
```

Or use the FreeCAD plugin with the updated configuration.

## Backward Compatibility

The deployment maintains backward compatibility with existing endpoints:
- Legacy endpoint: `/api/analysis/cad` 
- Enhanced endpoint: `/api/v2/analysis/dfm`

Both endpoints will continue to work, but the enhanced endpoint provides additional capabilities.

## Monitoring and Maintenance

After deployment, monitor the service using Google Cloud Run dashboard and logs:

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=freecad-copilot-service" --limit 50
```

## Troubleshooting

If you encounter issues:

1. Check the Cloud Run logs for errors
2. Verify all dependencies are properly installed
3. Test the API endpoints using the example client
4. Ensure the client configuration is correct
