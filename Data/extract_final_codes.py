"""Extract final code labels into JSONL records aligned with the GT names/order."""

import argparse
import json
from pathlib import Path

if __package__:
    from .jsonl_utils import read_records as read_gt_records, write_records
else:
    from jsonl_utils import read_records as read_gt_records, write_records


DATASETS = {
    "Scrum-interviews": (
        "rq_gt.jsonl",
        {"Scrum_RQ1": "rq1", "Scrum_RQ2": "rq2"},
    ),
    "StorySeeker": (
        "ground_truth.jsonl",
        {"goal": "goal", "rationale": "rationale"},
    ),
}

EXPERIMENTS = {
    "discuss": "discuss_process/json/discuss.json",
    "baseline1": "baseline1/json/baseline1.json",
    "baseline2": "discuss_process/json/baseline2.json",
}


def extract_codes(path):
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if "Final_codebook" in data:
        codebook = data["Final_codebook"]
    elif "Codebook" in data:
        codebook = data["Codebook"]
    else:
        codebook = data["codebook"]
    if isinstance(codebook, dict):
        codebook = codebook["codebook"]
    return [entry["code"] for entry in codebook]


def export_dataset(dataset_dir, model_name="gpt-4o"):
    dataset_dir = Path(dataset_dir)
    gt_filename, task_dirs = DATASETS[dataset_dir.name]
    gt_records = read_gt_records(dataset_dir / "processed" / gt_filename)
    output_dir = dataset_dir / f"{model_name}_output"

    # Resolve all inputs before writing any exports for this dataset.
    exports = {}
    for experiment, result_path in EXPERIMENTS.items():
        records = []
        for gt in gt_records:
            name = gt["name"]
            source = output_dir / task_dirs[name] / result_path
            records.append({"name": name, "code": extract_codes(source)})
        exports[output_dir / f"{experiment}_codes.jsonl"] = records

    for path, records in exports.items():
        write_records(path, records)
        print(f"Saved: {path} ({len(records)} records)")
    return list(exports)


def main():
    parser = argparse.ArgumentParser(
        description="Export final code labels in the same name/order as each dataset's GT."
    )
    parser.add_argument(
        "--data-dir", type=Path, default=Path(__file__).resolve().parent,
        help="Data directory (default: the directory containing this script).",
    )
    parser.add_argument("--model-name", default="gpt-4o")
    parser.add_argument(
        "--dataset", choices=tuple(DATASETS),
        help="Export one dataset; defaults to both datasets.",
    )
    args = parser.parse_args()
    datasets = [args.dataset] if args.dataset else DATASETS
    for dataset in datasets:
        export_dataset(args.data_dir / dataset, args.model_name)


if __name__ == "__main__":
    main()
