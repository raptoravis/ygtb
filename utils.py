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


# Style storage functions
ARTICLES_FILE = "data/articles.json"


def load_styles():
    """Load styles from data/articles.json"""
    if os.path.exists(ARTICLES_FILE):
        with open(ARTICLES_FILE, "r", encoding="utf-8") as f:
            data = f.read()
            if data.strip():
                import json

                loaded_data = json.loads(data)
                return loaded_data.get("styles", [])
    return []


def save_styles(styles):
    """Save styles to data/articles.json"""
    os.makedirs(os.path.dirname(ARTICLES_FILE), exist_ok=True)
    import json

    with open(ARTICLES_FILE, "w", encoding="utf-8") as f:
        json.dump({"styles": styles}, f, ensure_ascii=False, indent=2)


def get_style_by_name(style_name: str):
    """Get a style by name from data/articles.json

    Args:
        style_name: Name of the style to retrieve

    Returns:
        Style dictionary if found, None otherwise
    """
    styles = load_styles()
    for style in styles:
        if style.get("name") == style_name:
            return style
    return None


def list_styles():
    """List all available styles from data/articles.json

    Returns:
        List of style names
    """
    styles = load_styles()
    return [style.get("name", "未命名风格") for style in styles]


def add_article_to_style(style_name: str, content: str):
    """Add a rewritten article to a style in data/articles.json

    Args:
        style_name: Name of the style to add the article to
        content: The rewritten article content

    Returns:
        True if successful, False otherwise (e.g., style not found)

    Raises:
        Exception: If there's an error reading/writing the file
    """
    from datetime import datetime

    styles = load_styles()
    style_found = False

    for style in styles:
        if style.get("name") == style_name:
            style_found = True
            # Ensure articles list exists
            if "articles" not in style:
                style["articles"] = []

            # Create new article entry
            article_entry = {
                "content": content,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            # Add to articles list
            style["articles"].append(article_entry)
            break

    if not style_found:
        print(f"警告：未找到名为 '{style_name}' 的风格")
        return False

    # Save back to file
    save_styles(styles)
    return True


# Rewrite history functions
REWRITE_HISTORY_FILE = "data/rewrite_history.json"


def load_rewrite_history():
    """Load rewrite history from data/rewrite_history.json"""
    if os.path.exists(REWRITE_HISTORY_FILE):
        with open(REWRITE_HISTORY_FILE, "r", encoding="utf-8") as f:
            data = f.read()
            if data.strip():
                import json

                loaded_data = json.loads(data)
                return loaded_data.get("history", [])
    return []


def save_rewrite_history(history):
    """Save rewrite history to data/rewrite_history.json"""
    os.makedirs(os.path.dirname(REWRITE_HISTORY_FILE), exist_ok=True)
    import json

    with open(REWRITE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "history": history,
                "metadata": {
                    "version": "1.0",
                    "description": "文章重写历史记录，独立于风格参考文章",
                },
            },
            f,
            ensure_ascii=False,
            indent=2,
        )


def add_rewrite_history(
    style_name: str,
    original_content: str,
    rewritten_content: str,
    original_file: str = "",
    prompt_file: str = "",
    notes: str = "",
) -> int:
    """Add a rewrite entry to history

    Args:
        style_name: Name of the style used for rewriting
        original_content: The original article content
        rewritten_content: The rewritten article content
        original_file: Path to the original file (optional)
        prompt_file: Path to the prompt file (optional)
        notes: Additional notes about this rewrite (optional)

    Returns:
        The ID of the newly added history entry
    """
    from datetime import datetime

    history = load_rewrite_history()

    # Generate new ID
    new_id = 1
    if history:
        new_id = max(entry.get("id", 0) or 0 for entry in history) + 1

    # Create new history entry
    history_entry = {
        "id": new_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "style_name": style_name,
        "original_file": original_file,
        "original_content": original_content,
        "rewritten_content": rewritten_content,
        "prompt_file": prompt_file,
        "notes": notes,
    }

    # Add to history list
    history.append(history_entry)

    # Save back to file
    save_rewrite_history(history)

    return new_id


def get_rewrite_history_by_style(style_name: str):
    """Get all rewrite history entries for a specific style

    Args:
        style_name: Name of the style to filter by

    Returns:
        List of history entries for that style
    """
    history = load_rewrite_history()
    return [entry for entry in history if entry.get("style_name") == style_name]


def get_rewrite_history_entry(entry_id: int):
    """Get a specific rewrite history entry by ID

    Args:
        entry_id: ID of the history entry to retrieve

    Returns:
        History entry dict if found, None otherwise
    """
    history = load_rewrite_history()
    for entry in history:
        if entry.get("id") == entry_id:
            return entry
    return None


def list_rewrite_history(limit: int = None):
    """List all rewrite history entries

    Args:
        limit: Maximum number of entries to return (most recent first)

    Returns:
        List of history entries (sorted by timestamp, newest first)
    """
    history = load_rewrite_history()
    # Sort by id descending (newest first)
    sorted_history = sorted(history, key=lambda x: x.get("id") or 0, reverse=True)

    if limit:
        return sorted_history[:limit]
    return sorted_history


def delete_rewrite_history_entry(entry_id: int) -> bool:
    """Delete a rewrite history entry by ID

    Args:
        entry_id: ID of the history entry to delete

    Returns:
        True if deleted, False if not found
    """
    history = load_rewrite_history()
    original_len = len(history)
    history = [entry for entry in history if entry.get("id") != entry_id]

    if len(history) < original_len:
        save_rewrite_history(history)
        return True
    return False
