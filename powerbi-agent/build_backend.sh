#!/bin/bash

#SBATCH --job-name=build-pbi-backend
#SBATCH --partition=main
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00

set -euo pipefail

APP_DIR="${POWERBI_AGENT_APP_DIR:-${SLURM_SUBMIT_DIR:-}}"

if [[ -z "$APP_DIR" || ! -f "$APP_DIR/backend.def" ]]; then
    echo "Could not locate the Power BI agent directory."
    echo "Submit this job from powerbi-agent/ or set POWERBI_AGENT_APP_DIR."
    exit 1
fi

PROJECT_DIR="$(cd "$APP_DIR/.." && pwd)"
IMAGE_DIR="${POWERBI_AGENT_IMAGE_DIR:-$PROJECT_DIR/images}"

DEF_FILE="$APP_DIR/backend.def"

SCRATCH_BUILD_DIR="/scratch/$USER/powerbi-agent-backend-build"

IMAGE_NAME="powerbi-backend.sif"
TEMP_IMAGE="$SCRATCH_BUILD_DIR/$IMAGE_NAME"
FINAL_IMAGE="$IMAGE_DIR/$IMAGE_NAME"

export APPTAINER_CACHEDIR="/scratch/$USER/.apptainer/cache"
export APPTAINER_TMPDIR="/scratch/$USER/.apptainer/tmp"

mkdir -p "$SCRATCH_BUILD_DIR"
mkdir -p "$IMAGE_DIR"
mkdir -p "$APPTAINER_CACHEDIR"
mkdir -p "$APPTAINER_TMPDIR"

echo "Building Power BI backend Apptainer image..."
echo "Node: $(hostname)"
echo "Application directory: $APP_DIR"
echo "Definition file: $DEF_FILE"
echo "Final image: $FINAL_IMAGE"

cd "$APP_DIR"

apptainer build "$TEMP_IMAGE" "$DEF_FILE"

mv "$TEMP_IMAGE" "$FINAL_IMAGE"

echo "Build completed."
echo "Image stored at:"
echo "$FINAL_IMAGE"