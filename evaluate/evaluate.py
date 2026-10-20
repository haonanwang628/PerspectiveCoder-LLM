from functools import lru_cache
import json
from pathlib import Path
import torch
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer


@lru_cache(maxsize=1)
def load_embedding_model(device="cpu"):
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name).to(device)
    model.eval()
    return model, tokenizer


def get_embeddings(texts, model, tokenizer, device="cpu", batch_size=32):
    batches = []
    with torch.inference_mode():
        for start in range(0, len(texts), batch_size):
            inputs = tokenizer(texts[start:start + batch_size], 
                               padding=True, truncation=True, return_tensors="pt",).to(device)
            hidden = model(**inputs).last_hidden_state.float()
            mask = inputs["attention_mask"].unsqueeze(-1)
            pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1)
            batches.append(F.normalize(pooled, p=2, dim=1).cpu())
    return torch.cat(batches, dim=0)


def match_codes(gt_list, pred_list, threshold=0.7, device="cpu"):
    model, tokenizer = load_embedding_model(device)
    gt_emb = get_embeddings(gt_list, model, tokenizer, device)
    pred_emb = get_embeddings(pred_list, model, tokenizer, device)

    similarities = (gt_emb @ pred_emb.T + 1) / 2
    scores, indices = similarities.max(dim=0)
    accepted = torch.nonzero(scores >= threshold, as_tuple=True)[0].tolist()
    best_indices = indices.tolist()

    result = {}
    for index in accepted:
        gt_code = gt_list[best_indices[index]]
        result.setdefault(gt_code, []).append(pred_list[index])
    return result


def self_match(pred_list, threshold=0.7, device="cpu"):
    model, tokenizer = load_embedding_model(device)
    embeddings = get_embeddings(pred_list, model, tokenizer, device)
    visited = torch.zeros(len(pred_list), dtype=torch.bool)
    cluster_count = 0

    for index in range(len(pred_list)):
        if visited[index]:
            continue
        cluster_count += 1
        visited[index] = True
        similarities = (embeddings[index + 1:] @ embeddings[index] + 1) / 2
        visited[index + 1:] |= similarities >= threshold

    return cluster_count


def compute_score(code_match, ground_truth, generate_code, self_num):
    scores = {
        "recall": len(code_match) / len(ground_truth),
        "match_rate": sum(len(matches) for matches in code_match.values()) / len(generate_code),
        "code_diversity": self_num / len(generate_code),
    }
    for name, value in scores.items():
        print(f"{name.replace('_', ' ')}: {value:.3f}")
    return scores

if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from Data.jsonl_utils import read_records, write_records

    data_dir = Path(__file__).resolve().parents[1] / "Data"
    model_name = "gpt-4o"
    threshold = 0.7
    device = "cpu"
    datasets = {
        "Scrum-interviews": "rq_gt.jsonl",
        "StorySeeker": "ground_truth.jsonl",
    }

    for dataset, gt_filename in datasets.items():
        dataset_dir = data_dir / dataset
        output_dir = dataset_dir / f"{model_name}_output"

        gt_records = read_records(dataset_dir / "processed" / gt_filename)
        pred_records = read_records(output_dir / "discuss_codes.jsonl")
        predictions = {record["name"]: record["code"] for record in pred_records}
        if len(predictions) != len(pred_records):
            raise ValueError(f"{dataset}: discuss_codes.jsonl 包含重复的 name")
        if set(predictions) != {record["name"] for record in gt_records}:
            raise ValueError(f"{dataset}: GT 与 discuss_codes.jsonl 的 name 不一致")

        results = []
        for record in gt_records:
            name = record["name"]
            ground_truth = record["ground_truth"]
            generate_code = predictions[name]
            print(f"\n{dataset} / {name}")

            code_match = match_codes(ground_truth, generate_code, threshold, device)
            self_num = self_match(generate_code, threshold, device)
            scores = compute_score(code_match, ground_truth, generate_code, self_num)
            results.append({
                "name": name,
                "threshold": threshold,
                "ground_truth_count": len(ground_truth),
                "predicted_code_count": len(generate_code),
                "code_match": code_match,
                "scores": scores,
            })

        output_file = output_dir / "discuss_evaluation.jsonl"
        write_records(output_file, results)
        print(f"Saved: {output_file}")
