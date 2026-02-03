"""
Style Generator - Analyze reference articles and generate writing style descriptions.

This module provides functionality to analyze one or more reference articles
and generate a comprehensive style description using LLM.
"""

import argparse
import os
import sys
from typing import List, Optional

from langchain.prompts import ChatPromptTemplate

# Add project root to path for importing utils
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils import get_langchain_llm


def generate_style_description(
    reference_articles: List[str],
    style_name: str,
    provider: str = "antigravity",
    model: Optional[str] = None,
) -> str:
    """
    Analyze reference articles and generate a detailed style description.

    Args:
        reference_articles: List of reference article texts to analyze
        style_name: Name for the style being analyzed
        provider: LLM provider (antigravity, ollama, dashscope, openai, customai)
        model: Specific model name to use (optional)

    Returns:
        A detailed style description string

    Raises:
        ValueError: If provider is not supported or API credentials are missing
    """
    llm = get_langchain_llm(provider=provider, model=model)

    reference_text = "\n\n".join(
        [f"参考文章{i + 1}:\n{ref}" for i, ref in enumerate(reference_articles)]
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是一个专业的写作风格分析专家，能够准确捕捉文章的写作风格、语气、用词习惯和结构特点，"
                "并用简洁准确的语言描述这些风格特点。",
            ),
            (
                "human",
                """分析以下参考文章的风格特点，生成一个详细的风格描述。

风格名称: {style_name}

参考文章:
{reference_text}

请分析参考文章的以下方面，并生成一个清晰、详细的风格描述：
1. 写作风格（正式/随意/学术/文学等）
2. 语言特点（用词习惯、句式结构、修辞手法等）
3. 情感基调（严肃/轻松/热情/客观等）
4. 文章结构（开头/正文/结尾的组织方式）
5. 特殊的表达习惯或写作手法

请将以上分析整合成一个连贯、详细的风格描述，这个描述将用于指导AI以相同的风格重写其他文章。
描述应该具体、准确，足以让AI理解和模仿这种写作风格。""",
            ),
        ]
    )

    chain = prompt | llm
    result = chain.invoke({"style_name": style_name, "reference_text": reference_text})

    # Extract content from result (handle both string and AIMessage types)
    if hasattr(result, "content"):
        return str(result.content)
    return str(result)


def main():
    parser = argparse.ArgumentParser(description="从参考文章生成风格描述")
    parser.add_argument(
        "--articles",
        type=str,
        required=True,
        help="参考文章文件路径，多个文件用逗号分隔",
    )
    parser.add_argument(
        "--style-name",
        type=str,
        default="自定义风格",
        help="风格名称",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="antigravity",
        help="LLM 提供商 (antigravity/ollama/dashscope/openai/customai)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="LLM 模型名称",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出文件路径（可选，默认输出到控制台）",
    )

    args = parser.parse_args()

    # Read reference articles
    article_paths = [p.strip() for p in args.articles.split(",")]
    reference_articles = []

    for path in article_paths:
        if not os.path.exists(path):
            print(f"错误：文件不存在: {path}")
            sys.exit(1)

        with open(path, "r", encoding="utf-8") as f:
            reference_articles.append(f.read())

    print(f"正在分析 {len(reference_articles)} 篇参考文章...")
    print(f"风格名称: {args.style_name}")
    print(f"使用提供商: {args.provider}")
    if args.model:
        print(f"使用模型: {args.model}")

    try:
        style_description = generate_style_description(
            reference_articles=reference_articles,
            style_name=args.style_name,
            provider=args.provider,
            model=args.model,
        )

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(style_description)
            print(f"\n风格描述已保存到: {args.output}")
        else:
            print("\n生成的风格描述:")
            print("=" * 60)
            print(style_description)
            print("=" * 60)

    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
