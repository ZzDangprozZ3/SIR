#!/usr/bin/env bash
set -euo pipefail

echo "=== SGmVRNN Pipeline (NetMob23) ==="

# -------------------
# Paramètres (modifiable)
# -------------------
DATASET_TRAIN=${DATASET_TRAIN:-"../data_preprocess/data_processed/netmob_nf_dl_small_renum/train"}
DATASET_TEST=${DATASET_TEST:-"../data_preprocess/data_processed/netmob_nf_dl_small_renum/test"}

GPU_ID=${GPU_ID:-0}
N=${N:-96}
T=${T:-20}
BATCH=${BATCH:-128}
EPOCHS=${EPOCHS:-3}

APPLI=${APPLI:-"netflix"}
TILE=${TILE:-"unknown"}
START_DATE=${START_DATE:-"2019-01-01"}   # si tes timestamps sont des index

LOG_TRAIN=${LOG_TRAIN:-"log_trainer/netmob_nf_dl_small"}
LOG_TEST=${LOG_TEST:-"log_tester/netmob_nf_dl_small"}
CKPT_DIR=${CKPT_DIR:-"model/netmob_nf_dl_small"}

CHECKPOINT_FILE=${CHECKPOINT_FILE:-"catdim5_zdim10_cdim20_hdim20_winsize1_T20_l1"}
START_EPOCH_TEST=${START_EPOCH_TEST:-3}

EXPORT_DIR=${EXPORT_DIR:-"results/exports"}

echo "[1/4] Training..."
python SGmVRNN/trainer.py \
  --dataset_path "${DATASET_TRAIN}" \
  --gpu_id "${GPU_ID}" \
  --log_path "${LOG_TRAIN}" \
  --checkpoints_path "${CKPT_DIR}" \
  --epochs "${EPOCHS}" \
  --batch_size "${BATCH}" \
  --n "${N}" \
  --T "${T}"

echo "[2/4] Testing..."
python SGmVRNN/tester.py \
  --dataset_path "${DATASET_TEST}" \
  --gpu_id "${GPU_ID}" \
  --log_path "${LOG_TEST}" \
  --checkpoints_path "${CKPT_DIR}" \
  --checkpoints_file "${CHECKPOINT_FILE}" \
  --start_epoch "${START_EPOCH_TEST}" \
  --batch_size 1 \
  --n "${N}" \
  --T "${T}"

# Le fichier score est généré dans log_tester (ex: netmob_nf_dl_small_scores.txt)
SCORES_FILE=$(ls -1 "${LOG_TEST}"/*scores*.txt | head -n 1 || true)
if [[ -z "${SCORES_FILE}" ]]; then
  echo "❌ Aucun fichier scores trouvé dans ${LOG_TEST}"
  exit 1
fi

echo "[3/4] Export standard outputs (TXT + CSV)..."
python scripts/export_detections.py \
  --scores "${SCORES_FILE}" \
  --appli "${APPLI}" \
  --tile "${TILE}" \
  --start_date "${START_DATE}" \
  --out_dir "${EXPORT_DIR}" \
  --only_anomaly

echo "[4/4] Done ✅"
echo "Outputs:"
echo " - ${EXPORT_DIR}/${APPLI}_tile${TILE}_detections.txt"
echo " - ${EXPORT_DIR}/${APPLI}_tile${TILE}_detections.csv"
