#!/bin/bash
echo "========================================="
echo "  Starting Health Triage System"
echo "========================================="
echo ""

# Function to cleanly kill background processes on exit
cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $(jobs -p) 2>/dev/null
    exit
}

# Register the cleanup function for when the script is stopped (Ctrl+C)
trap cleanup SIGINT SIGTERM

echo "Starting FastAPI Backend..."
(cd backend && source venv/bin/activate && uvicorn app.main:app --reload) &

# Give the backend a second to start
sleep 2

echo "Starting Streamlit Frontend..."
(cd frontend && source ../backend/venv/bin/activate && streamlit run app.py) &

echo ""
echo "Both servers are running in the background."
echo "Press Ctrl+C to stop both servers."
echo "========================================="

# Keep the script running to catch Ctrl+C and wait for the processes
wait
