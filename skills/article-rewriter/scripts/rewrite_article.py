"""
Article Rewriter Tool - Manage article styles and generate rewrite prompts.

This module provides functionality to:
- List available writing styles from data/articles.json
- Load style descriptions
- Generate prompts for article rewriting (LLM call should be done externally)
- Save rewritten articles to history for future reference
- Track and clean up temporary files
"""

import argparse
import os
import sys

# Add project root to path for importing utils
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from termcolor import colored  # noqa: E402

from utils import (  # noqa: E402
    add_rewrite_history,
    delete_rewrite_history_entry,
    get_rewrite_history_by_style,
    get_rewrite_history_entry,
    get_style_by_name,
    list_rewrite_history,
    list_styles,
)

# Temporary files tracking
_temp_files = []


def track_temp_file(filepath: str):
    """Track a temporary file for cleanup."""
    _temp_files.append(filepath)


def cleanup_temp_files():
    """Clean up all tracked temporary files."""
    for filepath in _temp_files:
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(colored(f"已删除临时文件: {filepath}", "yellow"))
        except Exception as e:
            print(colored(f"删除临时文件失败 {filepath}: {e}", "red"))
    _temp_files.clear()


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
    parser = argparse.ArgumentParser(
        description="管理写作风格并生成重写提示",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 列出所有可用风格
  python rewrite_article.py --list-styles

  # 生成重写提示
  python rewrite_article.py --input article.txt --use-saved-style "幽默" --generate-prompt --output prompt.txt

  # 保存重写结果到历史
  python rewrite_article.py --input article.txt --use-saved-style "幽默" --save-to-history --rewrite-result result.txt

  # 查看历史记录
  python rewrite_article.py --list-history

  # 查看特定风格的历史
  python rewrite_article.py --list-history --style "幽默"

  # 删除历史记录
  python rewrite_article.py --delete-history 1

  # 导出重写结果
  python rewrite_article.py --export-history 1 --output export.txt
        """,
    )
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
        "--output",
        type=str,
        default=None,
        help="输出提示到指定文件（与 --generate-prompt 配合使用）",
    )
    parser.add_argument(
        "--rewrite-result",
        type=str,
        default=None,
        help="重写后的文章内容文件路径（与 --save-to-history 配合使用）",
    )
    parser.add_argument(
        "--save-to-history",
        action="store_true",
        help="将重写后的文章保存到 data/rewrite_history.json 历史记录中（供以后参考）",
    )
    parser.add_argument(
        "--list-styles",
        action="store_true",
        help="列出 data/articles.json 中所有可用的风格",
    )
    parser.add_argument(
        "--list-history",
        action="store_true",
        help="列出重写历史记录",
    )
    parser.add_argument(
        "--style",
        type=str,
        default=None,
        help="按风格名称筛选历史记录（与 --list-history 配合使用）",
    )
    parser.add_argument(
        "--delete-history",
        type=int,
        default=None,
        help="删除指定ID的历史记录",
    )
    parser.add_argument(
        "--export-history",
        type=int,
        default=None,
        help="导出指定ID的历史记录的重写内容（与 --output 配合使用）",
    )
    parser.add_argument(
        "--notes",
        type=str,
        default="",
        help="为重写记录添加备注（与 --save-to-history 配合使用）",
    )

    args = parser.parse_args()

    # List styles and exit
    if args.list_styles:
        styles = list_styles()
        print(colored("可用的风格:", "cyan"))
        for style in styles:
            print(f"  - {style}")
        sys.exit(0)

    # Delete history entry
    if args.delete_history is not None:
        if delete_rewrite_history_entry(args.delete_history):
            print(colored(f"已删除历史记录 [ID: {args.delete_history}]", "green"))
        else:
            print(colored(f"未找到 ID 为 {args.delete_history} 的历史记录", "yellow"))
        sys.exit(0)

    # Export history entry
    if args.export_history is not None:
        entry = get_rewrite_history_entry(args.export_history)
        if not entry:
            print(colored(f"未找到 ID 为 {args.export_history} 的历史记录", "yellow"))
            sys.exit(1)

        content = entry.get("rewritten_content", "")
        if args.output:
            try:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(content)
                print(colored(f"已导出到: {args.output}", "green"))
            except Exception as e:
                print(colored(f"导出失败: {e}", "red"))
        else:
            print(content)
        sys.exit(0)

    # List history and exit
    if args.list_history:
        if args.style:
            # List history for specific style
            history = get_rewrite_history_by_style(args.style)
            print(colored(f"风格 '{args.style}' 的历史记录:", "cyan"))
        else:
            # List all history
            history = list_rewrite_history()
            print(colored("重写历史记录:", "cyan"))

        if not history:
            print("暂无记录")
        else:
            print(colored(f"共有 {len(history)} 条记录", "cyan"))
            print("=" * 80)
            for entry in history[:20]:  # Show latest 20
                entry_id = entry.get("id", "N/A")
                timestamp = entry.get("timestamp", "N/A")
                style_name = entry.get("style_name", "未命名风格")
                notes = entry.get("notes", "")

                print(f"\n[ID: {entry_id}] {timestamp}")
                print(f"  风格: {style_name}")
                if notes:
                    print(f"  备注: {notes}")

                # Show preview of original content
                original = entry.get("original_content", "")
                if original:
                    preview = original[:100]
                    if len(original) > 100:
                        preview += "..."
                    print(f"  原文预览: {preview}")

            print("=" * 80)
            if len(history) > 20:
                print(colored(f"... 还有 {len(history) - 20} 条记录", "yellow"))
        sys.exit(0)

    # Validate required arguments for main workflow
    if not args.input:
        print(colored("错误：必须指定 --input 参数", "red"))
        sys.exit(1)

    # Validate style input options
    if args.style_description and args.use_saved_style:
        print(colored("错误：不能同时使用 --style-description 和 --use-saved-style", "red"))
        sys.exit(1)

    if not args.style_description and not args.use_saved_style:
        print(colored("错误：必须指定 --style-description 或 --use-saved-style", "red"))
        sys.exit(1)

    # Read input article
    if not os.path.exists(args.input):
        print(colored(f"错误：输入文件不存在: {args.input}", "red"))
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        article_text = f.read()

    # Read style description
    style_description = None
    final_style_name = args.style_name

    if args.use_saved_style:
        style = get_style_by_name(args.use_saved_style)
        if not style:
            print(colored(f"错误：未找到名为 '{args.use_saved_style}' 的风格", "red"))
            print(colored("使用 --list-styles 查看可用的风格", "yellow"))
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

        print(colored(f"使用已保存风格: {args.use_saved_style}", "cyan"))
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

        # Save to output file if specified
        if args.output:
            try:
                output_dir = os.path.dirname(args.output)
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)

                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(prompt)

                print(colored(f"提示已保存到: {args.output}", "green"))
                track_temp_file(args.output)

                # Also print to console
                print("\n生成的重写提示:")
                print("=" * 60)
                print(prompt)
                print("=" * 60)
                sys.exit(0)
            except Exception as e:
                print(colored(f"保存提示文件失败: {e}", "red"))
                sys.exit(1)
        else:
            # Just print to console
            print("生成的重写提示:")
            print("=" * 60)
            print(prompt)
            print("=" * 60)
            sys.exit(0)

    # Save rewritten article to history if requested
    if args.save_to_history:
        # Validate required parameters
        if not args.rewrite_result:
            print(
                colored(
                    "错误：使用 --save-to-history 时必须指定 --rewrite-result 参数",
                    "red",
                )
            )
            sys.exit(1)

        # Read the rewritten article
        if not os.path.exists(args.rewrite_result):
            print(colored(f"错误：重写结果文件不存在: {args.rewrite_result}", "red"))
            sys.exit(1)

        with open(args.rewrite_result, "r", encoding="utf-8") as f:
            rewritten_content = f.read()

        # Determine style name
        if args.use_saved_style:
            save_style_name = args.use_saved_style
        elif final_style_name:
            save_style_name = final_style_name
        else:
            print(
                colored(
                    "错误：无法确定风格名称，请使用 --use-saved-style 或 --style-name",
                    "red",
                )
            )
            sys.exit(1)

        # Save to history
        try:
            entry_id = add_rewrite_history(
                style_name=save_style_name,
                original_content=article_text,
                rewritten_content=rewritten_content,
                original_file=args.input,
                prompt_file=args.output if hasattr(args, "output") else "",
                notes=args.notes,
            )

            print(
                colored(
                    f"重写文章已成功保存到历史记录 [ID: {entry_id}]，风格: '{save_style_name}'",
                    "green",
                )
            )
            print(colored("历史记录保存在 data/rewrite_history.json", "cyan"))

            # Clean up the rewrite result file if it exists
            try:
                if os.path.exists(args.rewrite_result):
                    os.remove(args.rewrite_result)
                    print(colored(f"已删除重写结果文件: {args.rewrite_result}", "yellow"))
            except Exception as e:
                print(colored(f"删除重写结果文件失败: {e}", "red"))

            # Clean up any tracked temporary files
            cleanup_temp_files()
            sys.exit(0)
        except Exception as e:
            print(colored(f"保存历史记录时出错: {e}", "red"))
            sys.exit(1)

    # Default: show info
    print(colored(f"输入长度: {len(article_text)} 字符", "cyan"))
    if final_style_name:
        print(colored(f"风格名称: {final_style_name}", "cyan"))
    if args.instructions:
        print(colored(f"额外指令: {args.instructions}", "cyan"))
    print("\n提示：")
    print("  1. 使用 --generate-prompt --output prompt.txt 生成提示并保存到文件")
    print("  2. 在外部使用 LLM 根据提示重写文章，将结果保存到文件")
    print("  3. 使用 --save-to-history --rewrite-result rewritten.txt [--notes '备注'] 保存到历史记录")
    print("  4. 使用 --list-history 查看所有历史记录（供以后参考）")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(colored("\n操作已取消", "yellow"))
        sys.exit(0)
    except Exception as e:
        print(colored(f"发生错误: {e}", "red"))
        import traceback

        traceback.print_exc()
        sys.exit(1)
