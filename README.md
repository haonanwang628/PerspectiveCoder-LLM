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
1. [Scrum-results](https://drive.google.com/drive/folders/1d6FLKN7mHcevlgLD-NaRlsu3wcjnqQ59)

| Baseline | Description | Results|
| --- | --- | --- |
| Baseline1 | Single LLM + no perspective+ no discussion | [Codebook](https://docs.google.com/spreadsheets/d/1Q9zWtavjbn8rpxlq_AppBRiWt0577Yy5/edit?gid=267776357#gid=267776357)|
| Baseline2 | Three LLM + the same setting perspective of three roles with PerspectiveCoder-LM + no discussion |[Codebook](https://docs.google.com/spreadsheets/d/1FrMmHN5jOaKnq2HQieIQrza4hmcMC2p_/edit?gid=221633652#gid=221633652)|
| PerspectiveCoder-LM |the perspective of three roles+ discussion process |[Codebook](https://docs.google.com/spreadsheets/d/1J70V_qEsVKNTsTc5v5WeV3SS1x8siR2e/edit?usp=sharing&ouid=112333598917962269336&rtpof=true&sd=true) |

2.[StoryPerceptions-results]()

| Baseline | Description | Results|
| --- | --- | --- |
| Baseline1 | Single LLM + no perspective+ no discussion | [Codebook](https://docs.google.com/spreadsheets/d/1WBpQSInN0WSolt6CP92Up6Q20DZhmUiF/edit?usp=drive_link&ouid=112333598917962269336&rtpof=true&sd=true)|
| Baseline2 | Three LLM + the same setting perspective of three roles with PerspectiveCoder-LM + no discussion |[Codebook](https://docs.google.com/spreadsheets/d/1vocQVkiynDyu4tFerINzN6PgqGnfEe8b/edit?usp=drive_link&ouid=112333598917962269336&rtpof=true&sd=true)|
| PerspectiveCoder-LM |the perspective of three roles+ discussion process |[Codebook](https://docs.google.com/spreadsheets/d/12D8lnvzckqTYcZHjVRhvXzcUfOfTTJW7/edit?usp=drive_link&ouid=112333598917962269336&rtpof=true&sd=true) |

## *Install*
### Features
- Multi-agent discussion pipeline (`experiment_discuss_flow`) that coordinates three coding agents plus reviewer, discussion lead, and judge roles.
- Single-agent baseline pipeline (`experiment_single_flow`) for comparison studies.
- Automatic creation of experiment output folders and JSON exports.
- Configurable through JSON configuration files and CLI arguments.

### Project Layout
```
PerspectiveCoder-LM/
├── main.py                 # CLI entry point (discuss & baseline flows)
├── config/                 # Model and discussion configuration JSON files
├── Data/                   # Source interviews and processed datasets
├── utils/                  # Core agent orchestration utilities
└── ...
```

### Requirements
- Python 3.10+
- Dependencies listed in `requirements.txt`
- Access to the target language models configured in `config/config.json`

```powershell
pip install -r requirements.txt
```

### Command-Line Usage
`main.py` exposes a single CLI with several switches:

```powershell
python main.py `
  --input-file F:\Work\Debate\PrivousPerspectiveCoder-LM\Data\Scrum-interviews\processed\Scrum.json `
  --output-dir F:\Work\Debate\PrivousPerspectiveCoder-LM\Data\Scrum-interviews\gpt-4o_output `
  --config-dir F:\Work\Debate\PrivousPerspectiveCoder-LM\config\config.json `
  --model-name gpt-4o `
  --research-question "1. How do Scrum practitioners define software quality?" `
  --experiment-name 0
```

### CLI Arguments
| Flag | Default | Description |
| --- | --- | --- |
| `-i`, `--input-file` | `Data/Scrum-interviews/processed/Scrum.json` | JSON dataset containing interview records. Each record may include a `code` field which is removed before processing. |
| `-o`, `--output-dir` | `Data/Scrum-interviews/gpt-4o_output` | Root directory where experiment results are stored. Subfolders are created automatically if missing. |
| `-c`, `--config-dir` | `config/config.json` | Discussion configuration consumed by `DiscussFlowModel`. |
| `-m`, `--model-name` | `gpt-4o` | Target LLM name. Accepts a single model or a list mapped to individual roles. |
| `-rq`, `--research-question` | `""` | Research question context injected into agent prompts. |
| `-exp`, `--experiment-name` | `0` | Experiment selector: `0` discuss flow, `1` single-agent baseline, `2` discuss flow with matched identities. |

### Experiment Outputs
Depending on the experiment, the script writes JSON summaries under the chosen `output_dir`:
- `discuss_process/json/discuss.json`: team discussion results with agreed and final codebooks plus token usage statistics.
- `baseline1/json/baseline1.json`: single-agent codebook for the baseline condition.

Experiment `0` and `2` require six roles (`Role1`, `Role2`, `Role3`, `Reviewer`, `Discussion`, `Judge`). Role identities are generated via `roles_identity_generate`, enriched with positionality and initial codebooks, and evaluated by the reviewer/discussion/judge trio. Experiment `1` runs only `Role1` through the baseline pipeline.

### Customisation Tips
- **Datasets**: Place new interview corpora under `Data/` and point `--input-file` at the desired JSON file.
- **Configurations**: Update `config/discuss_config*.json` or `config/config.json` to tweak model endpoints, prompt templates, and stage settings.
- **Role Assignments**: Pass a list to `--model-name` to mix different models across roles (e.g., `"gpt-4o,gpt-4o-mini,gpt-5"`).
- **Research Question**: Supply a domain-specific question with `--research-question` to adjust agent framing.

### Reproducing Default Run
1. Ensure the default dataset `Scrum.json` exists at the processed path.
2. Activate your environment and install dependencies.
3. Execute the command shown in *Command-Line Usage* with `--experiment-name 0`.
4. Inspect `Data/Scrum-interviews/gpt-4o_output/discuss_process/json/discuss.json` for the full discussion artifact.

### Troubleshooting
- Missing output folders: `main.py` creates the baseline and discussion directories when `--output-dir` does not exist, but upstream directories must already be present.
- Invalid model mapping: ensure the number of models in a list equals the number of coding roles (excluding reviewer/discussion/judge).
- JSON parsing errors: verify the dataset and configuration files contain valid UTF-8 encoded JSON.

## License
The repository inherits its license terms from `PerspectiveCoder-LM`. Add explicit licensing information here if required.
