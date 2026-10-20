import argparse
from utils.Agent_discuss import DiscussFlowModel
from utils.Function import import_json, save_json, roles_identity_generate
import os
import json
from pathlib import Path
from config.discuss_menu import Scrum_positionality, StorySeeker_positionality

def experiment_discuss_flow(roles, roles_identity, texts, model_name, discuss_config, output_file, rq=None):
    if isinstance(model_name, list):
        models_name = dict(zip(roles, model_name))
    elif isinstance(model_name, str):
        models_name = {role: model_name for role in roles}
    else:
        return
    datasets = []

    for _, text in enumerate(texts):
        text.pop("code", None)
        datasets.append(text)

    discuss_flow = DiscussFlowModel(discuss_config, models_name)
    discuss_flow.target_text = json.dumps(
        {
            "columns": ["participant", "data_chunk"],
            "rows": [
                [item["participant"], item["data_chunk"]]
                for item in datasets
            ],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )

    roles = discuss_flow.agents_init()
    Reviewer, Judge = roles[3], roles[4]

    roles = roles[:3]
    roles_positionality, roles_init_codebook = discuss_flow.roles_stage(roles, roles_identity, rq=rq)

    for role_id, positionality, role_init_codebook in zip(roles_identity, roles_positionality, roles_init_codebook):
        role_id["positionality"] = positionality
        role_id["init_codebook"] = role_init_codebook["codebook"]
        # print(role_init_codebook["codebook"])

    init_codebook = []
    for role_identity in roles_identity:
        init_codebook.append(
            {
                    "role": "|".join(
                    f"{dimension}: {value}"
                    for dimension, value in role_identity.items()
                    if dimension not in ("positionality", "init_codebook")
                ),
                "codebook": role_identity["init_codebook"]})

    agreed_disagreed_codebook = discuss_flow.codebook_reviewer(Reviewer, init_codebook)

    disagreements = agreed_disagreed_codebook["disagreements"]
    exist_disagreements = bool(disagreements) and isinstance(disagreements[0], dict)

    result = {
        "Role_Team": roles_identity,
        "Agreed_disagreed_codebook": agreed_disagreed_codebook,
    }

    decision_agreed_codebook = None
    if exist_disagreements:
        decision_agreed_codebook, discuss_process = discuss_flow.codebook_discussion(
            roles, roles_identity, roles_positionality, agreed_disagreed_codebook
        )
        result["Discussion"] = discuss_process

    result["Final_codebook"] = discuss_flow.codebook_judge(
        Judge, init_codebook, agreed_disagreed_codebook, decision_agreed_codebook, rq=rq
    )
    result["current_num_token"] = {
        "input_token": discuss_flow.input_token,
        "output_token": discuss_flow.output_token,
    }

    chat_history = {"memory_lst": {agent.name: agent.memory_lst for agent in roles + [Reviewer, Judge]}}

    output_prefix = f"{args.output_dir}/discuss_process/json/{output_file}"
    save_json(f"{output_prefix}.json", result)
    save_json(f"{output_prefix}_chat_history.json", chat_history)

    if not exist_disagreements:
        return 0

    
def experiment_single_flow(role, texts, model_name, discuss_config, rq=None):
    role_name = role[0]
    models_name = {role_name: model_name}
    datasets = []

    for _, text in enumerate(texts):
        text.pop("code", None)
        datasets.append(text)

    single_flow = DiscussFlowModel(discuss_config, models_name)
    single_flow.target_text = json.dumps(
        {
            "columns": ["participant", "data_chunk"],
            "rows": [
                [item["participant"], item["data_chunk"]]
                for item in datasets
            ],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )

    role = single_flow.agents_init()
    role_codebook = single_flow.role_stage(role[0], rq=rq)

    result = {
        "Role": role_name,
        "Codebook": role_codebook["codebook"],
    }

    save_json(f"{args.output_dir}/baseline1/json/baseline1.json", result)


def parse_args():
    parser = argparse.ArgumentParser("", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-i", "--input-file", type=str,
                        default="Data/Scrum-interviews/processed/First Cycle - RQ1.json",
                        help="raw_text Input file path")
    parser.add_argument("-o", "--output-dir", type=str,
                        default="Data/Scrum-interviews/gpt-4o_output/rq1",
                        help="Codebook and discuss output file dir")
    parser.add_argument("-c", "--config-dir", type=str,
                        default="config/config.json",
                        help="config file dir")
    parser.add_argument("-m", "--model-name", type=str, default="gpt-4o", help="Model name")
    # parser.add_argument("-t", "--temperature", type=float, default=0, hewlp="Sampling temperature")

    # 旧代码（保留供参考）：
    # parser.add_argument("-rq", "--research-question", type=read_txt, default="Data/Scrum-interviews/processed/rq1.txt", help="Data iteration starting step")
    parser.add_argument("-rq", "--research-question", type=read_txt,
                        default="Data/Scrum-interviews/processed/rq1.txt",
                        help="UTF-8 research question txt path, or None to omit the research question")
    # 旧代码（保留供参考）：
    # parser.add_argument("-exp", "--experiment-name", type=int, default=0,
    #                     help="0: discuss, 1: baseline1, 2: baseline2")
    parser.add_argument("-exp", "--experiment-name", type=int, choices=(0, 1, 2), default=2,
                        help="0: discuss, 1: baseline1, 2: baseline2")

    return parser.parse_args()


def read_txt(path):

    if path is None or path.strip().lower() == "none":
        return None
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise argparse.ArgumentTypeError(f"Cannot read research question file: {exc}") from exc

if __name__ == "__main__":
    args = parse_args()

    target_texts = import_json(args.input_file)
    config = import_json(args.config_dir)

    if args.experiment_name in (0, 2):
        if "scrum" in args.input_file.lower():
            positionality = Scrum_positionality
        elif "storyseeker" in args.input_file.lower():
            positionality = StorySeeker_positionality
        else:
            raise ValueError(f"Unknown input file type for positionality: {args.input_file}")
    
    for subdir in ("baseline1/json", "discuss_process/json"):
        (Path(args.output_dir) / subdir).mkdir(parents=True, exist_ok=True)

    if args.experiment_name == 0:
        roles = ["Role1", "Role2", "Role3", "Reviewer", "Judge"]
        roles_identity = roles_identity_generate(len(roles) - 2, positionality)
        experiment_discuss_flow(roles, roles_identity, target_texts, args.model_name, config, "discuss", args.research_question)
    elif args.experiment_name == 1:
        roles = ["Role1"]
        experiment_single_flow(roles, target_texts, args.model_name, config, args.research_question)
    elif args.experiment_name == 2:
        roles = ["Role1", "Role2", "Role3", "Reviewer", "Judge"]
        roles_identity = roles_identity_generate(1, positionality)
        roles_identity = [roles_identity[0].copy() for _ in range(3)]
        experiment_discuss_flow(roles, roles_identity, target_texts, args.model_name, config, "baseline2", args.research_question)
