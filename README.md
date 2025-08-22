# FreeCAD Cloud Co-Pilot

An enhanced manufacturing co-pilot for FreeCAD with cloud-based AI processing and multi-agent system integration.

## Project Overview

This project enhances the existing FreeCAD Manufacturing Co-Pilot by:

1. **Refactoring the existing macro** for better performance and maintainability
2. **Adding cloud connectivity** to offload intensive processing
3. **Supporting multiple AI agents** for specialized manufacturing intelligence
4. **Enabling multi-agent orchestration** for comprehensive manufacturing insights
5. **Improving the UI** for better user experience

## Architecture

The system consists of two main components:

### 1. FreeCAD Macro (Client)
- Handles the user interface within FreeCAD
- Manages local CAD analysis
- Communicates with the cloud backend
- Provides agent selection and orchestration UI
- Supports fallback responses when offline

### 2. Cloud Backend (Server)
- Processes AI requests
- Manages multiple specialized manufacturing agents
- Orchestrates multi-agent collaboration
- Handles authentication and security
- Stores conversation history and context

## Getting Started

1. Install the FreeCAD macro
2. Configure your API keys in `macro/config.py`
3. Connect to the cloud backend
4. Run the macro within FreeCAD or use the launcher script

```bash
# Launch within FreeCAD
python /path/to/ManufacturingCoPilot.FCMacro

# Or use the standalone launcher (limited functionality)
python launch_copilot.py
```

## Features

### Multi-Agent System

The Manufacturing Co-Pilot now includes a specialized multi-agent system with experts in different manufacturing domains:

- **DFM Expert**: Design for Manufacturing specialist
- **Cost Estimator**: Provides detailed cost analysis
- **Process Planner**: Recommends optimal manufacturing processes
- **Material Selector**: Suggests appropriate materials

### Agent Orchestration

Users can select multiple agents to collaborate on complex manufacturing queries. The system will:

1. Route the query to each selected agent
2. Collect specialized insights from each agent
3. Generate a comprehensive response that integrates all perspectives

### Offline Fallback

The system provides intelligent fallback responses when cloud connectivity is unavailable, ensuring continuity of service.

## Latest Updates (MoldFlow‑Lite v0.2)

MoldFlow‑Lite v0.2 is a standalone FreeCAD macro that overlays a simple mold‑flow preview on your 3D part.

- __Dynamic overlays__: Works on any watertight solid in the active document. Uses selected faces as gate points; otherwise auto‑uses part center.
- __Correct alignment__: Overlays honor the part’s global placement/orientation.
- __Reliable seeding__: Gate seeds snap to the nearest interior voxel to avoid missing overlays.
- __Controls__: Material, grid resolution, point density, thin‑wall threshold, marker size, Fast preview.
- __Visuals__: Dot heatmap with a 3D color legend placed beside the model. Gate markers. Optional weld‑line toggle.
- __Status summary__: Plain, concise text showing quick/medium/late fill proportions, thin‑wall %, and overlay point count.
- __Clear overlay__: One click removes all overlay objects and the color legend, restoring original transparency.
- __Export__: Saves a minimal JSON (material, gates, heuristics) for external explanations.

Tips for speed:
- __Fast preview__: On → lower resolution, skips weld‑line extraction.
- __Grid resolution__: 36–48 is faster than 64+.
- __Point density__: 0.4–0.6 draws fewer dots while keeping the pattern.

File: `macro/MoldFlowLite_v0_2.FCMacro`

How to launch: open a model in FreeCAD, run the macro. Select faces to set gates (optional), then click “Show Mold Flow”.

Note: This macro is isolated and does not modify BOM, DFM, Text‑to‑CAD, or Sheet Metal features.

## Tech Stack

- __Client (FreeCAD)__: Python macros, Qt UI via PySide2 (bundled with FreeCAD), FreeCAD `Part`/Coin scene graph.
- __Unified/Cloud servers__: FastAPI + Uvicorn, multi‑agent orchestration, REST endpoints.
- __Agents/LLMs__: Anthropic Claude, OpenAI APIs (configurable). Local fallback supported.
- __Utilities__: Requests/HTTPX, dotenv, multipart uploads, JSON/JSON5 handling, optional NumPy/SciPy/Pandas for analysis.

## Libraries Used

Across the repository (deduplicated):

- __FreeCAD macro env__: PySide2 (provided by FreeCAD), FreeCAD Python API (`FreeCAD`, `FreeCADGui`, `Part`).
- __HTTP/Clients__: `requests`, `httpx`
- __Web servers__: `fastapi`, `uvicorn`, `gunicorn`, `starlette`
- __Data models__: `pydantic`
- __Env/Uploads__: `python-dotenv`, `python-multipart`
- __LLM SDKs__: `openai`, `anthropic`
- __Numerics/Data (backend)__: `numpy`, `scipy`, `pandas`
- __Serialization__: `json5` (in backend)
- __Agent service (text‑to‑cad)__: `flask` (containerized microservice)

Source requirement files:
- Root: `requirements.txt`
- Cloud backend: `cloud_backend/requirements.txt`
- Unified server: `unified_server/requirements.txt`
- Cloud services: `cloud_services/requirements.txt`
- Text‑to‑CAD agent: `cloud-services/text-to-cad-agent/requirements.txt`

## Custom BOM Window (Checkpoint 8)

The macro includes a custom, floating Bill of Materials (BOM) window with Indian market costing in INR.

How to use:

- **Open BOM**: Click the `BOM` button in the task panel.
- **Quantity prompt**: A dialog asks for your required production quantity. This seeds the BOM's amortization quantity for tooling-based processes (e.g., injection molding).
- **Per-row selections**: In the BOM table, each part row has dropdowns for **Process** and **Material**.
- **Live costs**: Unit and extended costs update immediately when you change process/material or amortization quantity.
- **Cost breakdown**: Hover any cell to see a detailed per-row breakdown (cycle time, material, scrap, tooling amortization, setup, etc.). The same text appears in the Notes column.
- **Per-unit at quantity**: The bottom panel shows a “Per-Unit at Qty” figure derived from the grand total divided by the selected quantity.
- **Exports**: Use buttons to export the BOM to CSV/XLSX.

Notes:

- Tooling costs are amortized by the “Amortization Quantity” shown in the BOM window; it defaults to your entered quantity but can be adjusted at any time.
- Pricing, densities, and process parameters are configurable in `pricing_in.json`.

## Development

This project is structured to allow for incremental improvements while maintaining compatibility with the existing functionality.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
