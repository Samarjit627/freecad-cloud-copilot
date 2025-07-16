# FreeCAD Cloud Copilot - Cloud Configuration

This document explains how to configure the cloud service endpoints for the FreeCAD Cloud Copilot.

## Cloud Configuration File

The cloud configuration is stored in a JSON file called `cloud_config.json` in the root directory of the project. This file allows you to customize the cloud service endpoints without modifying the code.

### Example Configuration

```json
{
  "cloud_api_url": "https://freecad-copilot-service-501520737043.asia-south1.run.app",
  "cloud_api_key": "",
  "default_analysis_endpoint": "/api/analysis/cad",
  "fallback_endpoints": [
    "/api/analysis",
    "/api/cad-analysis",
    "/api/v1/analysis",
    "/analysis",
    "/cad-analysis",
    "/analyze"
  ],
  "use_cloud_backend": true,
  "enable_auto_analysis": true,
  "enable_debug_mode": true
}
```

### Configuration Options

- `cloud_api_url`: The base URL of the cloud service
- `cloud_api_key`: The API key for the cloud service (if required)
- `default_analysis_endpoint`: The primary endpoint to use for CAD analysis
- `fallback_endpoints`: A list of alternative endpoints to try if the default endpoint fails
- `use_cloud_backend`: Whether to use the cloud backend (true) or local analysis only (false)
- `enable_auto_analysis`: Whether to automatically analyze CAD models when loaded
- `enable_debug_mode`: Whether to enable debug logging

## Troubleshooting Cloud Connectivity

If you're experiencing issues with cloud connectivity, try the following:

1. **Check the cloud service status**: Make sure the cloud service is running and accessible by visiting the health endpoint in a browser: `https://your-cloud-service-url/health`

2. **Verify the correct endpoint**: The default endpoint for CAD analysis is `/api/analysis/cad`. If your cloud service uses a different endpoint, update the `default_analysis_endpoint` in the configuration file.

3. **Enable debug mode**: Set `enable_debug_mode` to `true` in the configuration file to see more detailed logs about the cloud communication.

4. **Check API key**: If your cloud service requires an API key, make sure it's correctly set in the configuration file.

5. **Try fallback endpoints**: If the default endpoint isn't working, the client will automatically try the fallback endpoints listed in the configuration file.

## Cloud Service API Structure

The cloud service API is structured as follows:

- `/health`: Health check endpoint (GET)
- `/api/analysis/cad`: CAD analysis endpoint (POST)
- `/api/chat`: Chat endpoint (POST)
- `/api/agents`: Agents endpoint (POST)

## Local Fallback

If the cloud service is unavailable, the FreeCAD Cloud Copilot will automatically fall back to local analysis. The local analysis provides basic functionality but may not have all the features of the cloud-based analysis.

To disable cloud analysis and use local analysis only, set `use_cloud_backend` to `false` in the configuration file.
