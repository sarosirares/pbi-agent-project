#!/bin/bash

#SBATCH --job-name=pbi-backend
#SBATCH --partition=main
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=02:00:00

set -euo pipefail

APP_DIR="${POWERBI_AGENT_APP_DIR:-${SLURM_SUBMIT_DIR:-}}"

if [[ -z "$APP_DIR" || ! -f "$APP_DIR/app.py" ]]; then
    echo "Could not locate the Power BI agent directory."
    echo "Submit this job from powerbi-agent/ or set POWERBI_AGENT_APP_DIR."
    exit 1
fi

PROJECT_DIR="$(cd "$APP_DIR/.." && pwd)"

IMAGE_PATH="${POWERBI_AGENT_BACKEND_IMAGE:-$PROJECT_DIR/images/powerbi-backend.sif}"

HOST="0.0.0.0"
PORT=8080

if [[ ! -f "$IMAGE_PATH" ]]; then
    echo "Backend image not found:"
    echo "$IMAGE_PATH"
    exit 1
fi

echo "Starting Power BI backend..."
echo "Node: $(hostname)"
echo "Application directory: $APP_DIR"
echo "Image: $IMAGE_PATH"
echo "Address: $HOST:$PORT"

cd "$APP_DIR"

apptainer exec \
    --bind "$APP_DIR:/app" \
    --pwd /app \
    "$IMAGE_PATH" \
    python -m uvicorn app:app \
        --host "$HOST" \
        --port "$PORT"