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


def get_llm(provider="antigravity", model=None):
    from crewai import LLM

    temperature = 0.3
    if provider.lower() == "ollama":
        model = model or "codellama"
        glog_info(f"{provider} {model}")

        return LLM(
            model=f"{model}",
            base_url="http://localhost:11434",
            temperature=temperature,
        )
    elif provider.lower() == "antigravity":
        if ANTIGRAVITY_API_KEY and ANTIGRAVITY_BASE_URL:
            model = model or "gemini-3-flash"
            glog_info(f"{provider} {model}")
            return LLM(
                model=model,
                api_key=ANTIGRAVITY_API_KEY,
                base_url=ANTIGRAVITY_BASE_URL,
                temperature=temperature,
            )
        else:
            raise ValueError(
                "Antigravity API credentials not found. "
                "Please set ANTIGRAVITY_API_KEY, ANTIGRAVITY_BASE_URL and ANTIGRAVITY_MODEL env var."
            )
    elif provider == "dashscope":
        if DASHSCOPE_API_KEY and DASHSCOPE_BASE_URL:
            model = model or "qwen3-coder-plus"
            glog_info(f"{provider} {model}")

            return LLM(
                model=model,
                api_key=DASHSCOPE_API_KEY,
                base_url=DASHSCOPE_BASE_URL,
                temperature=temperature,
            )
        else:
            raise ValueError("Dashscope API credentials not found. Please set DASHSCOPE_API_KEY env var.")
    elif provider == "openai":
        if OPENAI_API_KEY and OPENAI_BASE_URL:
            model = model or "gpt-4"
            return LLM(
                model=model,
                api_key=OPENAI_API_KEY,  # type: ignore
                base_url=OPENAI_BASE_URL,
                temperature=temperature,
            )
        else:
            raise ValueError("OpenAI API credentials not found. Please set OPENAI_API_KEY env var.")


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
