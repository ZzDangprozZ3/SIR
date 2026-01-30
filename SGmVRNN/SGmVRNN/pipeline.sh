#!/usr/bin/env bash
set -euo pipefail

echo "=== SGmVRNN Pipeline (NetMob23) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PY=python3

GPU_ID=${GPU_ID:-0}
N=${N:-96}
EPOCHS=${EPOCHS:-3}
BATCH_SIZE=${BATCH_SIZE:-128}

TRAIN_PATH=${TRAIN_PATH:-"../data_preprocess/data_processed/netmob_nf_dl_small_renum/train"}
TEST_PATH=${TEST_PATH:-"../data_preprocess/data_processed/netmob_nf_dl_small_renum/test"}

LOG_TRAIN=${LOG_TRAIN:-"log_trainer/netmob_nf_dl_small"}
LOG_TEST=${LOG_TEST:-"log_tester/netmob_nf_dl_small"}
CKPT_DIR=${CKPT_DIR:-"model/netmob_nf_dl_small"}

mkdir -p "$LOG_TRAIN" "$LOG_TEST" "$CKPT_DIR"

echo "[1/2] Training..."
$PY trainer.py \
  --dataset_path "$TRAIN_PATH" \
  --gpu_id "$GPU_ID" \
  --log_path "$LOG_TRAIN" \
  --checkpoints_path "$CKPT_DIR" \
  --epochs "$EPOCHS" \
  --batch_size "$BATCH_SIZE" \
  --n "$N"

START_EPOCH="$EPOCHS"

echo "[2/2] Testing (scores)..."
$PY tester.py \
  --dataset_path "$TEST_PATH" \
  --gpu_id "$GPU_ID" \
  --log_path "$LOG_TEST" \
  --checkpoints_path "$CKPT_DIR" \
  --start_epoch "$START_EPOCH" \
  --n "$N"

echo "✅ Done."
echo "Scores => $LOG_TEST/*scores*.txt"
