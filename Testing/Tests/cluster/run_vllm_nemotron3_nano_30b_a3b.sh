#!/bin/bash

#SBATCH --job-name=nemotron3-vllm
#SBATCH --partition=main
#SBATCH --nodes=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --gres=gpu:nvidia_h200_3g.71gb:1

#SBATCH --output=/projects/airi/srares/powerbi-agent/logs/nemotron3-vllm-%j.out
#SBATCH --error=/projects/airi/srares/powerbi-agent/logs/nemotron3-vllm-%j.err

set -euo pipefail

PROJECT_DIR="/projects/airi/srares/powerbi-agent"
IMAGE_PATH="$PROJECT_DIR/images/vllm-v0.26.0.sif"
MODEL_PATH="$PROJECT_DIR/models/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16"
REASONING_PARSER="$MODEL_PATH/nano_v3_reasoning_parser.py"

PORT=8000
MAX_MODEL_LEN=32768

mkdir -p "$PROJECT_DIR/logs"

echo "Starting NVIDIA Nemotron 3 Nano 30B-A3B BF16"
echo "Model: $MODEL_PATH"
echo "Image: $IMAGE_PATH"
echo "Reasoning parser: $REASONING_PARSER"
echo "Port: $PORT"
echo "Max model length: $MAX_MODEL_LEN"

apptainer exec --nv \
    --bind "$PROJECT_DIR:$PROJECT_DIR" \
    "$IMAGE_PATH" \
    vllm serve "$MODEL_PATH" \
    --served-model-name Nemotron3-Nano-30B-A3B \
    --host 0.0.0.0 \
    --port "$PORT" \
    --max-model-len "$MAX_MODEL_LEN" \
    --max-num-seqs 16 \
    --trust-remote-code \
    --enable-auto-tool-choice \
    --tool-call-parser qwen3_coder \
    --reasoning-parser-plugin "$REASONING_PARSER" \
    --reasoning-parser nano_v3