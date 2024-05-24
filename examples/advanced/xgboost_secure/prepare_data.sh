#!/usr/bin/env bash
DATASET_PATH="${PWD}/dataset/creditcard.csv"
SPLIT_PATH="${PWD}/dataset"

if [ ! -f "${DATASET_PATH}" ]
then
    echo "Please check if you saved CreditCard dataset in ${DATASET_PATH}"
fi

echo "Generating CreditCard data splits, reading from ${DATASET_PATH}"

echo "Split data to training/validation v.s. testing"
python3 utils/prepare_data_traintest_split.py \
--data_path "${DATASET_PATH}" \
--test_ratio 0.2 \
--out_folder "${SPLIT_PATH}"

echo "Split training/validation data"
OUTPUT_PATH="${PWD}/dataset/base_xgb_data"
python3 utils/prepare_data_base.py \
--data_path "${SPLIT_PATH}/train.csv" \
--out_path "${OUTPUT_PATH}"

echo "Split training/validation data vertically"
OUTPUT_PATH="${PWD}/dataset/vertical_xgb_data"
python3 utils/prepare_data_vertical.py \
--data_path "${SPLIT_PATH}/train.csv" \
--site_num 3 \
--out_path "${OUTPUT_PATH}"

echo "Split training/validation data horizontally"
OUTPUT_PATH="${PWD}/dataset/horizontal_xgb_data"
python3 utils/prepare_data_horizontal.py \
--data_path "${SPLIT_PATH}/train.csv" \
--site_num 3 \
--out_path "${OUTPUT_PATH}"

echo "Split training/validation data both verically and horizontally"
OUTPUT_PATH="${PWD}/dataset/test_col_xgb_data"
python3 utils/prepare_data_col_tests.py \
--data_path "${SPLIT_PATH}/train.csv" \
--site_num 2 \
--out_path "${OUTPUT_PATH}"
