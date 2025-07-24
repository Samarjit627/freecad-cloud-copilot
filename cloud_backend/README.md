# FreeCAD Manufacturing Co-Pilot Cloud Backend

This repository contains the cloud backend service for the FreeCAD Manufacturing Co-Pilot plugin, providing advanced Design for Manufacturability (DFM) analysis, cost estimation, and tool recommendations.

## Architecture Overview

The cloud backend is built with FastAPI and deployed on Google Cloud Run. It provides:

- Advanced DFM analysis with manufacturability scoring
- Cost estimation for different manufacturing processes
- Tool recommendations based on part geometry
- Batch processing capabilities for multiple parts

## Local Development

### Prerequisites

- Python 3.9+
- Docker
- Google Cloud SDK (for deployment)

### Setup Development Environment

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application locally:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
   ```

4. Access the API documentation:
   - OpenAPI UI: http://localhost:8080/docs
   - ReDoc: http://localhost:8080/redoc

### Testing

Run the diagnostic script to test the service:
```bash
python diagnose_cloud_service.py
```

Test the local fallback mechanism:
```bash
python test_local_fallback.py
```

## Deployment

### Deploy to Google Cloud Run

1. Make sure you're authenticated with Google Cloud:
   ```bash
   gcloud auth login
   gcloud config set project manufacturing-co-pilot-465510
   ```

2. Deploy using the deployment script:
   ```bash
   ./deploy.sh
   ```

### Test Deployment

After deployment, verify the service is working:
```bash
python diagnose_cloud_service.py --url https://[your-service-url] --test-dfm
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: API key for OpenAI services
- `API_KEY`: API key for securing the service endpoints
- `PORT`: Port to run the service on (default: 8080)

### Cloud Configuration

The `cloud_config.json` file in the parent directory controls:
- `use_cloud_backend`: Whether to use cloud services
- `use_local_fallback`: Whether to use local fallback when cloud is unavailable
- `cloud_api_url`: URL of the cloud service
- `cloud_api_key`: API key for authentication
- `retry_count`: Number of retries for failed requests
- `retry_delay`: Delay between retries in seconds

## Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues and solutions.

## Simplified Test App

A minimal test app is provided in the `test_app` directory to help diagnose deployment issues:
```bash
cd test_app
./deploy_test_app.sh
```

## Local Fallback Mechanism

When the cloud service is unavailable, the client can use a local fallback mechanism:

1. Set `use_local_fallback: true` in `cloud_config.json`
2. The `CloudServiceHandler` will automatically use local implementations

## Security

- All endpoints are protected with API key authentication
- Sensitive data is not logged
- Environment variables are used for secrets

## Maintenance

### Updating Dependencies

1. Update `requirements.txt` with new versions
2. Rebuild and deploy the container

### Monitoring

Monitor the service using Google Cloud Run dashboard and logs:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=freecad-copilot-service" --limit=50
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
