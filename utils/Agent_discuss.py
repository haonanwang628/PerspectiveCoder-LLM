import json
import re
from utils.Agent import Agent
from config.model_menu import *
import random
import os
random.seed(3)


class DiscussFlowModel:
    def __init__(self, discuss_config, models_name):
        self.config = discuss_config
        self.models_name = models_name
        self.target_text = ""
        self.input_token = 0
        self.output_token = 0

    def ask_json_with_retry(self, agent, max_attempts=10, if_memory=False, if_print=True, 
                            expected_type=dict, validator=None):
        """Delegate JSON generation and validation to the shared retry helper."""
        return ask_json_with_retry(self, agent, max_attempts=max_attempts,if_memory=if_memory,
                                    if_print=if_print, expected_type=expected_type, validator=validator,)

    def agents_init(self):
        roles = []
        for role, model_name in self.models_name.items():
            model_local_dir = os.path.isdir(self.models_name[role])
            roles.append(Agent(
                model_name=model_name,
                name=role,
                api_key=None if model_local_dir else api_key[model_name],
                base_url=None if model_local_dir else base_url[model_name]
            ))

        return roles

    def role_stage(self, role, rq=None):
        # role init codebook generate
        if rq is not None:
            role.set_meta_prompt(
                self.config["Agents"]["Coder"]["system_non_pos_rq"].replace("{datasets}", self.target_text)
                .replace("{RQ}", rq))
            role.event(self.config["Agents"]["Coder"]["user_non_pos_rq"])
        else:
            role.set_meta_prompt(
                self.config["Agents"]["Coder"]["system_non_pos"].replace("{datasets}", self.target_text))
            role.event(self.config["Agents"]["Coder"]["user_non_pos"])
        # role_response = role.ask()
        # role.memory(role_response, False, True)
        # self.input_token += role.input_token
        # self.output_token += role.output_token

        # try:
        #     codebook = json.loads(role_response)
        # except Exception:
        #     codebook = json.loads(eval(role_response.replace('```', "'''").replace('json', '').strip()))
        # return self.ask_json_with_retry(role)
        return self.ask_json_with_retry(role)

    def roles_stage(self, roles, roles_identity, rq=None):
        # roles init codebook generate
        init_codebook, roles_positionality, role_prompt = [], [], []
        for i, role in enumerate(roles):
            if rq is not None:
                pos_system = self.config["Agents"]["Positionality"]["system_rq"] \
                    .replace("[Research Question]", rq)
                pos_user = self.config["Agents"]["Positionality"]["user_rq"]
            else:
                pos_system = self.config["Agents"]["Positionality"]["system"]
                pos_user = self.config["Agents"]["Positionality"]["user"]
            pos_system = pos_system \
                .replace("[insert]", roles_identity[i]["Gender"], 1) \
                .replace("[insert]", roles_identity[i]["Education"], 1) \
                .replace("[insert]", roles_identity[i]["Race_Ethnicity"], 1) \
                .replace("[insert]", roles_identity[i]["Age"], 1) \
                .replace("[insert]", roles_identity[i]["Degree_Subject"], 1) \
                .replace("[insert]", roles_identity[i]["Reddit_Use"], 1)
            # roles system
            role.set_meta_prompt(pos_system)

            # roles positionality statement
            role.event(pos_user)
            role_response = role.ask()
            roles_positionality.append(role_response)
            role.memory(role_response, True, True)
            self.input_token += role.input_token
            self.output_token += role.output_token

            # roles init codebook generate
            if rq is not None:
                role.set_meta_prompt(
                    self.config["Agents"]["Coder"]["system_rq"].replace("{datasets}", self.target_text)
                    .replace("{positionality statement}", roles_positionality[i]).replace("{RQ}", rq))
                role.event(self.config["Agents"]["Coder"]["user_rq"])
            else:
                role.set_meta_prompt(
                    self.config["Agents"]["Coder"]["system"].replace("{datasets}", self.target_text)
                    .replace("{positionality statement}", roles_positionality[i]))
                role.event(self.config["Agents"]["Coder"]["user"])
            # role_response = role.ask()
            # role.memory(role_response, False, True)
            # self.input_token += role.input_token
            # self.output_token += role.output_token
            # try:
                # parsed = json.loads(role_response)
            # except Exception:
                # parsed = json.loads(eval(role_response.replace('```', "'''").replace('json', '').strip()))
            parsed = self.ask_json_with_retry(role)
            init_codebook.append(parsed)

        return roles_positionality, init_codebook

    def codebook_reviewer(self, reviewer, init_codebook):

        reviewer_system = self.config["Agents"]["Reviewer"]["system"].replace("{codebook}", str(init_codebook))
        reviewer_user = self.config["Agents"]["Reviewer"]["user"]

        reviewer.set_meta_prompt(reviewer_system)
        reviewer.event(reviewer_user)
        # reviewer_response = reviewer.ask()
        # reviewer.memory(reviewer_response, False, True)
        # self.input_token += reviewer.input_token
        # self.output_token += reviewer.output_token

        # try:
            # agreed_disagreed_codebook = json.loads(reviewer_response)
        # except Exception:
            # agreed_disagreed_codebook = json.loads(
                # eval(reviewer_response.replace('```', "'''").replace('json', '').strip()))

        # return agreed_disagreed_codebook
        return self.ask_json_with_retry(reviewer)

    def codebook_discussion(self, roles, roles_identity, roles_positionality, agreed_disagreed_codebook):
        roles_update = [{"name": role.name, "obj": role} for role in roles]

        discussion_system = self.config["Agents"]["Discussion"]["system"]
        discussion_user = self.config["Agents"]["Discussion"]["user"]

        for role, identity, positionality in zip(roles, roles_identity, roles_positionality):
            role.memory_lst.clear()
            role.set_meta_prompt(
                discussion_system.replace("{Role}", f"{identity['Race_Ethnicity']}|{identity['Education']}|{identity['Gender']}|{identity['Age']}|{identity['Reddit_Use']}") \
                .replace("{Positionality Statement}", positionality)
                .replace("{Agreement / Disagreement Codes}", str(agreed_disagreed_codebook)))

        # Discussion
        discuss_responses = {}
        for i, discuss in enumerate(discussion_user.items()):
            roles_responses = []
            for role_info in roles_update:
                role = role_info["obj"]
                if i == 0:
                    role.event(f"{discuss}")
                else:
                    for m in roles_responses:
                        if role_info['name'] != m.keys():
                            role.memory(f"Other role:{m}")
                    role.event(f"{discuss}")
                # response = role.ask()
                # role.memory(response, True, True)
                # try:
                    # response = json.loads(response)
                # except Exception:
                    # response = json.loads(
                        # eval(response.replace('```', "'''").replace('json', '').strip()))
                # roles_responses.append({role_info['name']: response})
                # self.input_token += role.input_token
                # self.output_token += role.output_token
                response = self.ask_json_with_retry(role, if_memory=True)
                roles_responses.append({role_info["name"]: response})
            # include roles_responses of every round
            discuss_responses[f"round{i + 1}"] = f"{roles_responses}"

        final_agreed_codebook = discuss_responses["round3"]

        return final_agreed_codebook, discuss_responses

    def codebook_judge(self, Judge, init_codebook, agreed_disagreed_codebook, final_agreed_codebook, rq=None):

        if rq is not None:
            Judge_system = self.config["Agents"]["Judge"]["system_rq"] \
                .replace("{init_codebook}", str(init_codebook)) \
                .replace("{reviewer_output}", str(agreed_disagreed_codebook)) \
                .replace("{discussion_output}", str(final_agreed_codebook))
            Judge_user = self.config["Agents"]["Judge"]["user_rq"]
        else:
            Judge_system = self.config["Agents"]["Judge"]["system"] \
                .replace("{init_codebook}", str(init_codebook)) \
                .replace("{reviewer_output}", str(agreed_disagreed_codebook)) \
                .replace("{discussion_output}", str(final_agreed_codebook))
            Judge_user = self.config["Agents"]["Judge"]["user"]

        Judge.set_meta_prompt(Judge_system)
        Judge.event(Judge_user)
        # codebook = Judge.ask()
        # Judge.memory(codebook, False, True)
        # self.input_token += Judge.input_token
        # self.output_token += Judge.output_token

        # try:
            # parsed = json.loads(codebook)
        # except Exception:
            # parsed = json.loads(eval(codebook.replace('```', "'''").replace('json', '').strip()))

        # return parsed
        return self.ask_json_with_retry(Judge)


