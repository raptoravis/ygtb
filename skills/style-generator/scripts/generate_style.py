"""
Style Generator Tool - Manage writing styles and generate style analysis prompts.

This module provides functionality to:
- Read reference articles
- Generate prompts for style analysis (LLM call should be done externally)
- Save styles and articles to data/articles.json
"""

import argparse
import os
import sys
from datetime import datetime
from typing import List

# Add project root to path for importing utils
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils import load_styles, save_styles


def generate_style_prompt(
    reference_articles: List[str],
    style_name: str,
) -> str:
    """
    Generate a prompt for analyzing reference articles and generating style description.

    Args:
        reference_articles: List of reference article texts to analyze
        style_name: Name for the style being analyzed

    Returns:
        A complete prompt string for LLM to execute
    """
    reference_text = "\n\n".join([f"参考文章{i + 1}:\n{ref}" for i, ref in enumerate(reference_articles)])

    prompt = f"""你是一个专业的写作风格分析专家，能够准确捕捉文章的写作风格、语气、用词习惯和结构特点，并用简洁准确的语言描述这些风格特点。

分析以下参考文章的风格特点，生成一个详细的风格描述。

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
描述应该具体、准确，足以让AI理解和模仿这种写作风格。"""

    return prompt


def save_style_with_articles(
    style_name: str,
    style_description: str,
    reference_articles: List[str],
):
    """
    Save a style with reference articles to data/articles.json.

    Args:
        style_name: Name of the style
        style_description: Generated style description
        reference_articles: List of reference article texts
    """
    styles = load_styles()

    # Create article entries for reference
    article_entries = [
        {
            "content": article,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        for article in reference_articles
    ]

    new_style = {
        "name": style_name,
        "description": style_description,
        "additional_instructions": "",
        "articles": article_entries,
    }

    # Check if style with same name already exists
    existing_idx = None
    for i, style in enumerate(styles):
        if style.get("name") == style_name:
            existing_idx = i
            break

    if existing_idx is not None:
        # Update existing style
        styles[existing_idx] = new_style
        print(f"\n已更新风格 '{style_name}' 到 data/articles.json")
    else:
        # Add new style
        styles.append(new_style)
        print(f"\n已保存风格 '{style_name}' 到 data/articles.json")

    save_styles(styles)


def main():
    parser = argparse.ArgumentParser(description="管理写作风格并生成风格分析提示")
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
        "--generate-prompt",
        action="store_true",
        help="生成风格分析提示（用于外部 LLM 调用）",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="保存风格到 data/articles.json（需要先获得风格描述）",
    )
    parser.add_argument(
        "--style-description-file",
        type=str,
        help="风格描述文件路径（与 --save 配合使用）",
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

    print(f"读取 {len(reference_articles)} 篇参考文章...")
    print(f"风格名称: {args.style_name}")

    # Generate prompt if requested
    if args.generate_prompt:
        prompt = generate_style_prompt(
            reference_articles=reference_articles,
            style_name=args.style_name,
        )
        print("\n生成的风格分析提示:")
        print("=" * 60)
        print(prompt)
        print("=" * 60)
        sys.exit(0)

    # Save mode
    if args.save:
        if not args.style_description_file:
            print("错误：使用 --save 时必须指定 --style-description-file")
            sys.exit(1)

        if not os.path.exists(args.style_description_file):
            print(f"错误：风格描述文件不存在: {args.style_description_file}")
            sys.exit(1)

        with open(args.style_description_file, "r", encoding="utf-8") as f:
            style_description = f.read()

        save_style_with_articles(
            style_name=args.style_name,
            style_description=style_description,
            reference_articles=reference_articles,
        )
        print(f'\n现在可以使用 article-rewriter --style-name "{args.style_name}" 来使用此风格')
    else:
        print("\n提示：使用 --generate-prompt 生成风格分析提示")
        print("      获得风格描述后，使用 --save 保存到风格数据库")


if __name__ == "__main__":
    main()
