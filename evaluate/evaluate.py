from functools import lru_cache
import json
from pathlib import Path
import torch
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer
import matplotlib.pyplot as plt
import numpy as np

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


def match_codes(gt_list, pred_list, threshold=0.9, device="cpu"):
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



def group_codes(pred_list, threshold=0.9, device="cpu"):
    model, tokenizer = load_embedding_model(device)
    embeddings = get_embeddings(pred_list, model, tokenizer, device)
    visited = torch.zeros(len(pred_list), dtype=torch.bool)
    groups = []

    for index in range(len(pred_list)):
        if visited[index]:
            continue
        visited[index] = True
        similarities = (embeddings[index + 1:] @ embeddings[index] + 1) / 2
        matches = (similarities >= threshold) & ~visited[index + 1:]
        members = torch.nonzero(matches, as_tuple=True)[0].tolist()
        groups.append([pred_list[index]] + [pred_list[index + 1 + offset] for offset in members])
        visited[index + 1:] |= matches

    return groups

def plot_similarity_heatmap(
    gt_list,
    pred_list,
    output_path,
    device="cpu",
):
    """
    Plot cosine similarity heatmap between Ground Truth
    and Generated Codes without threshold filtering.

    Rows: Ground Truth Codes
    Columns: Generated Codes
    """

    if not gt_list or not pred_list:
        return

    model, tokenizer = load_embedding_model(device)

    gt_emb = get_embeddings(gt_list, model, tokenizer, device)
    pred_emb = get_embeddings(pred_list, model, tokenizer, device)

    # Original cosine similarity: [-1, 1]
    similarities = (gt_emb @ pred_emb.T + 1) / 2

    n_gt = len(gt_list)
    n_pred = len(pred_list)

    fig_width = max(10, n_pred * 0.9)
    fig_height = max(6, n_gt * 0.45)

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    im = ax.imshow(
        similarities,
        cmap="YlOrRd",
        vmin=-1,
        vmax=1,
        aspect="auto",
    )

    ax.set_xticks(np.arange(n_pred))
    ax.set_yticks(np.arange(n_gt))

    ax.set_xticklabels(
        pred_list,
        rotation=45,
        ha="right",
        fontsize=9,
    )

    ax.set_yticklabels(
        gt_list,
        fontsize=9,
    )

    ax.set_xlabel("Generated Codes", fontsize=12)
    ax.set_ylabel("Ground Truth Codes", fontsize=12)
    ax.set_title("GT vs Generated Codes: Cosine Similarity", fontsize=13)

    # Display cosine similarity values
    for i in range(n_gt):
        for j in range(n_pred):
            ax.text(
                j,
                i,
                f"{similarities[i, j]:.2f}",
                ha="center",
                va="center",
                fontsize=8,
                color="black",
            )

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Cosine Similarity")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved heatmap: {output_path}")


def self_match(pred_list, threshold=0.9, device="cpu"):
    return len(group_codes(pred_list, threshold, device))


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
    experiments = ("discuss", "baseline1", "baseline2","before_discuss")
    threshold = 0.8
    device = "cpu"
    datasets = {
        "Scrum-interviews": "rq_gt.jsonl",
        "StorySeeker": "ground_truth.jsonl",
    }

    for dataset, gt_filename in datasets.items():
        dataset_dir = data_dir / dataset
        output_dir = dataset_dir / f"{model_name}_output"

        gt_records = read_records(dataset_dir / "processed" / gt_filename)
        gt_results = []
        for record in gt_records:
            ground_truth = record["ground_truth"]
            groups = group_codes(ground_truth, threshold, device)
            cluster_count = len(groups)
            gt_results.append({
                "name": record["name"],
                "threshold": threshold,
                "ground_truth_count": len(ground_truth),
                "cluster_count": cluster_count,
                "code_diversity": cluster_count / len(ground_truth),
                "groups": groups,
            })
        write_records(output_dir / "gt_evaluation.jsonl", gt_results)

        for experiment in experiments:
            pred_file = output_dir / f"{experiment}_codes.jsonl"
            pred_records = read_records(pred_file)
            predictions = {record["name"]: record["code"] for record in pred_records}
            if len(predictions) != len(pred_records):
                raise ValueError(f"{dataset}: {pred_file.name} 包含重复的 name")
            if set(predictions) != {record["name"] for record in gt_records}:
                raise ValueError(f"{dataset}: GT 与 {pred_file.name} 的 name 不一致")

            results = []
            for record in gt_records:
                name = record["name"]
                ground_truth = record["ground_truth"]
                generate_code = predictions[name]
                print(f"\n{dataset} / {experiment} / {name}")

                code_match = match_codes(ground_truth, generate_code, threshold, device)
                self_num = self_match(generate_code, threshold, device)
                scores = compute_score(code_match, ground_truth, generate_code, self_num)
                heatmap_path = output_dir / "heatmaps" / f"{experiment}_{name}.png"

                plot_similarity_heatmap(
                    gt_list=ground_truth,
                    pred_list=generate_code,
                    output_path=heatmap_path,
                    device=device,
                )
                results.append({
                    "name": name,
                    "threshold": threshold,
                    "ground_truth_count": len(ground_truth),
                    "predicted_code_count": len(generate_code),
                    "code_match": code_match,
                    "scores": scores,
                })

            output_file = output_dir / f"{experiment}_evaluation.jsonl"
            write_records(output_file, results)
            print(f"Saved: {output_file}")
