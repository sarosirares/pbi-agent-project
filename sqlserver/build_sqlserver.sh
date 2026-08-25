#!/bin/bash

#SBATCH --job-name=build-pbi-sqlserver
#SBATCH --partition=main
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00

set -euo pipefail

SQLSERVER_DIR="${POWERBI_SQLSERVER_DIR:-${SLURM_SUBMIT_DIR:-}}"

if [[ -z "$SQLSERVER_DIR" || ! -f "$SQLSERVER_DIR/sqlserver.def" ]]; then
    echo "Could not locate the SQL Server deployment directory."
    echo "Submit this job from sqlserver/ or set POWERBI_SQLSERVER_DIR."
    exit 1
fi

PROJECT_DIR="$(cd "$SQLSERVER_DIR/.." && pwd)"
IMAGE_DIR="${POWERBI_AGENT_IMAGE_DIR:-$PROJECT_DIR/images}"

DEF_FILE="$SQLSERVER_DIR/sqlserver.def"

SCRATCH_BUILD_DIR="/scratch/$USER/powerbi-agent-sqlserver-build"

IMAGE_NAME="sqlserver-2025-nocap.sif"
TEMP_IMAGE="$SCRATCH_BUILD_DIR/$IMAGE_NAME"
FINAL_IMAGE="$IMAGE_DIR/$IMAGE_NAME"

export APPTAINER_CACHEDIR="/scratch/$USER/.apptainer/cache"
export APPTAINER_TMPDIR="/scratch/$USER/.apptainer/tmp"

mkdir -p "$SCRATCH_BUILD_DIR"
mkdir -p "$IMAGE_DIR"
mkdir -p "$APPTAINER_CACHEDIR"
mkdir -p "$APPTAINER_TMPDIR"

echo "Building SQL Server Apptainer image..."
echo "Node: $(hostname)"
echo "Definition file: $DEF_FILE"
echo "Final image: $FINAL_IMAGE"

cd "$SQLSERVER_DIR"

apptainer build "$TEMP_IMAGE" "$DEF_FILE"

mv "$TEMP_IMAGE" "$FINAL_IMAGE"

echo "Build completed."
echo "Image stored at:"
echo "$FINAL_IMAGE"