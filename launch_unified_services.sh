#!/bin/bash
# Launch script for FreeCAD Manufacturing Co-Pilot Unified Services
# Starts both the unified server and the local server

# Default ports
UNIFIED_SERVER_PORT=8083
LOCAL_SERVER_PORT=8090

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== FreeCAD Manufacturing Co-Pilot Unified Services ===${NC}"
echo -e "${BLUE}Starting services...${NC}"

# Create a directory for logs
mkdir -p logs

# Start the unified server in the background
echo -e "${YELLOW}Starting unified server on port $UNIFIED_SERVER_PORT...${NC}"
cd unified_server
./run_server.sh > ../logs/unified_server.log 2>&1 &
UNIFIED_PID=$!
cd ..

# Wait for the unified server to start
echo "Waiting for unified server to start..."
sleep 5

# Start the local server in the background
echo -e "${YELLOW}Starting local server on port $LOCAL_SERVER_PORT...${NC}"
./unified_local_server.py $LOCAL_SERVER_PORT > logs/local_server.log 2>&1 &
LOCAL_PID=$!

# Save PIDs to file for later cleanup
echo $UNIFIED_PID > logs/unified_server.pid
echo $LOCAL_PID > logs/local_server.pid

echo -e "${GREEN}Services started successfully!${NC}"
echo -e "${BLUE}Unified Server:${NC} http://localhost:$UNIFIED_SERVER_PORT"
echo -e "${BLUE}Local Server:${NC} http://localhost:$LOCAL_SERVER_PORT"
echo ""
echo -e "${YELLOW}To stop the services, run: ./stop_unified_services.sh${NC}"
echo -e "${YELLOW}Log files are available in the logs directory${NC}"

# Create a stop script if it doesn't exist
if [ ! -f "stop_unified_services.sh" ]; then
    cat > stop_unified_services.sh << 'EOF'
#!/bin/bash
# Stop script for FreeCAD Manufacturing Co-Pilot Unified Services

# Colors for terminal output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${RED}Stopping FreeCAD Manufacturing Co-Pilot Unified Services...${NC}"

# Kill the unified server
if [ -f logs/unified_server.pid ]; then
    UNIFIED_PID=$(cat logs/unified_server.pid)
    echo "Stopping unified server (PID: $UNIFIED_PID)..."
    kill $UNIFIED_PID 2>/dev/null || true
    rm logs/unified_server.pid
fi

# Kill the local server
if [ -f logs/local_server.pid ]; then
    LOCAL_PID=$(cat logs/local_server.pid)
    echo "Stopping local server (PID: $LOCAL_PID)..."
    kill $LOCAL_PID 2>/dev/null || true
    rm logs/local_server.pid
fi

echo -e "${GREEN}Services stopped successfully!${NC}"
EOF
    chmod +x stop_unified_services.sh
fi

# Launch FreeCAD with the plugin if requested
if [ "$1" == "--with-freecad" ]; then
    echo -e "${YELLOW}Launching FreeCAD with Manufacturing Co-Pilot plugin...${NC}"
    ./launch_freecad.sh
fi
