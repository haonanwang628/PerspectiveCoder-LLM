# PerspectiveCoder-LM: A LLM-based Multi-perspective-agent System for Large-scale Corpus Inductive Coding Analysis 
| [**Paper**]()|

We propose PerspectiveCoder-LM, an LLM-based multi-perspective-agent system for large-scale inductive coding, which generates qualitative research codebooks with multi-agent large language model discussions by simulating multiple perspectives. PerspectiveCoder-LM assigns specialised tasks to each agent, such as role-generating multi-perspective positionality statements, inductive coding, review agreements/disagreements of codebooks, and discussion codebooks.

<p align="center">
  <sub>System Introduction</sub>  
</p> 

<p align="center">
  <a href="https://latitude.so/developers?utm_source=github&utm_medium=readme&utm_campaign=prompt_repo_sponsorship" target="_blank">
    <img src="Images/systemintro.png" alt="Logo" width="700"/>
  </a>
</p>

## Contents

- [Introduction](#Introduction) [Project Management](https://docs.google.com/document/d/1yQeDEgtlWTl9SLAgr3bBJ9_l59sWQwWXsGzLFwkRVKY/edit?tab=t.utp4mklu2c15)
- [Install](#install)
- [Model Configuration](#model-configuration)
- [Local Model](#local-model)
- [Evaluation](#evaluation)
# Introduction



### LLM-based Multi-agent System 
| Agent | Description|
| --- | --- | 
| Facilitator-Agent | Provide a **Prologue** for (human-AI interaction system): introduce the workflow, set the stage, or remind all agents of their roles and so on|
| Role-Agent | Generate a **Positionality Statement** for every role to simulate the multi-perspective coding(Identity, Academic Level, Discipline, Research Interests, Biases/Assumptions, etc.)|
| Coder-Agent | For each role: Use the Positionality Statement to perform **Open Coding**, generate a full **initial codebook from every role**. |
| Reviewer-Agent | Review all **Codebook-Agreements/Disagreements** from the three role-generating initial codebooks|
| Discussion-Agent | Combine their disagreements, start the **discussion process** |
| Judge-Agent | **Decide what codes remain or are dropped** and produce the final codebook|

### Experiments and Analysis
#### Datasets
1. Scrum-[How Scrum Adds Value to Achieving Software Quality?](https://zenodo.org/records/6624064)
2. StoryPerceptions-[StoryPerceptions (EMNLP 2024): crowd “perceptions” + inductively derived code taxonomy + annotator demographics](https://maria-antoniak.github.io/resources/2024_emnlp_story_perceptions.pdf)
3. [Towards Designing a QA Chatbot for Online News (arXiv 2312.10650): open-coded question taxonomy + OSF release](https://ar5iv.labs.arxiv.org/html/2312.10650)
4. [The HaLLMark Effect (arXiv 2311.13057): open-coded policy recommendations + “coded policies” released on OSF](https://ar5iv.labs.arxiv.org/html/2311.13057)
6. [Social Bias Frames](https://maartensap.com/social-bias-frames/)
7. [Social Chemistry](https://maxwellforbes.com/social-chemistry/)
#### Codebook Format

#### Study 1: 
1. [Scrum-results](Data/Scrum-interviews/gpt-4o_output/)

| Baseline | Description | Results|
| --- | --- | --- |
| Baseline1 | Single LLM + no perspective+ no discussion | [RQ1](Data/Scrum-interviews/gpt-4o_output/rq1/baseline1/excel/baseline1.xlsx), [RQ2](Data/Scrum-interviews/gpt-4o_output/rq2/baseline1/excel/baseline1.xlsx) |
| Baseline2 | Three LLM + the same setting perspective of three roles with PerspectiveCoder-LM + discussion | [RQ1](Data/Scrum-interviews/gpt-4o_output/rq1/discuss_process/excel/baseline2.xlsx), [RQ2](Data/Scrum-interviews/gpt-4o_output/rq2/discuss_process/excel/baseline2.xlsx) |
| PerspectiveCoder-LM |the perspective of three roles+ discussion process | [RQ1](Data/Scrum-interviews/gpt-4o_output/rq1/discuss_process/excel/discuss.xlsx), [RQ2](Data/Scrum-interviews/gpt-4o_output/rq2/discuss_process/excel/discuss.xlsx) |

2. [StoryPerceptions-results](Data/StorySeeker/gpt-4o_output/)

| Baseline | Description | Results|
| --- | --- | --- |
| Baseline1 | Single LLM + no perspective+ no discussion | [Goal](Data/StorySeeker/gpt-4o_output/goal/baseline1/excel/baseline1.xlsx), [Rationale](Data/StorySeeker/gpt-4o_output/rationale/baseline1/excel/baseline1.xlsx) |
| Baseline2 | Three LLM + the same setting perspective of three roles with PerspectiveCoder-LM +  discussion | [Goal](Data/StorySeeker/gpt-4o_output/goal/discuss_process/excel/baseline2.xlsx), [Rationale](Data/StorySeeker/gpt-4o_output/rationale/discuss_process/excel/baseline2.xlsx) |
| PerspectiveCoder-LM |the perspective of three roles+ discussion process | [Goal](Data/StorySeeker/gpt-4o_output/goal/discuss_process/excel/discuss.xlsx), [Rationale](Data/StorySeeker/gpt-4o_output/rationale/discuss_process/excel/discuss.xlsx) |

## *Install*
### Features
- Multi-agent coding, review, discussion, and final adjudication.
- Single-agent and shared-positionality baselines.
- API models and local Hugging Face models.

### Project Layout
```
PerspectiveCoder-LM/
├── main.py                 # CLI entry point (discuss & baseline flows)
├── config/                 # Model settings, positionality, and prompts
├── Data/                   # Source interviews and processed datasets
├── models/                 # Model download script and local weights
├── evaluate/               # Code matching and evaluation
├── utils/                  # Core agent orchestration utilities
└── run_experiments.sh      # Scrum and StorySeeker experiments
```

### Requirements
- Python 3.10+
- PyTorch and dependencies listed in `requirements.txt`
- For API models, configure credentials and endpoints in `config/model_menu.py`

```bash
pip install -r requirements.txt
```

### Model Configuration
Add or update model settings at the end of `config/model_menu.py`:

```python
import os

model_name = "gpt-4o"
api_key[model_name] = os.getenv("OPENAI_API_KEY")
base_url[model_name] = None  # Or your provider's API base URL.
llm_MaxToken[model_name] = 128000
MODEL_TOKENIZER_MAP[model_name] = "cl100k_base"
if model_name not in available_models:
    available_models.append(model_name)
```

Set the key before running:

```bash
export OPENAI_API_KEY="YOUR_API_KEY"
```

For another API model, change the name, endpoint, context limit, and tokenizer encoding, then pass the same name to `-m`. Local models use their directory path and do not require entries in `model_menu.py`.

### Command-Line Usage
Run from the project root:

```bash
python main.py \
  -i "Data/Scrum-interviews/processed/First Cycle - RQ1.json" \
  -o Data/Scrum-interviews/gpt-4o_output/rq1 \
  -c config/config.json \
  -m gpt-4o \
  -rq Data/Scrum-interviews/processed/rq1.txt \
  -exp 0
```

Use `-rq None` to run without a research question.

### Local Model
Download the model:

```bash
python models/download_model.py \
  --model-id Qwen/Qwen2.5-1.5B-Instruct \
  --model-dir models/Qwen2.5-1.5B-Instruct
```

Pass the downloaded directory to `-m`:

```bash
python main.py \
  -i "Data/Scrum-interviews/processed/First Cycle - RQ1.json" \
  -o Data/Scrum-interviews/Qwen2.5-1.5B-Instruct_output/rq1 \
  -m models/Qwen2.5-1.5B-Instruct \
  -rq Data/Scrum-interviews/processed/rq1.txt \
  -exp 0
```

### Parser Arguments

| Flag | Default | Description |
| --- | --- | --- |
| `-i`, `--input-file` | `Data/Scrum-interviews/processed/First Cycle - RQ1.json` | JSON records with `participant` and `data_chunk`; existing `code` labels are excluded from prompts. |
| `-o`, `--output-dir` | `Data/Scrum-interviews/gpt-4o_output/rq1` | Experiment output directory. |
| `-c`, `--config-dir` | `config/config.json` | Agent prompts and discussion settings. |
| `-m`, `--model-name` | `gpt-4o` | API model name or local model directory. |
| `-rq`, `--research-question` | `Data/Scrum-interviews/processed/rq1.txt` | UTF-8 TXT file path, or `None`. |
| `-exp`, `--experiment-name` | `2` | `0`: discussion with different positionalities; `1`: single-agent baseline; `2`: discussion with shared positionality. |

### Experiment Outputs
Paths relative to `--output-dir`:

| Experiment | JSON Output |
| --- | --- |
| `0` | `discuss_process/json/discuss.json` |
| `1` | `baseline1/json/baseline1.json` |
| `2` | `discuss_process/json/baseline2.json` |

### Batch Experiments
Run all Scrum and StorySeeker experiments and export Excel files:

```bash
bash run_experiments.sh
```

Results are saved under `Data/<dataset>/gpt-4o_output/<task>/`.

### Evaluation
After completing the experiments, extract code lists and evaluate:

```bash
python -m Data.extract_final_codes --model-name gpt-4o
python evaluate/evaluate.py
```

Extraction produces `discuss_codes.jsonl`, `baseline1_codes.jsonl`, and `baseline2_codes.jsonl`. The evaluator evaluates all three methods, matching records to GT by `name`.

| Dataset | Ground Truth |
| --- | --- |
| Scrum-interviews | `Data/Scrum-interviews/processed/rq_gt.jsonl` |
| StorySeeker | `Data/StorySeeker/processed/ground_truth.jsonl` |

Code matching uses `sentence-transformers/all-MiniLM-L6-v2` (downloaded on first use), with similarity `(cosine + 1) / 2` and threshold `0.7`.

| Metric | Calculation |
| --- | --- |
| Recall | Matched GT codes / total GT codes |
| Match rate | Matched generated codes / total generated codes |
| Code diversity | Greedy similarity groups / total generated codes |

Results: `Data/<dataset>/gpt-4o_output/{discuss,baseline1,baseline2}_evaluation.jsonl`. For other models, change `--model-name` during extraction and `model_name` in `evaluate/evaluate.py`; `threshold` and `device` are set there too.

#### Evaluation Results (gpt-4o)

Scrum1 and Scrum2 correspond to Scrum RQ1 and RQ2; Story1 and Story2 correspond to StorySeeker goal and rationale. Values are rounded to three decimal places, with a matching threshold of `0.7`. Parentheses show the numerator/denominator used to calculate each metric. Mean is the unweighted arithmetic average across the four tasks, calculated before rounding.

**Baseline 1**

| Metric | Scrum1 | Scrum2 | Story1 | Story2 | Mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| Recall | 0.176 (3/17) | 0.150 (6/40) | 0.150 (3/20) | 0.200 (2/10) | 0.169 |
| Match rate | 1.000 (5/5) | 1.000 (6/6) | 0.625 (5/8) | 0.800 (4/5) | 0.856 |
| Diversity | 0.400 (2/5) | 1.000 (6/6) | 0.875 (7/8) | 0.600 (3/5) | 0.719 |

**Baseline 2**

| Metric | Scrum1 | Scrum2 | Story1 | Story2 | Mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| Recall | 0.176 (3/17) | 0.175 (7/40) | 0.150 (3/20) | 0.400 (4/10) | 0.225 |
| Match rate | 0.667 (4/6) | 1.000 (7/7) | 0.800 (4/5) | 0.800 (4/5) | 0.817 |
| Diversity | 0.500 (3/6) | 1.000 (7/7) | 0.800 (4/5) | 0.600 (3/5) | 0.725 |

**PerspectiveCoder-LM (Discuss)**

| Metric | Scrum1 | Scrum2 | Story1 | Story2 | Mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| Recall | 0.235 (4/17) | 0.200 (8/40) | 0.100 (2/20) | 0.200 (2/10) | 0.184 |
| Match rate | 1.000 (6/6) | 1.000 (8/8) | 0.400 (2/5) | 0.800 (4/5) | 0.800 |
| Diversity | 0.500 (3/6) | 0.875 (7/8) | 1.000 (5/5) | 0.600 (3/5) | 0.744 |


**Ground Truth**

GT diversity uses the same embedding model, threshold, greedy grouping algorithm, and original code order as predicted-code diversity. Results are saved to `Data/<dataset>/gpt-4o_output/gt_evaluation.jsonl`.

| Metric | Scrum1 | Scrum2 | Story1 | Story2 | Mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| GT diversity | 0.471 (8/17) | 0.400 (16/40) | 0.900 (18/20) | 0.900 (9/10) | 0.668 |

Scrum RQ2 uses the original 40 GT entries, including the duplicate `Feedback` label.

#### GT Code Groups

Each list is one greedy similarity group at threshold `0.7`. The first code is the representative; remaining codes meet the threshold against it. Codes within a group are not necessarily similar to every other member. Original order and duplicate entries are preserved; each entry appears in exactly one group.

**Scrum1 (RQ1): 8 groups / 17 codes**

1. [`Conformity to business needs`, `Add business value`, `Meets the business needs`, `Conformity to business requirements`]
2. [`Free of defects`]
3. [`Usability`, `Maintainability`, `Code readability`]
4. [`Software performance`, `Software security`, `Code quality`, `Memory management`]
5. [`Sustainable design`]
6. [`Reusability of code`, `Clean code`]
7. [`Avoiding technical debt`]
8. [`Simplicity`]

**Scrum2 (RQ2): 16 groups / 40 codes**

1. [`Collaboration`, `Knowledge sharing`, `Peer to peer learning`, `Support the collective effort to achieve quality`]
2. [`Early engagement of QAs`]
3. [`Psychological safety`]
4. [`Transparency`]
5. [`Accountability`, `Technical integrity`]
6. [`Understanding the requirements`, `knowledge of business requirements`, `Meets the business needs`]
7. [`Feedback`, `Quality review`, `Feedback`, `Continuous feedback`, `Improved quality`, `Better quality`]
8. [`Speaking up`]
9. [`Investing on quality`, `Caring about quality`, `Effort on quality`, `Taking ownership for quality`, `Commitment to quality`, `Motivation for quality`, `Ownership of quality`, `Focus on quality`, `Control over quality`, `Software quality`, `Increase quality`, `Code quality`]
10. [`Iterative development`]
11. [`Modularity of tasks`]
12. [`Frequent testing`]
13. [`Inspection and adaptation`]
14. [`Fewer bugs`, `Bugs resolution`]
15. [`Better code`, `Better product`]
16. [`Scalability`]

**Story1 (goal): 18 groups / 20 codes**

1. [`character_person`, `literary_device`]
2. [`event_experience`]
3. [`plot_sequence`]
4. [`problem_conflict`]
5. [`setting_background`]
6. [`theme_moral`]
7. [`fictional_hypothetical`]
8. [`evocative_transporting`]
9. [`cohesive_interpretable`]
10. [`suspenseful`]
11. [`creative`]
12. [`feels_like_story`, `emotion_sensation`]
13. [`implicitly_revealing`]
14. [`opinion`]
15. [`behavior_strategy`]
16. [`concept_definition`]
17. [`artifact`]
18. [`time`]

**Story2 (rationale): 9 groups / 10 codes**

1. [`narrative_story`]
2. [`question_request`]
3. [`explanation`, `sense-making`]
4. [`description_expression`]
5. [`argument_suggestion_rant`]
6. [`review`]
7. [`dialogue`]
8. [`entertainment`]
9. [`specialized_domain`]

## License
The repository inherits its license terms from `PerspectiveCoder-LM`. Add explicit licensing information here if required.
