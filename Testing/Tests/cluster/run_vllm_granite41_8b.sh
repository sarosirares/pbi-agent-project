#!/bin/bash

#SBATCH --job-name=granite41-vllm
#SBATCH --partition=main
#SBATCH --nodes=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --gres=gpu:nvidia_h200_2g.35gb:1

#SBATCH --output=granite41-vllm-%j.out
#SBATCH --error=granite41-vllm-%j.err

set -euo pipefail

PROJECT_DIR="${POWERBI_AGENT_ROOT:?Set POWERBI_AGENT_ROOT to the HPC working directory before submitting the job.}"

IMAGE_PATH="$PROJECT_DIR/images/vllm-nightly.sif"
MODEL_PATH="$PROJECT_DIR/models/Granite4.1-8B"

PORT=8000
MAX_MODEL_LEN=65536

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

echo "Starting Granite 4.1 8B with vLLM..."
echo "Node: $(hostname)"
echo "Image: $IMAGE_PATH"
echo "Model: $MODEL_PATH"
echo "Port: $PORT"
echo "Max model length: $MAX_MODEL_LEN"

apptainer exec --nv \
    --bind "$PROJECT_DIR:$PROJECT_DIR" \
    "$IMAGE_PATH" \
    vllm serve "$MODEL_PATH" \
    --served-model-name Granite4.1-8B \
    --host 0.0.0.0 \
    --port "$PORT" \
    --max-model-len "$MAX_MODEL_LEN" \
    --max-num-seqs 64 \
    --enable-auto-tool-choice \
    --tool-call-parser granite4