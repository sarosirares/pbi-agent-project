#!/bin/bash

#SBATCH --job-name=powerbi-vllm
#SBATCH --partition=main
#SBATCH --nodes=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --gres=gpu:nvidia_h200_2g.35gb:1

#SBATCH --output=/projects/airi/srares/powerbi-agent/logs/vllm-%j.out
#SBATCH --error=/projects/airi/srares/powerbi-agent/logs/vllm-%j.err

set -euo pipefail

PROJECT_DIR="/projects/airi/srares/powerbi-agent"

IMAGE_PATH="$PROJECT_DIR/images/vllm-nightly.sif"
MODEL_PATH="${1:-}"

PORT=8000
MAX_MODEL_LEN=65536

if [[ -z "$MODEL_PATH" ]]; then
    echo "ERROR: No model path was provided."
    echo "Usage: sbatch run_vllm.sh /path/to/model"
    exit 1
fi

if [[ ! -f "$IMAGE_PATH" ]]; then
    echo "ERROR: vLLM image not found:"
    echo "$IMAGE_PATH"
    exit 1
fi

if [[ ! -d "$MODEL_PATH" ]]; then
    echo "ERROR: Model directory not found:"
    echo "$MODEL_PATH"
    exit 1
fi

echo "Starting vLLM..."
echo "Node: $(hostname)"
echo "Image: $IMAGE_PATH"
echo "Model: $MODEL_PATH"
echo "Port: $PORT"
echo "Max model length: $MAX_MODEL_LEN"

apptainer exec --nv \
    --bind "$PROJECT_DIR:$PROJECT_DIR" \
    "$IMAGE_PATH" \
    vllm serve "$MODEL_PATH" \
    --served-model-name Qwen3.5-9B \
    --host 0.0.0.0 \
    --port "$PORT" \
    --max-model-len "$MAX_MODEL_LEN" \
    --max-num-seqs 64 \
    --reasoning-parser qwen3 \
    --enable-auto-tool-choice \
    --tool-call-parser qwen3_coder \
    --language-model-only