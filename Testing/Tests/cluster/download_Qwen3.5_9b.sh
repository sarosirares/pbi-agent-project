#!/bin/bash

#SBATCH --job-name=download-qwen35-9b
#SBATCH --partition=main
#SBATCH --nodes=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:00:00

#SBATCH --output=/projects/airi/srares/powerbi-agent/logs/download-qwen35-9b-%j.out
#SBATCH --error=/projects/airi/srares/powerbi-agent/logs/download-qwen35-9b-%j.err

set -euo pipefail

PROJECT_DIR="/projects/airi/srares/powerbi-agent"

IMAGE_PATH="$PROJECT_DIR/images/vllm-v0.26.0.sif"

MODEL_REPO="Qwen/Qwen3.5-9B"
MODEL_DIR="$PROJECT_DIR/models/Qwen3.5-9B"

export HF_HOME="$PROJECT_DIR/cache/huggingface"
export HF_HUB_DISABLE_TELEMETRY=1

mkdir -p "$MODEL_DIR"
mkdir -p "$HF_HOME"

echo "Downloading model..."
echo "Repository: $MODEL_REPO"
echo "Destination: $MODEL_DIR"

apptainer exec \
    --bind "$PROJECT_DIR:$PROJECT_DIR" \
    "$IMAGE_PATH" \
    hf download "$MODEL_REPO" \
    --local-dir "$MODEL_DIR"

echo "Download completed."
echo "Model stored at:"
echo "$MODEL_DIR"