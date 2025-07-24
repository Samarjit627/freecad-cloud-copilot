# FreeCAD Manufacturing Co-Pilot: Unified Architecture

This document describes the unified architecture that combines both Design for Manufacturability (DFM) analysis and Text-to-CAD features into a single cohesive system.

## Architecture Overview

The unified architecture consists of:

1. **Unified Cloud Server**: A FastAPI-based server that provides both DFM analysis and Text-to-CAD capabilities through a common API
2. **Unified Local Server**: A Python HTTP server that acts as a proxy between FreeCAD and the cloud server, with local fallback capabilities
3. **Launch Scripts**: Scripts to easily start and stop all services

## Directory Structure

```
freecad-cloud-copilot/
├── unified_server/               # Unified cloud server
│   ├── main.py                   # Main FastAPI application
│   ├── routers/                  # API route handlers
│   │   ├── dfm_analysis.py       # DFM analysis routes
│   │   └── text_to_cad.py        # Text-to-CAD routes
│   ├── services/                 # Business logic
│   │   ├── dfm_engine.py         # DFM analysis engine
│   │   └── text_to_cad_engine.py # Text-to-CAD engine
│   ├── requirements.txt          # Dependencies
│   ├── .env.template             # Environment variable template
│   ├── run_server.sh             # Script to run the server locally
│   ├── deploy.sh                 # Script to deploy to cloud
│   └── Dockerfile                # Docker configuration
├── unified_local_server.py       # Local proxy server with fallback
├── launch_unified_services.sh    # Script to launch all services
└── stop_unified_services.sh      # Script to stop all services
```

## API Endpoints

### DFM Analysis

- **Endpoint**: `/api/v2/analyze`
- **Method**: POST
- **Authentication**: API Key (X-API-Key header)
- **Request Body**:
  ```json
  {
    "user_requirements": {
      "material": "PLA",
      "target_process": "fdm_printing",
      "production_volume": 100,
      "use_advanced_dfm": true
    },
    "cad_data": {
      "geometry": { ... },
      "features": [ ... ],
      "metadata": { ... }
    }
  }
  ```
- **Response**:
  ```json
  {
    "manufacturability_score": 85.5,
    "issues": [ ... ],
    "recommendations": [ ... ],
    "cost_estimate": { ... },
    "lead_time": { ... }
  }
  ```

### Text-to-CAD

- **Endpoint**: `/api/v1/text-to-cad`
- **Method**: POST
- **Authentication**: API Key (X-API-Key header)
- **Request Body**:
  ```json
  {
    "prompt": "Create a bracket to hold a 40mm fan",
    "parameters": {
      "detail_level": "medium",
      "output_format": "freecad_python"
    }
  }
  ```
- **Response**:
  ```json
  {
    "prompt": "Create a bracket to hold a 40mm fan",
    "engineering_analysis": "...",
    "freecad_code": "...",
    "metadata": { ... }
  }
  ```

## Setup and Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/freecad-cloud-copilot.git
   cd freecad-cloud-copilot
   ```

2. Set up the unified server:
   ```bash
   cd unified_server
   cp .env.template .env
   # Edit .env to add your API keys
   ```

3. Install dependencies:
   ```bash
   cd unified_server
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Running the Services

Use the provided launch script to start both the unified server and local proxy:

```bash
./launch_unified_services.sh
```

To stop the services:

```bash
./stop_unified_services.sh
```

To launch FreeCAD with the services:

```bash
./launch_unified_services.sh --with-freecad
```

## Fallback Mechanism

The unified local server includes fallback mechanisms for both DFM analysis and Text-to-CAD functionality. If the cloud server is unavailable, the local server will use simplified local implementations to provide basic functionality.

## Environment Variables

- `ANTHROPIC_API_KEY`: API key for Anthropic Claude (for Text-to-CAD)
- `OPENAI_API_KEY`: API key for OpenAI (fallback for Text-to-CAD)
- `API_KEY`: API key for authenticating client requests (default: "test-api-key")
- `PORT`: Port to run the unified server on (default: 8080)

## Deployment

The unified server can be deployed to Google Cloud Run using the provided deployment script:

```bash
cd unified_server
./deploy.sh
```

## Benefits of the Unified Architecture

1. **Simplified Architecture**: One server to maintain instead of two
2. **Shared Resources**: Both features share common code and dependencies
3. **Unified API**: A single endpoint for all FreeCAD cloud services
4. **Easier Deployment**: Deploy once, get both features
5. **Consistent Environment**: Same environment variables and configuration
6. **Common Authentication**: Single authentication mechanism for all services
7. **Robust Fallback**: Local fallback for both features when cloud is unavailable
