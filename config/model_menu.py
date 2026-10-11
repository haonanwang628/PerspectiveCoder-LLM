# model menu
gpt_api = ""

MODEL_TOKENIZER_MAP = {
    "deepseek-chat": "cl100k_base",
    "deepseek-reasoner": "cl100k_base",
}

llm_MaxToken = {
    "deepseek-chat": 8000,
    "deepseek-reasoner": 10000,
    "gpt-4o-mini": 128000,
    "gpt-4o": 128000,
    "gpt-5": 128000
}

available_models = ["deepseek-chat", "gpt-4o-mini", "gpt-4o", "gpt-5"]

api_key = {
    "gpt-4o-mini": gpt_api,
    "gpt-4o": gpt_api,
    "gpt-5": gpt_api,
    "deepseek-chat": "",
    "deepseek-reasoner": ""
}
# import os
# api_key = {
#     "gpt-4o": os.getenv("DEEPSEEK_API_KEY"),
#     "gpt-4o-mini": os.getenv("DEEPSEEK_API_KEY"),
#     "deepseek-chat": os.getenv("DEEPSEEK_API_KEY"),
#     "deepseek-reasoner": os.getenv("DEEPSEEK_API_KEY"),
#     "gpt-5": os.getenv("DEEPSEEK_API_KEY")
# }

base_url = {
    "gpt-4o-mini": "",
    "gpt-4o": "",
    "gpt-5": "",
    "deepseek-chat": "https://api.deepseek.com/v1",
    "deepseek-reasoner": "https://api.deepseek.com/v1",
}
