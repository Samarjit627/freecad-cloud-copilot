# Enhanced CAD Analysis API Guide

This guide provides documentation for the enhanced CAD geometry extraction and analysis API (Part 4). The enhanced API provides advanced manufacturing intelligence, process recommendations, and batch processing capabilities while maintaining backward compatibility with existing endpoints.

## Table of Contents

1. [Overview](#overview)
2. [API Endpoints](#api-endpoints)
3. [Data Models](#data-models)
4. [Usage Examples](#usage-examples)
5. [Advanced Features](#advanced-features)
6. [Performance Considerations](#performance-considerations)

## Overview

The enhanced CAD analysis API builds upon the existing DFM analysis system to provide:

- Advanced geometric complexity analysis
- Detailed manufacturability assessment for multiple processes
- Intelligent process recommendations with cost and lead time estimates
- Batch processing capabilities for analyzing multiple parts
- Performance monitoring and caching for improved response times
- Backward compatibility with legacy endpoints

## API Endpoints

### Enhanced DFM Analysis

```
POST /api/v2/analysis/dfm
```

Performs comprehensive DFM analysis on CAD geometry with advanced manufacturing intelligence.

**Request Body:**
```json
{
  "cad_data": {
    "part_name": "example_part",
    "volume": 125000.0,
    "surface_area": 15000.0,
    "bounding_box": {
      "length": 100.0,
      "width": 50.0,
      "height": 25.0
    },
    "center_of_mass": {
      "x": 50.0,
      "y": 25.0,
      "z": 12.5
    },
    "holes": [
      {
        "diameter": 10.0,
        "depth": 25.0,
        "position": {"x": 25.0, "y": 25.0, "z": 0.0}
      }
    ],
    "thin_walls": [
      {
        "thickness": 2.0,
        "area": 500.0,
        "position": {"x": 50.0, "y": 0.0, "z": 12.5}
      }
    ],
    "faces": 24
  },
  "material": "ALUMINUM",
  "production_volume": 1000,
  "processes": ["CNC_MILLING", "INJECTION_MOLDING"]
}
```

**Response:**
```json
{
  "cad_data": { /* CAD geometry data */ },
  "manufacturability_score": 85.0,
  "issues": [
    {
      "severity": "warning",
      "message": "Thin wall detected (2.0mm) below recommended thickness (2.5mm)",
      "location": {"x": 50.0, "y": 0.0, "z": 12.5},
      "recommendation": "Increase wall thickness to at least 2.5mm for better manufacturability"
    }
  ],
  "process_suitability": [
    {
      "process": "CNC_MILLING",
      "suitability_score": 85.0,
      "manufacturability": "good",
      "estimated_unit_cost": 150.0,
      "estimated_lead_time": 7,
      "advantages": ["Excellent accuracy and precision", "No tooling required"],
      "limitations": ["Higher unit cost", "Slower production rate"]
    },
    {
      "process": "INJECTION_MOLDING",
      "suitability_score": 75.0,
      "manufacturability": "good",
      "estimated_unit_cost": 25.0,
      "estimated_lead_time": 28,
      "advantages": ["Low unit cost at high volumes", "Fast production rate"],
      "limitations": ["High initial tooling cost", "Design constraints for moldability"]
    }
  ],
  "cost_analysis": {
    "total_cost": 150.0,
    "setup_cost": 50.0,
    "material_cost": 20.0,
    "processing_cost": 80.0
  },
  "metadata": {
    "complexity_score": 45.0,
    "complexity_rating": "Medium",
    "complexity_factors": {
      "surface_volume_ratio": 0.12,
      "feature_density": 0.08,
      "aspect_ratio": 4.0,
      "feature_count": 2
    },
    "machining_time": {
      "total_time_minutes": 120.0,
      "setup_time_minutes": 30.0,
      "rough_machining_minutes": 45.0,
      "finish_machining_minutes": 35.0,
      "hole_operations_minutes": 10.0
    }
  }
}
```

### Legacy CAD Analysis (Enhanced)

```
POST /api/v2/analysis/cad
```

Provides backward compatibility with the legacy CAD analysis format while enhancing the response with advanced manufacturing intelligence.

**Query Parameters:**
- `material` (string, default: "ABS"): Material type
- `volume` (integer, default: 100): Production volume

**Request Body:**
```json
{
  "part_name": "example_part",
  "dimensions": {
    "length": 100.0,
    "width": 50.0,
    "height": 25.0
  },
  "volume": 125000.0,
  "surface_area": 15000.0,
  "center_of_mass": {
    "x": 50.0,
    "y": 25.0,
    "z": 12.5
  },
  "features": {
    "holes": [
      {
        "diameter": 10.0,
        "depth": 25.0,
        "position": {"x": 25.0, "y": 25.0, "z": 0.0}
      }
    ],
    "thin_walls": [
      {
        "thickness": 2.0,
        "area": 500.0,
        "position": {"x": 50.0, "y": 0.0, "z": 12.5}
      }
    ]
  }
}
```

**Response:**
```json
{
  "part_name": "example_part",
  "dimensions": { /* dimensions data */ },
  "volume": 125000.0,
  "surface_area": 15000.0,
  "center_of_mass": { /* center of mass data */ },
  "features": { /* features data */ },
  "manufacturability_score": 85.0,
  "manufacturing_issues": [
    {
      "severity": "warning",
      "message": "Thin wall detected (2.0mm) below recommended thickness (2.5mm)",
      "location": {"x": 50.0, "y": 0.0, "z": 12.5},
      "recommendation": "Increase wall thickness to at least 2.5mm"
    }
  ],
  "recommended_processes": [
    {
      "process": "CNC_MILLING",
      "suitability": 85.0,
      "cost_estimate": 150.0
    },
    {
      "process": "INJECTION_MOLDING",
      "suitability": 75.0,
      "cost_estimate": 25.0
    }
  ],
  "complexity_rating": "Medium",
  "analysis_timestamp": "2025-07-23T12:34:56.789Z"
}
```

### Batch Analysis

```
POST /api/v2/analysis/batch
```

Process multiple DFM analysis requests in a single batch with parallel processing for improved performance.

**Request Body:**
```json
{
  "requests": [
    { /* DFM analysis request 1 */ },
    { /* DFM analysis request 2 */ },
    { /* DFM analysis request 3 */ }
  ],
  "callback_url": "https://example.com/api/callback"
}
```

**Response:**
```json
{
  "batch_id": "batch_3_example_part",
  "status": "processing",
  "message": "Processing 3 requests",
  "results_count": 0
}
```

### Batch Status

```
GET /api/v2/analysis/batch/{batch_id}
```

Get the status of a batch analysis request.

**Response:**
```json
{
  "batch_id": "batch_3_example_part",
  "status": "completed",
  "message": "All requests processed successfully",
  "results_count": 3,
  "results": [
    { /* DFM analysis response 1 */ },
    { /* DFM analysis response 2 */ },
    { /* DFM analysis response 3 */ }
  ]
}
```

### System Performance

```
GET /api/v2/system/performance
```

Get system performance metrics.

**Response:**
```json
{
  "metrics": {
    "total_requests": 1250,
    "successful_requests": 1230,
    "failed_requests": 20,
    "cache_hits": 450,
    "average_processing_time": 2.5,
    "peak_processing_time": 8.3
  },
  "timestamp": "2025-07-23T12:34:56.789Z",
  "uptime_hours": 72.5
}
```

## Data Models

### CADGeometry

Represents the geometric data of a CAD model.

| Field | Type | Description |
|-------|------|-------------|
| part_name | string | Name of the part |
| volume | float | Volume in cubic millimeters |
| surface_area | float | Surface area in square millimeters |
| bounding_box | BoundingBox | Minimum bounding box dimensions |
| center_of_mass | Point3D | Center of mass coordinates |
| holes | array | List of holes in the part |
| thin_walls | array | List of thin walls in the part |
| faces | integer | Number of faces in the model (optional) |

### ProcessType

Enum representing different manufacturing processes.

- `INJECTION_MOLDING`
- `CNC_MILLING`
- `CNC_TURNING`
- `FDM_PRINTING`
- `SLA_PRINTING`
- `SLS_PRINTING`
- `SHEET_METAL`
- `CASTING`
- `FORGING`
- `EXTRUSION`

### MaterialType

Enum representing different material types.

- `ABS`
- `PLA`
- `PETG`
- `NYLON`
- `POLYCARBONATE`
- `ALUMINUM`
- `STEEL`
- `STAINLESS_STEEL`
- `BRASS`
- `COPPER`
- `TITANIUM`

## Usage Examples

### Python Client Example

```python
import requests
import json

# Define API endpoint
api_url = "http://localhost:8000/api/v2/analysis/dfm"

# Prepare CAD data
cad_data = {
    "part_name": "example_part",
    "volume": 125000.0,
    "surface_area": 15000.0,
    "bounding_box": {
        "length": 100.0,
        "width": 50.0,
        "height": 25.0
    },
    "center_of_mass": {
        "x": 50.0,
        "y": 25.0,
        "z": 12.5
    },
    "holes": [
        {
            "diameter": 10.0,
            "depth": 25.0,
            "position": {"x": 25.0, "y": 25.0, "z": 0.0}
        }
    ],
    "thin_walls": [
        {
            "thickness": 2.0,
            "area": 500.0,
            "position": {"x": 50.0, "y": 0.0, "z": 12.5}
        }
    ],
    "faces": 24
}

# Create request payload
payload = {
    "cad_data": cad_data,
    "material": "ALUMINUM",
    "production_volume": 1000,
    "processes": ["CNC_MILLING", "INJECTION_MOLDING"]
}

# Send request
response = requests.post(api_url, json=payload)

# Parse response
if response.status_code == 200:
    result = response.json()
    print(f"Manufacturability score: {result['manufacturability_score']}")
    print(f"Recommended process: {result['process_suitability'][0]['process']}")
    print(f"Estimated cost: ${result['process_suitability'][0]['estimated_unit_cost']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### Batch Processing Example

```python
import requests
import json

# Define API endpoint
api_url = "http://localhost:8000/api/v2/analysis/batch"

# Prepare multiple requests
requests_data = []
for i in range(3):
    # Create a request for each part
    requests_data.append({
        "cad_data": {
            "part_name": f"part_{i}",
            # ... other CAD data ...
        },
        "material": "ALUMINUM",
        "production_volume": 1000,
        "processes": ["CNC_MILLING", "INJECTION_MOLDING"]
    })

# Create batch request payload
payload = {
    "requests": requests_data,
    "callback_url": "https://example.com/api/callback"
}

# Send request
response = requests.post(api_url, json=payload)

# Parse response
if response.status_code == 200:
    result = response.json()
    batch_id = result["batch_id"]
    print(f"Batch processing started with ID: {batch_id}")
    
    # Check batch status (in a real application, you would poll periodically)
    status_url = f"http://localhost:8000/api/v2/analysis/batch/{batch_id}"
    status_response = requests.get(status_url)
    if status_response.status_code == 200:
        status = status_response.json()
        print(f"Batch status: {status['status']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

## Advanced Features

### Complexity Analysis

The enhanced API provides detailed complexity analysis for CAD geometries, considering:

- Surface-to-volume ratio
- Feature density
- Aspect ratio complexity
- Feature count

This analysis helps in understanding the manufacturing challenges and selecting appropriate processes.

### Process Recommendations

The system recommends suitable manufacturing processes based on:

- Part geometry and complexity
- Material compatibility
- Production volume
- Cost and lead time requirements

Each recommendation includes advantages, limitations, and estimated costs.

### Caching and Performance Optimization

The enhanced API includes:

- Result caching for improved response times
- Parallel processing for batch requests
- Performance monitoring and metrics

## Performance Considerations

- **Caching**: Identical requests are cached for 24 hours to improve response times.
- **Batch Processing**: Use batch processing for analyzing multiple parts to benefit from parallel processing.
- **Response Size**: Responses may be large due to detailed analysis results. Consider using pagination or filtering if needed.
- **Rate Limiting**: The API has rate limiting to prevent abuse. Refer to the headers for rate limit information.

---

For additional support or feature requests, please contact the development team.
