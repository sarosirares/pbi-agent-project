#!/bin/bash

#SBATCH --job-name=download-nemotron3
#SBATCH --partition=main
#SBATCH --nodes=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=02:00:00

#SBATCH --output=/projects/airi/srares/powerbi-agent/logs/download-nemotron3-%j.out
#SBATCH --error=/projects/airi/srares/powerbi-agent/logs/download-nemotron3-%j.err

set -euo pipefail

PROJECT_DIR="/projects/airi/srares/powerbi-agent"
IMAGE_PATH="$PROJECT_DIR/images/vllm-v0.26.0.sif"

MODEL_REPO="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16"
MODEL_DIR="$PROJECT_DIR/models/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16"

export HF_HOME="$PROJECT_DIR/cache/huggingface"
export HF_HUB_DISABLE_TELEMETRY=1

mkdir -p "$MODEL_DIR"
mkdir -p "$HF_HOME"
mkdir -p "$PROJECT_DIR/logs"

echo "Downloading NVIDIA Nemotron 3 Nano 30B-A3B BF16..."
echo "Repository: $MODEL_REPO"
echo "Destination: $MODEL_DIR"

apptainer exec \
    --bind "$PROJECT_DIR:$PROJECT_DIR" \
    "$IMAGE_PATH" \
    hf download "$MODEL_REPO" \
    --local-dir "$MODEL_DIR"

echo "Download completed."

du -sh "$MODEL_DIR"