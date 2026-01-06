import argparse
import json

from scrapegraphai.graphs import SearchGraph, SmartScraperGraph

from utils import get_llm_params


def main():
    parser = argparse.ArgumentParser(description="文章风格分析与重写工具")
    parser.add_argument(
        "--provider",
        type=str,
        default="antigravity",
        help="LLM 提供商 (ollama/antigravity/dashscope)",
    )
    parser.add_argument("--model", type=str, default="gemini-3-flash", help="LLM 模型名称")
    args = parser.parse_args()

    llm_params = get_llm_params(provider=args.provider, model=args.model)

    api_key = llm_params["api_key"]
    provider = llm_params["provider"]
    model = llm_params["model"]
    base_url = llm_params["base_url"]

    graph_config = {
        "llm": {
            "api_key": api_key,
            "base_url": base_url,
            "model": f"{provider}/{model}",
        },
        "embedder": {
            "model": "ollama/nomic-embed-text",
            "base_url": "http://localhost:11434",
        },
        "verbose": True,  # 开启话痨模式，看 AI 怎么思考
        "headless": False,  # 设置为 False 可以看到浏览器自动打开，超酷！
    }

    # 2. 定义目标和任务
    # 甚至是中文 Prompt，AI 完全听得懂！
    target_url = "https://news.ycombinator.com/"  # 著名的 Hacker News
    prompt = """请帮我提取页面上所有新闻的'标题'和'链接'。
请严格按照以下JSON格式输出，不要添加任何其他文字或解释：
```json
{
  "news": [
    {
      "title": "新闻标题",
      "link": "新闻链接"
    }
  ]
}
```"""

    # 3. 创建 Agent 实例
    smart_scraper = SmartScraperGraph(prompt=prompt, source=target_url, config=graph_config)

    # 4. 执行！见证奇迹
    print(" Agent 正在出发...")
    result = smart_scraper.run()

    print(json.dumps(result, indent=2, ensure_ascii=False))

    # 任务：去百度搜索 "Python 教程"，并总结前 3 个结果的摘要
    search_prompt = """搜索 'Python 2026 趋势'，并总结前 3 篇文章的核心观点。
请严格按照以下JSON格式输出：
```json
{
  "summary": "总体概述",
  "articles": [
    {
      "title": "文章标题",
      "core_points": ["核心观点1", "核心观点2"]
    }
  ]
}
```"""
    search_graph = SearchGraph(prompt=search_prompt, config=graph_config)

    result = search_graph.run()
    print(result)
    pass


if __name__ == "__main__":
    main()
