"""
Article Rewriter - Rewrite articles according to a specified writing style.

This module provides functionality to rewrite content to match a specific
writing style description using LLM.
"""

import argparse
import os
import sys
from typing import Optional

from langchain.prompts import ChatPromptTemplate

# Add project root to path for importing utils
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils import get_langchain_llm


def rewrite_article(
    article_text: str,
    style_description: str,
    style_name: str = "",
    additional_instructions: str = "",
    provider: str = "antigravity",
    model: Optional[str] = None,
) -> str:
    """
    Rewrite an article according to a specified writing style.

    Args:
        article_text: The content to be rewritten
        style_description: Detailed description of the target writing style
        style_name: Name of the style (optional)
        additional_instructions: Extra guidance for the rewrite (optional)
        provider: LLM provider (antigravity, ollama, dashscope, openai, customai)
        model: Specific model name to use (optional)

    Returns:
        The rewritten article text

    Raises:
        ValueError: If provider is not supported or API credentials are missing
    """
    llm = get_langchain_llm(provider=provider, model=model)

    instructions_part = (
        f"\n\n额外指令:\n{additional_instructions}" if additional_instructions else ""
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是一个专业的写作风格模仿专家，能够根据提供的风格描述准确模仿各种写作风格。",
            ),
            (
                "human",
                """根据以下风格描述，用这种风格重写目标文章。

风格名称: {style_name}
风格描述: {style_description}
{instructions_part}

目标文章:
{article_text}

请严格按照上面的风格描述，重写目标文章，保持原文的核心内容不变。""",
            ),
        ]
    )

    chain = prompt | llm
    result = chain.invoke(
        {
            "style_name": style_name,
            "style_description": style_description,
            "instructions_part": instructions_part,
            "article_text": article_text,
        }
    )

    # Extract content from result (handle both string and AIMessage types)
    if hasattr(result, "content"):
        return str(result.content)
    return str(result)


def main():
    parser = argparse.ArgumentParser(description="根据风格描述重写文章")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="输入文章文件路径",
    )
    parser.add_argument(
        "--style-description",
        type=str,
        required=True,
        help="风格描述文件路径或直接使用文本",
    )
    parser.add_argument(
        "--style-name",
        type=str,
        default="",
        help="风格名称（可选）",
    )
    parser.add_argument(
        "--instructions",
        type=str,
        default="",
        help="额外指令，例如：让文章更简洁、增加幽默感等",
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

    # Read input article
    if not os.path.exists(args.input):
        print(f"错误：输入文件不存在: {args.input}")
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        article_text = f.read()

    # Read style description
    if os.path.exists(args.style_description):
        with open(args.style_description, "r", encoding="utf-8") as f:
            style_description = f.read()
    else:
        # Use the argument directly as style description text
        style_description = args.style_description

    print(f"正在重写文章...")
    print(f"输入长度: {len(article_text)} 字符")
    print(f"使用提供商: {args.provider}")
    if args.model:
        print(f"使用模型: {args.model}")
    if args.style_name:
        print(f"风格名称: {args.style_name}")
    if args.instructions:
        print(f"额外指令: {args.instructions}")

    try:
        result = rewrite_article(
            article_text=article_text,
            style_description=style_description,
            style_name=args.style_name,
            additional_instructions=args.instructions,
            provider=args.provider,
            model=args.model,
        )

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"\n重写完成，已保存到: {args.output}")
        else:
            print("\n重写结果:")
            print("=" * 60)
            print(result)
            print("=" * 60)

    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
