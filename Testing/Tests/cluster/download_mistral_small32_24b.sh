#!/bin/bash

#SBATCH --job-name=download-mistral32-24b
#SBATCH --partition=main
#SBATCH --nodes=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:00:00

#SBATCH --output=/projects/airi/srares/powerbi-agent/logs/download-mistral32-24b-%j.out
#SBATCH --error=/projects/airi/srares/powerbi-agent/logs/download-mistral32-24b-%j.err

set -euo pipefail

PROJECT_DIR="/projects/airi/srares/powerbi-agent"

IMAGE_PATH="$PROJECT_DIR/images/vllm-nightly.sif"

MODEL_REPO="mistralai/Mistral-Small-3.2-24B-Instruct-2506"
MODEL_DIR="$PROJECT_DIR/models/Mistral-Small-3.2-24B-Instruct-2506"

export HF_HOME="$PROJECT_DIR/cache/huggingface"
export HF_HUB_DISABLE_TELEMETRY=1

mkdir -p "$MODEL_DIR"
mkdir -p "$HF_HOME"
mkdir -p "$PROJECT_DIR/logs"

echo "Downloading Mistral Small 3.2 24B..."
echo "Repository: $MODEL_REPO"
echo "Destination: $MODEL_DIR"
echo "Image: $IMAGE_PATH"

# Download only the native Mistral-format files needed by vLLM.
# This avoids downloading a second duplicate ~48 GB set of HF-format weights.
apptainer exec \
    --bind "$PROJECT_DIR:$PROJECT_DIR" \
    "$IMAGE_PATH" \
    hf download "$MODEL_REPO" \
    consolidated.safetensors \
    params.json \
    tekken.json \
    SYSTEM_PROMPT.txt \
    --local-dir "$MODEL_DIR"

echo "Download completed."
echo "Model stored at:"
echo "$MODEL_DIR"

du -sh "$MODEL_DIR"