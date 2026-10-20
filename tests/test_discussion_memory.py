"""Offline regression checks using real agent methods without loading model SDKs."""

import ast
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
NAMESPACE = {"json": json, "re": re}


def load_definitions(relative_path, names):
    tree = ast.parse((ROOT / relative_path).read_text(), filename=relative_path)
    definitions = [
        node for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name in names
    ]
    if len(definitions) != len(names):
        raise AssertionError(f"Missing definitions in {relative_path}")
    exec(
        compile(ast.Module(body=definitions, type_ignores=[]), relative_path, "exec"),
        NAMESPACE,
    )


load_definitions("utils/Agent.py", {"Agent"})
load_definitions("utils/Agent_discuss.py", {"DiscussFlowModel", "ask_json_with_retry"})
Agent = NAMESPACE["Agent"]
DiscussFlowModel = NAMESPACE["DiscussFlowModel"]


class ScriptedAgent(Agent):
    def __init__(self, name, fail_once=False):
        self.name = name
        self.memory_lst = []
        self.input_token = 1
        self.output_token = 1
        self.requests = []
        self.fail_once = fail_once

    def ask(self):
        prompt = self.memory_lst[-1]["content"]
        round_number = int(re.search(r"ROUND (\d+)", prompt).group(1))
        self.requests.append((round_number, deepcopy(self.memory_lst)))
        if self.fail_once and round_number == 2:
            self.fail_once = False
            return "INVALID_JSON_RESPONSE"
        return json.dumps({
            "speaker": self.name,
            "round": round_number,
            "marker": f"{self.name}-ROUND-{round_number}",
        })


class DiscussionMemoryTests(unittest.TestCase):
    def run_discussion(self, order=("Role1", "Role2", "Role3"), fail_role=None):
        config = json.loads((ROOT / "config/config.json").read_text())
        flow = DiscussFlowModel(config, {})
        roles = [ScriptedAgent(name, fail_once=name == fail_role) for name in order]
        identities = [{"Professional_Role": f"{name} job"} for name in order]
        positionalities = [f"I am {name}." for name in order]
        with redirect_stdout(io.StringIO()):
            final, rounds = flow.codebook_discussion(
                roles, identities, positionalities,
                {"agreements": [], "disagreements": [{"code": "Teamwork"}]},
            )
        return flow, {role.name: role for role in roles}, final, rounds

    def peer_context(self, prompt):
        match = re.search(
            r"<Other_Roles_Previous_Round>\n(.*?)\n</Other_Roles_Previous_Round>",
            prompt,
            re.DOTALL,
        )
        return json.loads(match.group(1)) if match else {}

    def test_every_role_receives_completed_peer_rounds(self):
        flow, roles, final, rounds = self.run_discussion()
        for name, role in roles.items():
            for round_number, messages in role.requests:
                with self.subTest(role=name, round=round_number):
                    history = "\n".join(message["content"] for message in messages)
                    for previous_round in range(1, round_number):
                        for speaker in roles:
                            self.assertIn(f"{speaker}-ROUND-{previous_round}", history)
                    for speaker in roles:
                        self.assertNotIn(f"{speaker}-ROUND-{round_number}", history)
                    peers = self.peer_context(messages[-1]["content"])
                    self.assertEqual(
                        set(peers), set(roles) - {name} if round_number > 1 else set()
                    )
                    for speaker, response in peers.items():
                        self.assertEqual(response["speaker"], speaker)
                        self.assertEqual(response["round"], round_number - 1)
            self.assertEqual(
                [message["role"] for message in role.memory_lst],
                ["system"] + ["user", "assistant"] * 3,
            )
        self.assertEqual(list(rounds), ["round1", "round2", "round3"])
        self.assertEqual(final, rounds["round3"])
        # Preserve the string-valued format consumed by existing result exporters.
        for payload in rounds.values():
            self.assertIsInstance(payload, str)
            self.assertEqual(len(ast.literal_eval(payload)), 3)
        self.assertEqual(flow.input_token, 9)

    def test_peer_context_does_not_depend_on_speaking_order(self):
        _, first, _, _ = self.run_discussion()
        _, reversed_roles, _, _ = self.run_discussion(("Role3", "Role2", "Role1"))
        for name in first:
            for (_, request), (_, reversed_request) in zip(
                first[name].requests, reversed_roles[name].requests
            ):
                self.assertEqual(
                    self.peer_context(request[-1]["content"]),
                    self.peer_context(reversed_request[-1]["content"]),
                )

    def test_retry_keeps_one_reply_and_restores_the_user_prompt(self):
        flow, roles, _, _ = self.run_discussion(fail_role="Role2")
        role = roles["Role2"]
        self.assertEqual([number for number, _ in role.requests], [1, 2, 2, 3])
        self.assertIn("Validation error:", role.requests[2][1][-1]["content"])
        self.assertEqual(
            self.peer_context(role.requests[1][1][-1]["content"]),
            self.peer_context(role.requests[2][1][-1]["content"]),
        )
        self.assertEqual(
            [message["role"] for message in role.memory_lst],
            ["system"] + ["user", "assistant"] * 3,
        )
        saved_history = json.dumps(role.memory_lst)
        self.assertNotIn("Validation error:", saved_history)
        self.assertNotIn("INVALID_JSON_RESPONSE", saved_history)
        self.assertEqual(flow.input_token, 10)
        self.assertEqual(flow.output_token, 10)

    def test_memory_retains_user_and_assistant_messages(self):
        agent = ScriptedAgent("Role1")
        agent.set_meta_prompt("system")
        agent.event("question")
        agent.memory("answer")
        self.assertEqual(
            agent.memory_lst,
            [
                {"role": "system", "content": "system"},
                {"role": "user", "content": "question"},
                {"role": "assistant", "content": "answer"},
            ],
        )
        before = deepcopy(agent.memory_lst)
        agent.event("temporary question")
        agent.memory("temporary answer", if_memory=False)
        self.assertEqual(agent.memory_lst, before)
        agent.memory_lst.clear()
        agent.memory("answer")
        self.assertEqual(agent.memory_lst, [{"role": "assistant", "content": "answer"}])


if __name__ == "__main__":
    unittest.main()
