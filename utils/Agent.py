import os
import openai
import time
import torch

from utils.Function import llm_MaxToken, num_tokens_from_string, load_local_model
from transformers import AutoTokenizer, AutoModelForCausalLM



class Agent:
    def __init__(self, model_name, name="", temperature=1.0, sleep_time=0, api_key=None, base_url=None):
        """Create an agent
            Args:
                model_name (str): model name, e.g., 'gpt-4', 'deepseek-chat'
                name (str): name of this agent
                temperature (float): generation randomness
                sleep_time (float): optional sleep before each query
                api_key (str): API key for the model
                base_url (str): base URL for non-OpenAI models
         """
        self.model_name = model_name
        self.model_local_dir= os.path.isdir(model_name)
        
        self.name = name
        self.temperature = temperature
        self.sleep_time = sleep_time
        self.api_key = api_key
        self.base_url = base_url

        self.memory_lst = []
        if self.model_local_dir:
                    self.tokenizer, self.model = load_local_model(model_name)
                    self.max_token = self.model.config.max_position_embeddings
        else:
            self.max_token = llm_MaxToken[model_name]

        self.input_token = 0
        self.output_token = 0

    def query(self, messages, max_tokens, temperature):
        """Send a query to the LLM API with streaming and error handling."""
        time.sleep(self.sleep_time)

        # ========== Local model ==========
        if self.model_local_dir:
            inputs = self.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, 
                                                        return_tensors="pt",  return_dict=True).to(self.model.device)
            input_length = inputs["input_ids"].shape[-1]
            available_tokens = self.max_token - input_length - 32
            max_new_tokens = min(max_tokens, available_tokens)

            if max_new_tokens <= 0:
                raise ValueError(f"Context too long: {input_length} tokens")
            generation_kwargs = {"max_new_tokens": max_new_tokens,
                                "do_sample": temperature > 0,
                                "pad_token_id": self.tokenizer.eos_token_id}
            if temperature > 0:
                generation_kwargs["temperature"] = temperature

            with torch.inference_mode():
                outputs = self.model.generate(**inputs, **generation_kwargs)
            generated_ids = outputs[0][input_length:]
            response = self.tokenizer.decode(generated_ids, skip_special_tokens=True)

            return response

        # ========== API Models ===========
        client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url) if self.base_url else openai.OpenAI(
            api_key=self.api_key)

        # print(f"Sending request to model: {self.name} of {self.model_name} via {self.base_url}...")
        try:
            if self.model_name in ["gpt-5"]:
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_completion_tokens=max_tokens,
                    timeout=4 * 10 * 60
                )
            else:
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,   # gpt4
                    timeout=4 * 10 * 60
                )
            response = response.choices[0].message.content
        except Exception as e:
            print(f"[Error] {e}")
            raise e

        return response

    def ask(self):
        num_context_token = sum([num_tokens_from_string(m["content"], self.model_name, tokenizer=self.tokenizer if self.model_local_dir else None) for m in self.memory_lst])
        if self.model_name in ["gpt-5"]:
            t = self.max_token
        else:
            t = self.max_token - num_context_token if self.max_token - num_context_token < 10000 else 10000
        response = self.query(self.memory_lst, t, self.temperature)

        response_token = num_tokens_from_string(response, self.model_name, tokenizer=self.tokenizer if self.model_local_dir else None)

        self.input_token = num_context_token
        self.output_token = response_token
        

        self.input_token = num_context_token
        self.output_token = response_token

        return response

    def set_meta_prompt(self, meta_prompt: str):
        """Set the meta_prompt

        Args:
            meta_prompt (str): the meta prompt
        """
        self.memory_lst.append({"role": "system", "content": f"{meta_prompt}"})

    def event(self, event):
        """Add an new event in the memory
        Args:
            event (str): string that describe the event.
        """
        self.memory_lst.append({"role": "user", "content": f"{event}"})

    def memory(self, memory, if_memory=True, if_print=False):
        """Monologue in the memory

        Args:
            memory (str): string that generated by the model in the last round.
            if_memory: True or False
            if_print: True or False
        """
        if if_memory and self.memory_lst[-1]["role"] == "user":
            self.memory_lst.pop()
            self.memory_lst.append({"role": "assistant", "content": f"{memory}"})
        elif self.memory_lst[-1]["role"] == "user":
            self.memory_lst.pop()
        # if if_memory:
        #     self.memory_lst.append({"role": "assistant", "content": f"{memory}"})
        if if_print:
            print(f"----- {self.name} -----\n{memory}\n")
