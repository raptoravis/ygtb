# AGENTS.md

This file provides guidance for agentic coding tools working in this repository.

## Build and Development Commands

This project uses `uv` as the package manager. Ensure you have the virtual environment activated.

```bash
# Install dependencies
uv sync

# Run a Python file
python script_name.py

# Run with arguments
python article_style_analyzer.py --provider antigravity

# Run the style analyzer tool (Bokeh server)
python article_style_analyzer.py --provider antigravity --model gemini-3-flash

# Run stock analysis
python stock_analysis.py -t AAPL --provider antigravity

# Run financial analysis
python financial_analysis.py

# Run job application crew
python job_application.py

# Lint code
uv run ruff check .

# Fix linting issues automatically
uv run ruff check --fix .

# Run specific file through linter
uv run ruff check article_style_analyzer.py
```

## Testing

This codebase currently does not have formal tests. When adding new features, consider:

1. Creating a `tests/` directory
2. Using pytest for unit tests
3. Adding test files named `test_*.py`
4. Place tests adjacent to source files or in dedicated test directory

To run a single test (when tests are added):
```bash
uv run pytest tests/test_module.py::test_function_name -v
```

## Code Style Guidelines

### Imports and Organization

- Import standard library modules first, then third-party libraries
- Group imports by category with blank lines between groups
- Use absolute imports from project modules (e.g., `from utils import get_llm`)
- Import order: stdlib → third-party → local imports
- Avoid wildcard imports (`from module import *`)

```python
import argparse
import os
from datetime import datetime

from bokeh.layouts import column
from crewai import Agent, Crew, Task

from utils import get_llm, glog_info
```

### Type Annotations

- Use type hints for function parameters and return values
- Use `str`, `int`, `dict`, `list` without quotes
- Annotate constants with their types

```python
def get_llm_params(provider: str, model: str) -> dict:
    HOME_PATH: str = os.path.join(os.path.expanduser("~"), ".ygtb")
```

### Naming Conventions

- **Functions and variables**: `snake_case` (e.g., `load_history`, `stock_cache`)
- **Classes**: `PascalCase` (e.g., `StyleTab`, `Agent`)
- **Constants**: `ALL_CAPS` (e.g., `HOME_PATH`, `OPENAI_API_KEY`)
- **Private methods**: `_leading_underscore` (e.g., `_stock_cache`)

### Line Length and Formatting

- Target line length: ~120 characters (configured in flake8 settings)
- Use 4 spaces for indentation (no tabs)
- Break long strings at logical points, not mid-word

### String Formatting

- Use f-strings for string interpolation
- Prefer f-strings over `.format()` or `%` formatting

```python
glog_info(colored(f"正在分析股票: {args.ticket}", "cyan"))
```

### Docstrings

- Use triple quotes for docstrings
- Keep docstrings concise and descriptive
- Include parameter and return types for complex functions

```python
def load_history():
    """加载历史记录"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("history", [])
        except Exception:
            return []
    return []
```

### Error Handling

- Use `try-except` blocks for operations that may fail
- Catch specific exceptions when possible
- Use bare `except Exception` sparingly with meaningful error handling

```python
try:
    from datetime import datetime, timedelta
    ticker_data = polygon_client.get_ticker_details(ticket)
except Exception as e:
    if ticket in _stock_cache:
        return f"API受限，使用缓存数据: {_stock_cache[ticket]}"
    return f"获取数据失败: {str(e)}"
```

### Environment Variables

- Use `python-dotenv` to load environment variables
- Store credentials in `~/.bbt/credentials.env` or `~/.ygtb/`
- Access via `os.environ.get()` with defaults where appropriate

```python
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
```

### CLI Arguments

- Use `argparse` for command-line interfaces
- Provide default values and helpful descriptions
- Use `--provider` and `--model` arguments for LLM configuration

```python
parser = argparse.ArgumentParser(description="文章风格分析与重写工具")
parser.add_argument("--provider", type=str, default="antigravity", help="LLM 提供商")
parser.add_argument("--model", type=str, default="gemini-3-flash", help="LLM 模型名称")
args = parser.parse_args()
```

### CrewAI Patterns

- Define agents with clear `role`, `goal`, and `backstory`
- Use `verbose=True` for debugging in development
- Set `allow_delegation=True` for hierarchical processes
- Use `@tool` decorator for custom tools

```python
agent = Agent(
    role="文章风格分析师",
    goal="分析参考文章的风格并生成详细的风格描述",
    backstory="你是一个专业的写作风格分析专家...",
    llm=llm,
    verbose=True,
    allow_delegation=False,
)
```

### File I/O

- Always specify `encoding="utf-8"` when reading/writing text files
- Use `os.makedirs(..., exist_ok=True)` for directory creation
- Use `with` statement for file operations

```python
with open(ARTICLES_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
```

### Language and Comments

- Code should be in English (variable names, function names, classes)
- Comments and docstrings can be in English or Chinese (mixed in this codebase)
- Be consistent with language choice within a single file/module

## Framework-Specific Notes

- **crewAI**: This project heavily uses crewAI for multi-agent workflows
- **Bokeh**: Used for the web-based article style analyzer interface
- **LLM Integration**: Supports multiple providers (ollama, antigravity, dashscope, openai)
- **Data Storage**: Uses JSON files for styles and history in `data/` directory


<!-- open-mem-context -->
## Project Activity (auto-generated by open-mem)

### ./
| ID | Type | Title | Date |
|----|------|-------|------|
| ebc55fdf-04b2-43d4-8649-649e512c804d | 🔴 bugfix | Python LSP: TextIO reconfigure error persists | 2026-03-30 |
| 3bc087f3-7e87-4bdc-b8a4-a3e99f5e01d6 | 🔴 bugfix | Feishu-export: wiki found 18 but all skipped due to get_node errors | 2026-03-30 |
| b63bee6a-e5e1-4395-818d-8373f974b8cd | 🔴 bugfix | Python LSP: TextIO reconfigure error persists | 2026-03-30 |
| 5de5f825-d0ab-4fb7-b091-afd719ef2a89 | 🔴 bugfix | Feishu-export: node_raw assignment inside wrong if-block | 2026-03-30 |
| 8bcfdc5e-16de-4871-8d2a-377fd5ddaf29 | 🔴 bugfix | Feishu-export: UnboundLocalError - node_raw not assigned | 2026-03-30 |
| 6d5b272b-a37b-4d11-9682-997bf2644690 | 🔴 bugfix | Python LSP: TextIO error + new unbound variable warning | 2026-03-30 |
| e435e454-9912-4d5e-8f6d-c43ae5073e40 | 🔴 bugfix | Python LSP: TextIO reconfigure error persists | 2026-03-30 |
| a82908fd-dc2f-4649-993a-c8ad82d7b250 | 🔵 discovery | Feishu-export: wiki node resolution and fallback logic | 2026-03-30 |
| 0731ee35-e754-40d3-9c86-31c4223a353f | 🔴 bugfix | Python LSP: TextIO reconfigure error persists | 2026-03-30 |
| 6d277ef5-cf20-4b46-8e30-233ca92af19d | 🔴 bugfix | Python LSP: TextIO reconfigure error persists | 2026-03-30 |

**Key concepts:** type-stub-mismatch, lsp-false-positive, runtime-vs-compiletime, export-failure, encoding-error, wiki-token-resolution, empty-results, code-structure-bug, unbound-variable, conditional-assignment

💡 *Use `mem-find` to search full details. Use `mem-create` to save important decisions.*
<!-- /open-mem-context -->
