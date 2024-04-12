#!/usr/bin/env bash
DATASET_PATH="${PWD}/dataset/creditcard.csv"
SPLIT_PATH="${PWD}/dataset"
OUTPUT_PATH_VER="${PWD}/dataset/vertical_xgb_data_lite"
OUTPUT_FILE_VER="data.csv"

if [ ! -f "${DATASET_PATH}" ]
then
    echo "Please check if you saved CreditCard dataset in ${DATASET_PATH}"
fi

echo "Generating CreditCard data splits, reading from ${DATASET_PATH}"

python3 utils/prepare_data_split.py \
--data_path "${DATASET_PATH}" \
--test_ratio 0.2 \
--row_ratio 0.5 \
--out_folder "${SPLIT_PATH}"

python3 utils/prepare_data_vertical.py \
--data_path "${SPLIT_PATH}/train_lite.csv" \
--site_num 2 \
--out_path "${OUTPUT_PATH_VER}" \
--out_file "${OUTPUT_FILE_VER}"
