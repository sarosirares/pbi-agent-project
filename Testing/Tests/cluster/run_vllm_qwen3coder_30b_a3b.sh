#!/bin/bash

#SBATCH --job-name=qwen3coder-vllm
#SBATCH --partition=main
#SBATCH --nodes=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --gres=gpu:nvidia_h200_3g.71gb:1

#SBATCH --output=/projects/airi/srares/powerbi-agent/logs/qwen3coder-vllm-%j.out
#SBATCH --error=/projects/airi/srares/powerbi-agent/logs/qwen3coder-vllm-%j.err

set -euo pipefail

PROJECT_DIR="/projects/airi/srares/powerbi-agent"
IMAGE_PATH="$PROJECT_DIR/images/vllm-v0.26.0.sif"
MODEL_PATH="$PROJECT_DIR/models/Qwen3-Coder-30B-A3B-Instruct"

PORT=8000
MAX_MODEL_LEN=32768

mkdir -p "$PROJECT_DIR/logs"

echo "Starting Qwen3-Coder-30B-A3B-Instruct"
echo "Model: $MODEL_PATH"
echo "Image: $IMAGE_PATH"
echo "Port: $PORT"
echo "Max model length: $MAX_MODEL_LEN"

apptainer exec --nv \
    --bind "$PROJECT_DIR:$PROJECT_DIR" \
    "$IMAGE_PATH" \
    vllm serve "$MODEL_PATH" \
    --served-model-name Qwen3-Coder-30B-A3B-Instruct \
    --host 0.0.0.0 \
    --port "$PORT" \
    --max-model-len "$MAX_MODEL_LEN" \
    --max-num-seqs 32 \
    --enable-auto-tool-choice \
    --tool-call-parser qwen3_coder