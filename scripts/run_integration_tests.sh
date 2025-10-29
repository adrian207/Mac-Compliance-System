#!/bin/bash
# Integration Test Runner Script for Linux/Mac
# Author: Adrian Johnson <adrian207@gmail.com>

set -e

MODE="mock"
INTEGRATION="all"
START_MOCKS=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --integration)
            INTEGRATION="$2"
            shift 2
            ;;
        --start-mocks)
            START_MOCKS=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo ""
echo "========================================"
echo "Integration Test Runner"
echo "========================================"
echo ""

# Check mode
if [ "$MODE" = "mock" ]; then
    echo "Mode: MOCK (using local mock servers)"
    
    if [ "$START_MOCKS" = true ]; then
        echo ""
        echo "Starting mock servers..."
        
        # Start Kandji mock server in background
        echo "  Starting Mock Kandji API on port 8001..."
        python tests/mocks/mock_kandji.py > /dev/null 2>&1 &
        MOCK_PID=$!
        
        # Wait for server to start
        echo "  Waiting for servers to initialize..."
        sleep 3
        
        # Test if server is up
        if curl -s -f http://localhost:8001/docs > /dev/null 2>&1; then
            echo "  ✓ Mock Kandji API is running (PID: $MOCK_PID)"
        else
            echo "  ✗ Failed to start Mock Kandji API"
            echo "    Try running manually: python tests/mocks/mock_kandji.py"
            exit 1
        fi
    else
        echo ""
        echo "⚠️  Make sure mock servers are running:"
        echo "   python tests/mocks/mock_kandji.py"
        echo ""
        echo "   Or run with --start-mocks flag"
        echo ""
    fi
else
    echo "Mode: LIVE (using real API credentials)"
    echo ""
    echo "⚠️  Make sure environment variables are set:"
    echo "   KANDJI_ENDPOINT, KANDJI_API_KEY, etc."
    echo ""
fi

# Run tests
echo ""
echo "Running integration tests..."
echo "Integration: $INTEGRATION"
echo ""

python tests/integration_tests/test_integrations.py \
    --mode "$MODE" \
    --integration "$INTEGRATION"

EXIT_CODE=$?

# Cleanup message
if [ "$MODE" = "mock" ] && [ "$START_MOCKS" = true ]; then
    echo ""
    echo "⚠️  Mock servers are still running in background"
    echo "   Kill them with: kill $MOCK_PID"
fi

exit $EXIT_CODE

