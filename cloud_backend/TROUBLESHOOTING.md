# Troubleshooting Guide for FreeCAD Manufacturing Co-Pilot Cloud Service

This guide provides steps to diagnose and fix common issues with the cloud service deployment.

## Deployment Issues

### 503 Service Unavailable Errors

If you're experiencing 503 Service Unavailable errors, follow these steps:

1. **Check the service status:**
   ```bash
   python diagnose_cloud_service.py
   ```

2. **Check Cloud Run logs:**
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=freecad-copilot-service" --limit=50
   ```

3. **Common causes of 503 errors:**
   - Application crashes during startup
   - Memory limits exceeded
   - Missing dependencies
   - Import errors
   - Permissions issues

### Deployment Stuck or Aborted

If your deployment gets stuck or aborted, try these steps:

1. **Check Docker authentication:**
   ```bash
   gcloud auth configure-docker
   ```

2. **Verify Google Cloud authentication:**
   ```bash
   gcloud auth login
   gcloud config set project manufacturing-co-pilot-465510
   ```

3. **Try deploying the test app first:**
   ```bash
   cd test_app
   ./deploy_test_app.sh
   ```

4. **Check for Docker build issues:**
   - Build the Docker image locally first:
     ```bash
     docker build -t freecad-copilot-service .
     docker run -p 8080:8080 freecad-copilot-service
     ```
   - Test locally with: `curl http://localhost:8080/health`

## Application Issues

### Import Errors

If you're seeing import errors:

1. **Check the package structure:**
   - Ensure all directories have `__init__.py` files
   - Verify import paths in `main.py`

2. **Fix import paths:**
   - Use try/except blocks for different import scenarios
   - Consider using absolute imports

### Missing Dependencies

If dependencies are missing:

1. **Update requirements.txt:**
   - Ensure all dependencies are listed with versions
   - Include system dependencies in the Dockerfile

2. **Check for conflicting dependencies:**
   - Use `pip check` to verify dependency compatibility

## Performance Issues

If the service is slow or unresponsive:

1. **Increase resource allocation:**
   - Update the deployment script to allocate more memory/CPU
   - Adjust the number of workers in gunicorn

2. **Enable caching:**
   - Implement caching for frequent operations
   - Use memory caching for small datasets

## Testing and Verification

To verify the service is working correctly:

1. **Run the diagnostic script:**
   ```bash
   python diagnose_cloud_service.py --test-dfm
   ```

2. **Test individual endpoints:**
   ```bash
   curl -v https://[service-url]/health
   curl -v -H "X-API-Key: [your-api-key]" https://[service-url]/api/v2/analysis/dfm -d @test_payload.json
   ```

## Rollback Procedure

If you need to rollback to a previous version:

1. **List previous revisions:**
   ```bash
   gcloud run revisions list --service=freecad-copilot-service --region=asia-south1
   ```

2. **Rollback to a specific revision:**
   ```bash
   gcloud run services update-traffic freecad-copilot-service --to-revisions=REVISION_ID=100 --region=asia-south1
   ```

## Local Fallback

If the cloud service remains unavailable:

1. **Enable local fallback mode:**
   - Set `use_local_fallback: true` in `cloud_config.json`
   - Verify local fallback works with `test_local_fallback.py`

2. **Notify users:**
   - Add a notification in the FreeCAD plugin UI about cloud service status
   - Provide guidance on limitations of local mode

## Contact Support

If you continue to experience issues:

- File an issue on the GitHub repository
- Contact the development team at support@freecad-manufacturing-copilot.com
