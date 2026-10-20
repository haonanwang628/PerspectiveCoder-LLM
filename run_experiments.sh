#!/usr/bin/env bash
# 在项目根目录运行：bash run_experiments.sh

model_name="gpt-4o"

run_experiments() {
    local input_file="$1"
    local output_dir="$2"
    local rq_file="$3"
    local experiment

    # 0: discuss；1: baseline1；2: baseline2
    for experiment in 0 1 2; do
        python main.py -i "$input_file" -o "$output_dir" \
            -m "$model_name" -rq "$rq_file" -exp "$experiment"
    done

    # 将三组实验结果分别转换为 Excel
    python Data/discuss_json_to_excel.py \
        -i "$output_dir/discuss_process/json/discuss.json" \
        -o "$output_dir/discuss_process/excel/discuss.xlsx"
    python Data/baseline1_json_to_excel.py \
        -i "$output_dir/baseline1/json/baseline1.json" \
        -o "$output_dir/baseline1/excel/baseline1.xlsx"
    python Data/discuss_json_to_excel.py \
        -i "$output_dir/discuss_process/json/baseline2.json" \
        -o "$output_dir/discuss_process/excel/baseline2.xlsx"
}

# Scrum：RQ1、RQ2
for rq in 1 2; do
    run_experiments \
        "Data/Scrum-interviews/processed/First Cycle - RQ${rq}.json" \
        "Data/Scrum-interviews/${model_name}_output/rq${rq}" \
        "Data/Scrum-interviews/processed/rq${rq}.txt"
done

# StorySeeker：goal、rationale
for task in goal rationale; do
    run_experiments \
        "Data/StorySeeker/processed/${task}.json" \
        "Data/StorySeeker/${model_name}_output/${task}" \
        "Data/StorySeeker/processed/rq.txt"
done

