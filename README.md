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

## Development

This project is structured to allow for incremental improvements while maintaining compatibility with the existing functionality.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
