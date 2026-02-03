"""
Article Rewriter Tool - Manage article styles and generate rewrite prompts.

This module provides functionality to:
- List available writing styles from data/articles.json
- Load style descriptions
- Generate prompts for article rewriting (LLM call should be done externally)
- Save rewritten articles to styles
"""

import argparse
import os
import sys

# Add project root to path for importing utils
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils import get_style_by_name, list_styles


def generate_rewrite_prompt(
    article_text: str,
    style_description: str,
    style_name: str = "",
    additional_instructions: str = "",
) -> str:
    """
    Generate a prompt for rewriting an article according to a specified writing style.

    Args:
        article_text: The content to be rewritten
        style_description: Detailed description of target writing style
        style_name: Name of the style (optional)
        additional_instructions: Extra guidance for rewrite (optional)

    Returns:
        A complete prompt string for LLM to execute
    """
    instructions_part = f"\n\n额外指令:\n{additional_instructions}" if additional_instructions else ""

    prompt = f"""你是一个专业的写作风格模仿专家，能够根据提供的风格描述准确模仿各种写作风格。

根据以下风格描述，用这种风格重写目标文章。

风格名称: {style_name}
风格描述: {style_description}
{instructions_part}

目标文章:
{article_text}

请严格按照上面的风格描述，重写目标文章，保持原文的核心内容不变。"""

    return prompt


def main():
    parser = argparse.ArgumentParser(description="管理写作风格并生成重写提示")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="输入文章文件路径（使用 --list-styles 或 --generate-prompt 时可选）",
    )
    parser.add_argument(
        "--style-description",
        type=str,
        default=None,
        help="风格描述文件路径或直接使用文本（与 --use-saved-style 互斥）",
    )
    parser.add_argument(
        "--use-saved-style",
        type=str,
        default=None,
        help="从 data/articles.json 中读取指定名称的风格（与 --style-description 互斥）",
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
        "--generate-prompt",
        action="store_true",
        help="生成重写提示（用于外部 LLM 调用）",
    )
    parser.add_argument(
        "--save-article",
        action="store_true",
        help="将重写后的文章保存到 data/articles.json 对应风格的 articles 数组中",
    )
    parser.add_argument(
        "--list-styles",
        action="store_true",
        help="列出 data/articles.json 中所有可用的风格",
    )

    args = parser.parse_args()

    # List styles and exit
    if args.list_styles:
        styles = list_styles()
        print("可用的风格:")
        for style in styles:
            print(f"  - {style}")
        sys.exit(0)

    # Validate required arguments
    if not args.input and not args.generate_prompt:
        print("错误：必须指定 --input（除非使用 --list-styles）")
        sys.exit(1)

    # Validate style input options
    if args.style_description and args.use_saved_style:
        print("错误：不能同时使用 --style-description 和 --use-saved-style")
        sys.exit(1)

    if not args.style_description and not args.use_saved_style:
        print("错误：必须指定 --style-description 或 --use-saved-style")
        sys.exit(1)

    # Read input article
    if not os.path.exists(args.input):
        print(f"错误：输入文件不存在: {args.input}")
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        article_text = f.read()

    # Read style description
    style_description = None
    final_style_name = args.style_name

    if args.use_saved_style:
        style = get_style_by_name(args.use_saved_style)
        if not style:
            print(f"错误：未找到名为 '{args.use_saved_style}' 的风格")
            print("使用 --list-styles 查看可用的风格")
            sys.exit(1)

        style_description = style.get("description", "")
        if not final_style_name:
            final_style_name = style.get("name", args.use_saved_style)

        # Merge additional instructions from saved style
        saved_instructions = style.get("additional_instructions", "")
        if saved_instructions:
            if args.instructions:
                combined_instructions = f"{saved_instructions}\n\n{args.instructions}"
            else:
                combined_instructions = saved_instructions
            args.instructions = combined_instructions

        print(f"使用已保存风格: {args.use_saved_style}")
    else:
        # Read style description from file or text
        if os.path.exists(args.style_description):
            with open(args.style_description, "r", encoding="utf-8") as f:
                style_description = f.read()
        else:
            # Use the argument directly as style description text
            style_description = args.style_description

    # Generate prompt if requested
    if args.generate_prompt:
        prompt = generate_rewrite_prompt(
            article_text=article_text,
            style_description=style_description,
            style_name=final_style_name,
            additional_instructions=args.instructions,
        )
        print("生成的重写提示:")
        print("=" * 60)
        print(prompt)
        print("=" * 60)
        sys.exit(0)

    print(f"输入长度: {len(article_text)} 字符")
    if final_style_name:
        print(f"风格名称: {final_style_name}")
    if args.instructions:
        print(f"额外指令: {args.instructions}")
    print("\n提示：使用 --generate-prompt 参数生成完整的 LLM 提示")
    print("      或者使用 --save-article 将重写后的结果保存到风格数据库")


if __name__ == "__main__":
    main()
