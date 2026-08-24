#!/bin/bash

#SBATCH --job-name=qwen36-vllm
#SBATCH --partition=main
#SBATCH --nodes=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --gres=gpu:nvidia_h200:1

#SBATCH --output=qwen36-vllm-%j.out
#SBATCH --error=qwen36-vllm-%j.err

set -euo pipefail

PROJECT_DIR="${POWERBI_AGENT_ROOT:?Set POWERBI_AGENT_ROOT to the HPC working directory before submitting the job.}"
IMAGE_PATH="$PROJECT_DIR/images/vllm-v0.26.0.sif"
MODEL_PATH="$PROJECT_DIR/models/Qwen3.6-27B"

PORT=8000
MAX_MODEL_LEN=98304

mkdir -p "$PROJECT_DIR/logs"

echo "Starting Qwen3.6-27B"
echo "Model: $MODEL_PATH"
echo "Image: $IMAGE_PATH"
echo "Port: $PORT"
echo "Max model length: $MAX_MODEL_LEN"

apptainer exec --nv \
    --bind "$PROJECT_DIR:$PROJECT_DIR" \
    "$IMAGE_PATH" \
    vllm serve "$MODEL_PATH" \
    --served-model-name Qwen3.6-27B \
    --host 0.0.0.0 \
    --port "$PORT" \
    --max-model-len "$MAX_MODEL_LEN" \
    --max-num-seqs 32 \
    --reasoning-parser qwen3 \
    --enable-auto-tool-choice \
    --tool-call-parser qwen3_coder \
    --language-model-only