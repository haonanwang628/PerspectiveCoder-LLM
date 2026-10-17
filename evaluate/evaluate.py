from functools import lru_cache

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


def compute_score(code_match, ground_truth, generate_code, self_num, use_count, total_count):
    scores = {
        "recall": len(code_match) / len(ground_truth),
        "match_rate": sum(len(matches) for matches in code_match.values()) / len(generate_code),
        "code_diversity": self_num / len(generate_code),
        "text_utilization_rate": use_count / total_count,
    }
    for name, value in scores.items():
        print(f"{name.replace('_', ' ')}: {value:.3f}")
    return scores

if __name__ == "__main__":