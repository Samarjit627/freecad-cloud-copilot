# FreeCAD Manufacturing Co-Pilot Unified Server

This unified server combines both Design for Manufacturability (DFM) analysis and Text-to-CAD features into a single cohesive service for the FreeCAD Manufacturing Co-Pilot.

## Features

### 1. DFM Analysis
- Analyzes CAD models for manufacturability issues
- Provides detailed recommendations for design improvements
- Estimates manufacturing costs and lead times
- Supports multiple manufacturing processes and materials

### 2. Text-to-CAD Generation
- Converts natural language descriptions into FreeCAD Python code
- Provides engineering analysis of the design requirements
- Generates parametric, well-commented FreeCAD code
- Falls back to template-based generation when AI services are unavailable

## Architecture

The unified server uses a modular architecture:

- **FastAPI Framework**: High-performance web framework for building APIs
- **Modular Routers**: Separate routers for DFM analysis and Text-to-CAD functionality
- **Service Layer**: Encapsulated business logic in service classes
- **Shared Authentication**: Common API key authentication across all endpoints
- **Unified Configuration**: Single environment configuration for all services

## API Endpoints

### DFM Analysis
- `POST /api/v2/analyze`: Analyze a CAD model for manufacturability

### Text-to-CAD
- `POST /api/v1/text-to-cad`: Generate FreeCAD code from text description

### Utility
- `GET /health`: Health check endpoint
- `GET /`: API information and documentation links

## Setup and Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.template` to `.env` and add your API keys
6. Run the server: `./run_server.sh`

## Environment Variables

- `ANTHROPIC_API_KEY`: API key for Anthropic Claude (for Text-to-CAD)
- `OPENAI_API_KEY`: API key for OpenAI (fallback for Text-to-CAD)
- `API_KEY`: API key for authenticating client requests
- `PORT`: Port to run the server on (default: 8080)
- `LOG_LEVEL`: Logging level (default: INFO)

## Deployment

The server can be deployed to Google Cloud Run using the provided `deploy.sh` script:

```bash
./deploy.sh
```

## Local Development

For local development, use the provided run script:

```bash
./run_server.sh
```

## Client Integration

Update the FreeCAD macro to point to the unified server endpoint:

```python
# For DFM Analysis
url = "http://localhost:8080/api/v2/analyze"

# For Text-to-CAD
url = "http://localhost:8080/api/v1/text-to-cad"
```

## Security

- API key authentication is required for all endpoints
- Environment variables are used for sensitive configuration
- CORS is configured to allow requests from specified origins

## Error Handling

The server includes comprehensive error handling:
- Global exception handler for unexpected errors
- Fallback mechanisms for AI service unavailability
- Detailed logging for troubleshooting
