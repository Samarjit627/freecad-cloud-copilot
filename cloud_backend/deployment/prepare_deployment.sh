#!/bin/bash
# Script to prepare deployment package for Google Cloud Run

# Set base directories
BASE_DIR=$(cd "$(dirname "$0")/.." && pwd)
DEPLOY_DIR="$BASE_DIR/deployment/package"

echo "=== Preparing Enhanced DFM Analysis API Deployment Package ==="
echo "Base directory: $BASE_DIR"
echo "Deployment directory: $DEPLOY_DIR"

# Create deployment directory structure
echo "Creating directory structure..."
mkdir -p "$DEPLOY_DIR/app/services"
mkdir -p "$DEPLOY_DIR/app/routers"
mkdir -p "$DEPLOY_DIR/app/models"
mkdir -p "$DEPLOY_DIR/app/tests"
mkdir -p "$DEPLOY_DIR/docs"
mkdir -p "$DEPLOY_DIR/examples"

# Copy enhanced API files
echo "Copying enhanced API files..."
cp "$BASE_DIR/app/services/enhanced_api_converter.py" "$DEPLOY_DIR/app/services/"
cp "$BASE_DIR/app/services/advanced_integration.py" "$DEPLOY_DIR/app/services/"
cp "$BASE_DIR/app/routers/enhanced_analysis.py" "$DEPLOY_DIR/app/routers/"
cp "$BASE_DIR/app/main.py" "$DEPLOY_DIR/app/"

# Copy documentation and examples
echo "Copying documentation and examples..."
cp "$BASE_DIR/docs/enhanced_api_guide.md" "$DEPLOY_DIR/docs/"
cp "$BASE_DIR/examples/enhanced_api_example.py" "$DEPLOY_DIR/examples/"

# Copy dependencies
echo "Copying dependencies..."
cp "$BASE_DIR/app/models/dfm_models.py" "$DEPLOY_DIR/app/models/"
cp "$BASE_DIR/app/services/dfm_engine.py" "$DEPLOY_DIR/app/services/"

# Copy test suite
echo "Copying test suite..."
cp "$BASE_DIR/app/tests/test_enhanced_api.py" "$DEPLOY_DIR/app/tests/"

# Create Dockerfile
echo "Creating Dockerfile..."
cat > "$DEPLOY_DIR/Dockerfile" << 'EOF'
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "${PORT:-8080}"]
EOF

# Create requirements.txt
echo "Creating requirements.txt..."
cat > "$DEPLOY_DIR/requirements.txt" << 'EOF'
fastapi>=0.68.0
uvicorn>=0.15.0
pydantic>=1.8.2
python-multipart>=0.0.5
requests>=2.26.0
EOF

# Create .dockerignore
echo "Creating .dockerignore..."
cat > "$DEPLOY_DIR/.dockerignore" << 'EOF'
Dockerfile
.dockerignore
.git
.gitignore
__pycache__/
*.py[cod]
*$py.class
*.so
.env
venv/
ENV/
.vscode/
.idea/
EOF

# Create deployment instructions
echo "Creating deployment instructions..."
cat > "$DEPLOY_DIR/DEPLOY.md" << 'EOF'
# Deployment Instructions

## 1. Build the container

```bash
cd /path/to/deployment/package
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/freecad-copilot-service
```

Replace `YOUR_PROJECT_ID` with your actual Google Cloud project ID.

## 2. Deploy to Cloud Run

```bash
gcloud run deploy freecad-copilot-service \
  --image gcr.io/YOUR_PROJECT_ID/freecad-copilot-service \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated
```

## 3. Update client configuration

After deployment, update the `cloud_config.json` file to use the enhanced API endpoints:

```json
{
  "cloud_api_url": "https://freecad-copilot-service-YOUR_PROJECT_ID.asia-south1.run.app",
  "cloud_api_key": "dev_api_key_for_testing",
  "default_analysis_endpoint": "/api/v2/analysis/dfm",
  "dfm_endpoint": "/api/v2/analysis/dfm",
  "use_dedicated_dfm_endpoint": true
}
```
EOF

echo "=== Deployment package prepared successfully ==="
echo "Deployment package is ready at: $DEPLOY_DIR"
echo "Follow the instructions in $DEPLOY_DIR/DEPLOY.md to deploy to Google Cloud Run"
