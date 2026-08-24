#!/bin/bash

#SBATCH --job-name=build-vllm-nightly
#SBATCH --partition=main
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=40G
#SBATCH --time=01:00:00

set -euo pipefail

PROJECT_DIR="/projects/airi/srares/powerbi-agent"
IMAGE_DIR="$PROJECT_DIR/images"

DEF_FILE="$HOME/powerbi-agent/cluster/vllm-nightly.def"

SCRATCH_BUILD_DIR="/scratch/$USER/powerbi-agent-build"

IMAGE_NAME="vllm-nightly.sif"

TEMP_IMAGE="$SCRATCH_BUILD_DIR/$IMAGE_NAME"
FINAL_IMAGE="$IMAGE_DIR/$IMAGE_NAME"

export APPTAINER_CACHEDIR="/scratch/$USER/.apptainer/cache"
export APPTAINER_TMPDIR="/scratch/$USER/.apptainer/tmp"

mkdir -p "$SCRATCH_BUILD_DIR"
mkdir -p "$IMAGE_DIR"
mkdir -p "$APPTAINER_CACHEDIR"
mkdir -p "$APPTAINER_TMPDIR"

echo "Building vLLM nightly Apptainer image..."
echo "Node: $(hostname)"
echo "Definition file: $DEF_FILE"
echo "Temporary image: $TEMP_IMAGE"
echo "Final image: $FINAL_IMAGE"

apptainer build "$TEMP_IMAGE" "$DEF_FILE"

echo "Build completed."

mv "$TEMP_IMAGE" "$FINAL_IMAGE"

echo "Image stored at:"
echo "$FINAL_IMAGE"