class SingleModel:
    def __init__(self, config, models_name):
        """Create a Discuss Model
        Args:
            discuss_config: discuss prompt and discuss progress design
            models_name: multi Agents(roles and Facilitator) models name,
        """
        self.config = config
        self.models_name = models_name

        self.target_text = ""
        self.input_token = 0
        self.output_token = 0

    def agent_init(self):
        """
            return: roles and Facilitator Agent.
        """
        model_local_dir = os.path.isdir(self.models_name)
        agent = Agent(
            model_name=self.models_name,
            name="SingleLLM",
            api_key=None if model_local_dir else api_key[self.models_name],
            base_url=None if model_local_dir else base_url[self.models_name]
        )
        return agent

    def baseline1_codebook_generate(self, agent):
        agent.set_meta_prompt(self.config["system"])
        agent.event(
            self.config["user"].replace("{dataset}", self.target_text))
        # reply = agent.ask()
        # agent.memory(reply, False)
        # reply = json.loads(reply.replace('```', "").replace('json', '').strip())

        # return reply
        return ask_json_with_retry(self, agent, if_print=False)

def ask_json_with_retry(self, agent, max_attempts=10, if_memory=False, if_print=True, expected_type=dict, validator=None):
    """
    Request a JSON response and retry if parsing or validation fails.

    Args:
        agent: Agent with a pending user message.
        max_attempts: Maximum number of generation attempts.
        if_memory: Whether to retain the successful response.
        if_print: Whether to print the successful response.
        expected_type: Expected top-level type, or None to skip this check.
        validator: Optional validation function. It must raise ValueError
            when validation fails.

    Returns:
        The parsed and validated JSON value.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    if not agent.memory_lst or agent.memory_lst[-1]["role"] != "user":
        raise ValueError("Add a user message with agent.event() before calling this method")
    
    user_message = agent.memory_lst[-1]
    original_question = user_message["content"]
    validation_errors = []
    try:
        for attempt in range(1, max_attempts + 1):
            response = agent.ask()
            # Count tokens consumed by every attempt, including failed ones.
            self.input_token += agent.input_token
            self.output_token += agent.output_token
            try:
                text = response.strip()
                # Extract JSON from an optional Markdown code block.
                match = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
                if match:
                    text = match.group(1).strip()
                parsed = json.loads(text)
                if (expected_type is not None and not isinstance(parsed, expected_type)):
                    raise ValueError(f"Expected top-level type {expected_type.__name__}, "
                        f"got {type(parsed).__name__}")
                # Apply optional stage-specific validation.
                if validator is not None:
                    validator(parsed)

            except ValueError as exc:
                if attempt == max_attempts:
                    raise RuntimeError(f"{agent.name} failed to produce a valid JSON "
                        f"response after {max_attempts} attempts") from exc
                error = f"Validation error: {exc}"
                if error not in validation_errors:
                    validation_errors.append(error)
                user_message["content"] = (
                    original_question
                    + "\n\nReturn valid JSON only; fix these errors:\n"
                    + "\n".join(validation_errors))
                
                continue

            # Store and print only the validated JSON, not the raw response.
            validated_response = json.dumps(parsed, ensure_ascii=False, indent=2)
            agent.memory(validated_response, if_memory, if_print)
            return parsed

    finally:
        # Restore the original message if it remains in conversation history.
        user_message["content"] = original_question