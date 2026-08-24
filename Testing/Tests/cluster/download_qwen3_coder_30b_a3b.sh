#!/bin/bash

#SBATCH --job-name=download-qwen3coder
#SBATCH --partition=main
#SBATCH --nodes=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:30:00

#SBATCH --output=download-qwen3coder-%j.out
#SBATCH --error=download-qwen3coder-%j.err

set -euo pipefail

PROJECT_DIR="${POWERBI_AGENT_ROOT:?Set POWERBI_AGENT_ROOT to the HPC working directory before submitting the job.}"
IMAGE_PATH="$PROJECT_DIR/images/vllm-v0.26.0.sif"

MODEL_REPO="Qwen/Qwen3-Coder-30B-A3B-Instruct"
MODEL_DIR="$PROJECT_DIR/models/Qwen3-Coder-30B-A3B-Instruct"

export HF_HOME="$PROJECT_DIR/cache/huggingface"
export HF_HUB_DISABLE_TELEMETRY=1

mkdir -p "$MODEL_DIR"
mkdir -p "$HF_HOME"
mkdir -p "$PROJECT_DIR/logs"

echo "Downloading Qwen3-Coder-30B-A3B-Instruct..."
echo "Repository: $MODEL_REPO"
echo "Destination: $MODEL_DIR"

apptainer exec \
    --bind "$PROJECT_DIR:$PROJECT_DIR" \
    "$IMAGE_PATH" \
    hf download "$MODEL_REPO" \
    --local-dir "$MODEL_DIR"

echo "Download completed."
du -sh "$MODEL_DIR"