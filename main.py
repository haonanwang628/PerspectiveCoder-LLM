import argparse
from utils.Agent_discuss import DiscussFlowModel
from utils.Function import import_json, save_json, roles_identity_generate
import os


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
    discuss_flow.target_text = str(datasets)

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
                "role": f"{role_identity['Race_Ethnicity']}|{role_identity['Education']}|{role_identity['Gender']}|{role_identity['Age']}|{role_identity['Reddit_Use']}",
                "codebook": role_identity["init_codebook"]})

    agreed_disagreed_codebook = discuss_flow.codebook_reviewer(Reviewer, init_codebook)
    if not agreed_disagreed_codebook["disagreements"] or not isinstance(agreed_disagreed_codebook["disagreements"][0], dict):
        final_codebook = discuss_flow.codebook_judge(Judge, init_codebook, agreed_disagreed_codebook,
                                                     "", rq)
        result = {
            "Role_Team": roles_identity,
            "Agreed_disagreed_codebook": agreed_disagreed_codebook,
            "Final_codebook": final_codebook,
            "current_num_token": {"input_token": discuss_flow.input_token,
                                  "output_token": discuss_flow.output_token}
        }
        save_json(f"{args.output_dir}\\discuss_process\\json\\{output_file}.json", result)
        return 0
    decision_agreed_codebook, discuss_process = discuss_flow.codebook_discussion(roles, roles_identity,
                                                                                 roles_positionality,
                                                                                 agreed_disagreed_codebook)

    final_codebook = discuss_flow.codebook_judge(Judge, init_codebook, agreed_disagreed_codebook,
                                                 decision_agreed_codebook, rq)

    result = {
        "Role_Team": roles_identity,
        "Agreed_disagreed_codebook": agreed_disagreed_codebook,
        "Discussion": discuss_process,
        "Final_codebook": final_codebook,
        "current_num_token": {"input_token": discuss_flow.input_token,
                              "output_token": discuss_flow.output_token}
    }
    save_json(f"{args.output_dir}\\discuss_process\\json\\{output_file}.json", result)


def experiment_single_flow(role, texts, model_name, discuss_config, rq=None):
    role_name = role[0]
    models_name = {role_name: model_name}
    datasets = []

    for _, text in enumerate(texts):
        text.pop("code", None)
        datasets.append(text)

    single_flow = DiscussFlowModel(discuss_config, models_name)
    single_flow.target_text = str(datasets)

    role = single_flow.agents_init()
    role_codebook = single_flow.role_stage(role[0], rq=rq)

    result = {
        "Role": role_name,
        "Codebook": role_codebook["codebook"],
    }

    save_json(f"{args.output_dir}\\baseline1\\json\\baseline1.json", result)


def parse_args():
    parser = argparse.ArgumentParser("", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-i", "--input-file", type=str,
                        default=r"F:\Work\Debate\PrivousPerspectiveCoder-LM\Data\StorySeeker\processed\goal.json",
                        help="raw_text Input file path")
    parser.add_argument("-o", "--output-dir", type=str,
                        default=r"F:\Work\Debate\PrivousPerspectiveCoder-LM\Data\StorySeeker\gpt-4o_output",
                        help="Codebook and discuss output file dir")
    parser.add_argument("-c", "--config-dir", type=str,
                        default=r"F:\Work\Debate\PrivousPerspectiveCoder-LM\config\config.json",
                        help="config file dir")
    parser.add_argument("-m", "--model-name", type=str, default="gpt-4o", help="Model name")
    # parser.add_argument("-t", "--temperature", type=float, default=0, hewlp="Sampling temperature")

    parser.add_argument("-rq", "--research-question", type=str, default="", help="Data iteration starting step")
    parser.add_argument("-exp", "--experiment-name", type=float, default=2,
                        help="0: discuss, 1: baseline1, 2: baseline2")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    target_texts = import_json(args.input_file)
    config = import_json(args.config_dir)
    if not os.path.exists(args.output_dir):
        os.mkdir(args.output_dir)
        os.mkdir(os.path.join(args.output_dir, "baseline1"))
        os.mkdir(os.path.join(args.output_dir, "baseline1", "json"))
        os.mkdir(os.path.join(args.output_dir, "discuss_process"))
        os.mkdir(os.path.join(args.output_dir, "discuss_process", "json"))

    # 暂且先将这个作为默认rq（TBD）
    rq = ''' [RQ1] What are crowd workers’ descrip-
            tive perceptions of storytelling in social media
            texts?
            
            [RQ2] How do narrative perceptions dif-
            fer among crowd workers?
            
            [RQ3] How do narra-
            tive perceptions differ across prescriptive labels
            from researchers, descriptive annotations from
            crowd workers, and predictions from LLM-
            based classifiers? 
            '''

    if args.experiment_name == 0:
        roles = ["Role1", "Role2", "Role3", "Reviewer", "Judge"]
        roles_identity = roles_identity_generate(len(roles) - 2)
        experiment_discuss_flow(roles, roles_identity, target_texts, args.model_name, config, "discuss", rq)
    elif args.experiment_name == 1:
        roles = ["Role1"]
        experiment_single_flow(roles, target_texts, args.model_name, config, rq)
    elif args.experiment_name == 2:
        roles = ["Role1", "Role2", "Role3", "Reviewer", "Judge"]
        roles_identity = roles_identity_generate(1)
        roles_identity = [roles_identity[0] for _ in range(3)]
        experiment_discuss_flow(roles, roles_identity, target_texts, args.model_name, config, "baseline2", rq)
