#!/bin/bash
#SBATCH --job-name=mistral32-vllm
#SBATCH --partition=main
#SBATCH --nodes=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --gres=gpu:nvidia_h200:1
#SBATCH --output=/projects/airi/srares/powerbi-agent/logs/mistral32-vllm-%j.out
#SBATCH --error=/projects/airi/srares/powerbi-agent/logs/mistral32-vllm-%j.err

set -euo pipefail

PROJECT_DIR="/projects/airi/srares/powerbi-agent"
IMAGE_PATH="$PROJECT_DIR/images/vllm-nightly.sif"
MODEL_PATH="$PROJECT_DIR/models/Mistral-Small-3.2-24B-Instruct-2506"

PORT=8000
MAX_MODEL_LEN=98304

mkdir -p "$PROJECT_DIR/logs"

echo "Starting Mistral Small 3.2 24B"
echo "Model: $MODEL_PATH"
echo "Image: $IMAGE_PATH"
echo "Port: $PORT"
echo "Max model length: $MAX_MODEL_LEN"

apptainer exec --nv \
    --bind "$PROJECT_DIR:$PROJECT_DIR" \
    "$IMAGE_PATH" \
    vllm serve "$MODEL_PATH" \
    --served-model-name Mistral-Small-3.2-24B \
    --host 0.0.0.0 \
    --port "$PORT" \
    --tokenizer-mode mistral \
    --config-format mistral \
    --load-format mistral \
    --max-model-len "$MAX_MODEL_LEN" \
    --max-num-seqs 32 \
    --language-model-only \
    --enable-auto-tool-choice \
    --tool-call-parser mistral