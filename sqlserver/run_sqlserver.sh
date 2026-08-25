#!/bin/bash

#SBATCH --job-name=pbi-sqlserver
#SBATCH --partition=main
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=02:00:00

set -euo pipefail

SQLSERVER_DIR="${POWERBI_SQLSERVER_DIR:-${SLURM_SUBMIT_DIR:-}}"

if [[ -z "$SQLSERVER_DIR" || ! -f "$SQLSERVER_DIR/sqlserver.def" ]]; then
    echo "Could not locate the SQL Server deployment directory."
    echo "Submit this job from sqlserver/ or set POWERBI_SQLSERVER_DIR."
    exit 1
fi

PROJECT_DIR="$(cd "$SQLSERVER_DIR/.." && pwd)"

IMAGE_PATH="${POWERBI_SQLSERVER_IMAGE:-$PROJECT_DIR/images/sqlserver-2025-nocap.sif}"

ENV_FILE="$SQLSERVER_DIR/sqlserver.env"
STATE_DIR="$SQLSERVER_DIR/data"
BACKUP_DIR="$SQLSERVER_DIR/backup"

if [[ ! -f "$IMAGE_PATH" ]]; then
    echo "SQL Server image not found:"
    echo "$IMAGE_PATH"
    exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
    echo "SQL Server environment file not found:"
    echo "$ENV_FILE"
    echo "Copy sqlserver.env.example to sqlserver.env and configure it first."
    exit 1
fi

mkdir -p "$STATE_DIR"
mkdir -p "$BACKUP_DIR"

echo "Starting SQL Server..."
echo "Node: $(hostname)"
echo "Image: $IMAGE_PATH"
echo "Data directory: $STATE_DIR"
echo "Backup directory: $BACKUP_DIR"

apptainer exec \
    --env-file "$ENV_FILE" \
    --bind "$STATE_DIR:/var/opt/mssql" \
    --bind "$BACKUP_DIR:/var/opt/mssql/backup" \
    "$IMAGE_PATH" \
    /opt/mssql/bin/sqlservr