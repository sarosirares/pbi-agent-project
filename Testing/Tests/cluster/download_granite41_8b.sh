#!/bin/bash

#SBATCH --job-name=download-granite41-8b
#SBATCH --partition=main
#SBATCH --nodes=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:00:00

#SBATCH --output=download-granite41-8b-%j.out
#SBATCH --error=download-granite41-8b-%j.err

set -euo pipefail

PROJECT_DIR="${POWERBI_AGENT_ROOT:?Set POWERBI_AGENT_ROOT to the HPC working directory before submitting the job.}"

IMAGE_PATH="$PROJECT_DIR/images/vllm-nightly.sif"

MODEL_REPO="ibm-granite/granite-4.1-8b"
MODEL_DIR="$PROJECT_DIR/models/Granite4.1-8B"

export HF_HOME="$PROJECT_DIR/cache/huggingface"
export HF_HUB_DISABLE_TELEMETRY=1

mkdir -p "$MODEL_DIR"
mkdir -p "$HF_HOME"
mkdir -p "$PROJECT_DIR/logs"

echo "Downloading Granite 4.1 8B..."
echo "Repository: $MODEL_REPO"
echo "Destination: $MODEL_DIR"
echo "Image: $IMAGE_PATH"

apptainer exec \
    --bind "$PROJECT_DIR:$PROJECT_DIR" \
    "$IMAGE_PATH" \
    hf download "$MODEL_REPO" \
    --local-dir "$MODEL_DIR"

echo "Download completed."
echo "Model stored at:"
echo "$MODEL_DIR"