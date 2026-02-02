# Add your utilities or helper functions to this file.

import os

from dotenv import find_dotenv, load_dotenv

HOME_PATH: str = os.path.join(os.path.expanduser("~"), ".bbt")
credentials_env_path = os.path.join(HOME_PATH, "credentials.env")
load_dotenv(credentials_env_path, verbose=True)

DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY")
DASHSCOPE_BASE_URL = os.environ.get("DASHSCOPE_BASE_URL")

ANTIGRAVITY_API_KEY = os.environ.get("ANTIGRAVITY_API_KEY")
ANTIGRAVITY_BASE_URL = os.environ.get("ANTIGRAVITY_BASE_URL")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

CUSTOMAI_API_KEY = os.environ.get("CUSTOMAI_API_KEY")
CUSTOMAI_BASE_URL = os.environ.get("CUSTOMAI_BASE_URL")


def glog_info(msg: str):
    print(msg)


# these expect to find a .env file at the directory above the lesson.
def load_env():
    _ = load_dotenv(find_dotenv())


def get_openai_api_key():
    load_env()
    api_key = os.getenv("OPENAI_API_KEY")
    return api_key


def get_serper_api_key():
    load_env()
    api_key = os.getenv("SERPER_API_KEY")
    return api_key


def get_llm_params(provider: str, model: str) -> dict:
    temperature = 0.3
    provider = provider.lower()

    provider_configs = {
        "ollama": {
            "provider": "ollama",
            "model": None,  # Will use the model parameter
            "base_url": "http://localhost:11434",
        },
        "antigravity": {
            "provider": "openai",
            "model": "gemini-3-flash",
            "api_key": ANTIGRAVITY_API_KEY,
            "base_url": ANTIGRAVITY_BASE_URL,
            "error_msg": "Antigravity API credentials not found. Please set ANTIGRAVITY_API_KEY/ANTIGRAVITY_BASE_URL",
        },
        "dashscope": {
            "provider": "openai",
            "model": "qwen3-coder-plus",
            "api_key": DASHSCOPE_API_KEY,
            "base_url": DASHSCOPE_BASE_URL,
            "error_msg": "Dashscope API credentials not found. Please set DASHSCOPE_API_KEY env var.",
        },
        "openai": {
            "provider": "openai",
            "model": "gpt-4",
            "api_key": OPENAI_API_KEY,
            "base_url": OPENAI_BASE_URL,
            "error_msg": "OpenAI API credentials not found. Please set OPENAI_API_KEY env var.",
        },
        "customai": {
            "provider": "openai",
            "model": "kuaishou/kat-coder-pro-v1-free",
            "api_key": CUSTOMAI_API_KEY,
            "base_url": CUSTOMAI_BASE_URL,
            "error_msg": "OpenAI API credentials not found. Please set CUSTOMAI_API_KEY/CUSTOMAI_BASE_URL env var.",
        },
    }

    if provider not in provider_configs:
        raise ValueError(f"Unknown provider: {provider}")

    config = provider_configs[provider]

    if provider != "ollama" and not (config["api_key"] and config["base_url"]):
        raise ValueError(config["error_msg"])

    model = model or config["model"]
    glog_info(f"{provider} {model}")

    llm_params = {
        "provider": config["provider"],
        "base_url": config["base_url"],
        "model": model,
        "temperature": temperature,
    }

    if provider != "ollama":
        llm_params["api_key"] = config["api_key"]
    else:
        pass

    return llm_params


def get_llm(provider: str, model: str):
    from crewai import LLM

    llm_params = get_llm_params(provider=provider, model=model)
    return LLM(**llm_params)


def get_langchain_llm(provider: str, model: str):
    """Get LangChain compatible LLM instance for article_style_analyzer"""
    provider = provider.lower()
    temperature = 0.3

    provider_configs = {
        "ollama": {
            "model": model or "llama3.2",
            "base_url": "http://localhost:11434",
        },
        "antigravity": {
            "model": model or "gemini-3-flash",
            "api_key": ANTIGRAVITY_API_KEY,
            "base_url": ANTIGRAVITY_BASE_URL,
        },
        "dashscope": {
            "model": model or "qwen3-coder-plus",
            "api_key": DASHSCOPE_API_KEY,
            "base_url": DASHSCOPE_BASE_URL,
        },
        "openai": {
            "model": model or "gpt-4",
            "api_key": OPENAI_API_KEY,
            "base_url": OPENAI_BASE_URL,
        },
        "customai": {
            "model": model or "kuaishou/kat-coder-pro-v1-free",
            "api_key": CUSTOMAI_API_KEY,
            "base_url": CUSTOMAI_BASE_URL,
        },
    }

    if provider not in provider_configs:
        raise ValueError(f"Unknown provider: {provider}")

    config = provider_configs[provider]

    if provider == "ollama":
        from langchain_ollama import OllamaLLM

        return OllamaLLM(model=config["model"], base_url=config["base_url"], temperature=temperature)
    else:
        if not (config["api_key"] and config["base_url"]):
            raise ValueError(f"API credentials not found for provider: {provider}")
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=config["model"],
            api_key=config["api_key"],
            base_url=config["base_url"],
            temperature=temperature,
        )


# break line every 80 characters if line is longer than 80 characters
# don't break in the middle of a word
def pretty_print_result(result):
    parsed_result = []
    for line in result.split("\n"):
        if len(line) > 80:
            words = line.split(" ")
            new_line = ""
            for word in words:
                if len(new_line) + len(word) + 1 > 80:
                    parsed_result.append(new_line)
                    new_line = word
                else:
                    if new_line == "":
                        new_line = word
                    else:
                        new_line += " " + word
            parsed_result.append(new_line)
        else:
            parsed_result.append(line)
    return "\n".join(parsed_result)
