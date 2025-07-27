#!/bin/bash
# Script to start the unified server with Python 3.12 and Pydantic v2

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting unified server with Python 3.12 and Pydantic v2...${NC}"

# Create logs directory if it doesn't exist
mkdir -p logs

# Kill any existing unified server processes
if [ -f ./logs/unified_server_v2.pid ]; then
    echo -e "${YELLOW}Stopping existing unified server...${NC}"
    kill $(cat ./logs/unified_server_v2.pid) 2>/dev/null || true
    rm ./logs/unified_server_v2.pid
fi

# Activate Python 3.12 virtual environment with updated packages
source venv_py312_new/bin/activate

# Set the port
PORT=8084

echo -e "${YELLOW}Starting unified server on port $PORT...${NC}"

# Start the server with Python 3.12
python ./unified_server_v2.py > ./logs/unified_server_v2.log 2>&1 &
UNIFIED_PID=$!

# Save PID to file for later cleanup
echo $UNIFIED_PID > ./logs/unified_server_v2.pid

echo -e "${GREEN}Unified server started successfully!${NC}"
echo -e "${BLUE}Unified Server:${NC} http://localhost:$PORT"
echo ""
echo -e "${YELLOW}To stop the server, run: kill $(cat ./logs/unified_server_v2.pid)${NC}"
echo -e "${YELLOW}Log files are available in the logs directory${NC}"
