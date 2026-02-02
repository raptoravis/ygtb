import argparse
import html
import json
import os
from datetime import datetime

from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.document import Document
from bokeh.layouts import column, row
from bokeh.models import Button, Div, Select, TabPanel, Tabs, TextAreaInput, TextInput
from bokeh.server.server import Server
from langchain.prompts import ChatPromptTemplate
from termcolor import colored

from utils import get_langchain_llm, glog_info

HOME_PATH: str = os.path.join(os.path.expanduser("~"), ".ygtb")

ARTICLES_FILE = "data/articles.json"
HISTORY_FILE = os.path.join(HOME_PATH, "data/history.json")


def load_styles():
    if os.path.exists(ARTICLES_FILE):
        with open(ARTICLES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("styles", [])
    return []


def save_styles(styles):
    os.makedirs(os.path.dirname(ARTICLES_FILE), exist_ok=True)
    with open(ARTICLES_FILE, "w", encoding="utf-8") as f:
        json.dump({"styles": styles}, f, ensure_ascii=False, indent=2)


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


def save_history(history):
    """保存历史记录"""
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump({"history": history}, f, ensure_ascii=False, indent=2)


def add_history_entry(original_text, result_text, style_name, additional_instructions=""):
    """添加新的历史记录条目"""
    history = load_history()

    # 创建新的历史记录条目
    entry = {
        "id": len(history),
        "original_text": original_text,
        "result_text": result_text,
        "style_name": style_name,
        "additional_instructions": additional_instructions,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date": datetime.now().strftime("%Y-%m-%d"),
    }

    history.append(entry)
    save_history(history)
    return entry


def generate_style_description_from_articles(reference_articles, style_name, provider, model):
    llm = get_langchain_llm(provider=provider, model=model)

    reference_text = "\n\n".join([f"参考文章{i + 1}:\n{ref}" for i, ref in enumerate(reference_articles)])

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是一个专业的写作风格分析专家，能够准确捕捉文章的写作风格、语气、用词习惯和结构特点，并用简洁准确的语言描述这些风格特点。",
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
    return str(result.content)


def analyze_article_with_style(
    article_text,
    style_description,
    style_name,
    additional_instructions,
    provider,
    model,
):
    llm = get_langchain_llm(provider=provider, model=model)

    instructions_part = f"\n\n额外指令:\n{additional_instructions}" if additional_instructions else ""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "你是一个专业的写作风格模仿专家，能够根据提供的风格描述准确模仿各种写作风格。"),
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
    return str(result.content)


class StyleTab:
    def __init__(self, style_data, styles_list, update_ui_callback):
        self.style_data = style_data
        self.styles_list = styles_list
        self.update_ui_callback = update_ui_callback

        self.name_input = TextInput(
            value=style_data.get("name", ""),
            title="风格名称",
            sizing_mode="stretch_width",
        )

        self.desc_input = TextAreaInput(
            value=style_data.get("description", ""),
            title="风格描述",
            placeholder="描述这个风格的特点...",
            rows=6,
            sizing_mode="stretch_width",
        )

        # 风格专有的额外指令文本框
        self.style_additional_instructions_input = TextAreaInput(
            value=style_data.get("additional_instructions", ""),
            title="风格额外指令（可选）",
            placeholder="输入该风格专有的额外指令，例如：保持特定句式、使用特定词汇等...",
            rows=4,
            sizing_mode="stretch_width",
        )

        self.article_input = TextAreaInput(
            title="输入参考文章",
            placeholder="在这里输入文章内容...",
            value="",
            rows=8,
            sizing_mode="stretch_width",
            max_length=10000000,
        )

        self.add_article_button = Button(
            label="添加文章",
            button_type="success",
            height=40,
            sizing_mode="stretch_width",
        )

        self.article_select = Select(title="选择要删除的文章", value="", options=[], sizing_mode="stretch_width")
        self.delete_article_button = Button(
            label="删除选中文章",
            button_type="danger",
            height=40,
            sizing_mode="stretch_width",
        )

        self.add_article_button.on_click(self.add_article)
        self.delete_article_button.on_click(self.delete_selected_article)

        self.articles_preview_div = column(children=[], sizing_mode="stretch_width")
        self.update_articles_display()

        self.panel = TabPanel(
            child=column(
                row(self.name_input, sizing_mode="stretch_width"),
                self.desc_input,
                self.style_additional_instructions_input,
                self.article_input,
                row(
                    self.add_article_button,
                    self.article_select,
                    self.delete_article_button,
                ),
                self.articles_preview_div,
                sizing_mode="stretch_width",
            ),
            title=style_data.get("name", "未命名风格"),
        )

        self.name_input.on_change("value", self.on_name_change)
        self.desc_input.on_change("value", self.on_desc_change)
        self.style_additional_instructions_input.on_change("value", self.on_additional_instructions_change)

    def on_name_change(self, attr, old, new):
        new_name = new.strip() or "未命名风格"
        self.style_data["name"] = new_name
        self.panel.title = new_name
        self.update_ui_callback()

    def on_desc_change(self, attr, old, new):
        self.style_data["description"] = new
        save_styles(self.styles_list)

    def on_additional_instructions_change(self, attr, old, new):
        self.style_data["additional_instructions"] = new
        save_styles(self.styles_list)

    def update_articles_display(self):
        articles = self.style_data.get("articles", [])
        children = []

        # Update select options
        options = [(str(i), f"文章 {i + 1}") for i in range(len(articles))]
        self.article_select.options = options

        # If the current value is no longer valid, reset it
        if self.article_select.value and self.article_select.value not in [opt[0] for opt in options]:
            self.article_select.value = ""

        if not articles:
            children.append(Div(text="<p>暂无参考文章</p>"))
        else:
            children.append(Div(text="<h4>参考文章列表:</h4>"))
            for i, article in enumerate(articles):
                article_div = Div(
                    text=f"""
                        <p><strong>文章 {i + 1}</strong> - <small>添加时间: {article.get("time", "N/A")}</small></p>
                        <div style="white-space: pre-wrap; overflow-wrap: break-word; text-align: left;">
                            {html.escape(article["content"])}
                        </div>
                        """,
                    sizing_mode="stretch_width",
                )
                article_wrapper = row(
                    article_div,
                    sizing_mode="stretch_width",
                    styles={
                        "border": "1px solid #ddd",
                        "padding": "15px",
                        "margin": "5px 0",
                        "background-color": "#f9f9f9",
                        "box-sizing": "border-box",
                        "width": "100%",
                        "max-width": "100%",
                    },
                )
                children.append(article_wrapper)

        self.articles_preview_div.children = children

    def add_article(self):
        content = self.article_input.value.strip()
        if content:
            if "articles" not in self.style_data:
                self.style_data["articles"] = []
            self.style_data["articles"].append(
                {
                    "content": content,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            save_styles(self.styles_list)
            self.article_input.value = ""
            self.update_articles_display()

    def delete_selected_article(self):
        val = self.article_select.value
        if val:
            try:
                idx = int(val)
                self.delete_article_by_index(idx)
                self.article_select.value = ""
            except ValueError:
                pass

    def delete_article_by_index(self, index):
        articles = self.style_data.get("articles", [])
        if 0 <= index < len(articles):
            del self.style_data["articles"][index]
            save_styles(self.styles_list)
            self.update_articles_display()

    def update_data(self):
        new_name = self.name_input.value or "未命名风格"
        self.style_data["name"] = new_name
        self.style_data["description"] = self.desc_input.value or ""
        self.style_data["additional_instructions"] = self.style_additional_instructions_input.value or ""
        self.panel.title = new_name


def make_document(doc: Document, provider, model):
    styles_list = load_styles()

    add_style_button = Button(
        label="添加新风格",
        button_type="primary",
        height=40,
        sizing_mode="stretch_width",
    )

    style_select = Select(title="选择要删除的风格", value="", options=[], sizing_mode="stretch_width")
    delete_style_button = Button(
        label="删除选中风格",
        button_type="danger",
        height=40,
        sizing_mode="stretch_width",
    )

    style_tabs = []
    tabs_widget = Tabs(tabs=[])
    left_column = None  # 先声明变量，稍后赋值

    def create_style_tabs():
        nonlocal style_tabs
        style_tabs = []

        for style_data in styles_list:
            style_tab = StyleTab(
                style_data,
                styles_list,
                update_style_tabs,
            )
            style_tabs.append(style_tab)

        return Tabs(tabs=[tab.panel for tab in style_tabs])

    def update_style_tabs(new_tab_index=None):
        nonlocal tabs_widget, left_column
        current_active = tabs_widget.active
        save_styles(styles_list)
        new_tabs_widget = create_style_tabs()
        # 如果指定了新 tab 索引，则切换到该 tab；否则保持当前激活的 tab
        if new_tab_index is not None and 0 <= new_tab_index < len(new_tabs_widget.tabs):
            new_tabs_widget.active = new_tab_index
        elif current_active is not None and current_active < len(new_tabs_widget.tabs):
            new_tabs_widget.active = current_active
        left_column.children[2] = new_tabs_widget
        tabs_widget = new_tabs_widget
        update_style_select_options()

    def update_style_select_options():
        options = [(str(i), s.get("name", "未命名风格")) for i, s in enumerate(styles_list)]
        style_select.options = options
        # Reset selection if invalid
        if style_select.value and style_select.value not in [opt[0] for opt in options]:
            style_select.value = ""

    def add_style():
        new_style = {
            "name": "新风格",
            "description": "",
            "additional_instructions": "",
            "articles": [],
        }
        styles_list.append(new_style)
        save_styles(styles_list)
        # 切换到新创建的 tab（最后一个）
        update_style_tabs(new_tab_index=len(styles_list) - 1)

    def delete_selected_style():
        val = style_select.value
        if val:
            try:
                idx = int(val)
                if 0 <= idx < len(styles_list):
                    del styles_list[idx]
                    save_styles(styles_list)
                    style_select.value = ""
                    update_style_tabs()
            except ValueError:
                pass

    add_style_button.on_click(add_style)
    delete_style_button.on_click(delete_selected_style)

    update_style_select_options()

    target_article_input = TextAreaInput(
        title="输入需要风格转换的文章",
        placeholder="在这里输入需要转换的文章...",
        value="",
        rows=15,
        sizing_mode="stretch_width",
        max_length=10000000,
    )

    style_select_div = Div(text="<p>选择要使用的风格（在左侧切换tab）</p>", sizing_mode="stretch_width")

    # 历史记录相关组件
    history_div = Div(text="<h3>历史记录</h3>", sizing_mode="stretch_width")

    # 历史记录下拉列表
    history_select = Select(title="选择历史记录", value="", options=[], sizing_mode="stretch_width")

    # 恢复历史记录按钮
    restore_history_button = Button(
        label="恢复选中记录",
        button_type="warning",
        height=40,
        disabled=True,
        sizing_mode="stretch_width",
    )

    # 清除历史记录按钮
    clear_history_button = Button(
        label="清除历史记录",
        button_type="danger",
        height=40,
        sizing_mode="stretch_width",
    )

    analyze_button = Button(label="重写", button_type="primary", height=50, sizing_mode="stretch_width")

    additional_instructions_input = TextAreaInput(
        title="额外指令（可选）",
        placeholder="输入额外的指令，例如：让文章更简洁、增加幽默感、使用更正式的语气等...",
        value="",
        rows=4,
        sizing_mode="stretch_width",
    )

    result_div = Div(text="", sizing_mode="stretch_width")

    # 添加复制按钮
    copy_button = Button(
        label="复制结果",
        button_type="success",
        height=40,
        disabled=True,
        sizing_mode="stretch_width",
    )

    # 清除额外指令按钮
    clear_instructions_button = Button(
        label="清除额外指令",
        button_type="warning",
        height=50,
        sizing_mode="stretch_width",
    )

    def copy_to_clipboard():
        """使用Python复制文本到剪贴板"""
        try:
            # 从HTML中提取纯文本内容
            import re

            result_text = ""

            if result_div.text and "使用 " in result_div.text:
                # 更简单的提取方法：直接查找包含实际内容的div
                # 查找包含 "white-space: pre-wrap" 的div
                pattern = r'white-space: pre-wrap; overflow-wrap: break-word;">([^<]*)</div>'
                match = re.search(pattern, result_div.text)

                if match:
                    result_text = match.group(1)
                    # 去除HTML转义字符
                    result_text = html.unescape(result_text)
                    result_text = result_text.strip()
                else:
                    # 备用方法：查找div标签内的文本内容
                    # 查找所有div标签并提取文本内容
                    div_pattern = r"<div[^>]*>([^<]*)</div>"
                    matches = re.findall(div_pattern, result_div.text)
                    for match in matches:
                        if match.strip() and not match.startswith("使用 "):
                            result_text = match.strip()
                            result_text = html.unescape(result_text)
                            break

            if result_text:
                try:
                    import pyperclip

                    # 复制到剪贴板
                    pyperclip.copy(result_text)
                    copy_button.label = "已复制"
                except ImportError:
                    # 如果pyperclip不可用，使用备用方法
                    import platform
                    import subprocess

                    # 根据操作系统使用不同的复制命令
                    system = platform.system()
                    if system == "Darwin":  # macOS
                        subprocess.run("pbcopy", universal_newlines=True, input=result_text)
                    elif system == "Windows":  # Windows
                        subprocess.run("clip", universal_newlines=True, input=result_text)
                    else:  # Linux
                        subprocess.run("xclip", universal_newlines=True, input=result_text)

                    copy_button.label = "已复制"

                # 2秒后恢复按钮状态
                def reset_copy_button():
                    copy_button.label = "复制结果"

                doc.add_timeout_callback(reset_copy_button, 2000)
            else:
                copy_button.label = "无内容"

                # 2秒后恢复按钮状态
                def reset_copy_button():
                    copy_button.label = "复制结果"

                doc.add_timeout_callback(reset_copy_button, 2000)

        except Exception:
            copy_button.label = "复制失败"

            def reset_copy_button():
                copy_button.label = "复制结果"

            doc.add_timeout_callback(reset_copy_button, 2000)

    copy_button.on_click(copy_to_clipboard)

    def update_history_select():
        """更新历史记录下拉列表"""
        history = load_history()
        options = [("", "选择历史记录")]

        for entry in reversed(history):  # 最新的记录在前面
            timestamp = entry.get("timestamp", "")
            style_name = entry.get("style_name", "未命名风格")
            preview = (
                entry.get("original_text", "")[:50] + "..."
                if len(entry.get("original_text", "")) > 50
                else entry.get("original_text", "")
            )

            option_text = f"{timestamp} - {style_name}: {preview}"
            options.append((str(entry["id"]), option_text))

        history_select.options = options

        # 如果没有历史记录，禁用恢复按钮
        restore_history_button.disabled = len(history) == 0

    def restore_selected_history():
        """恢复选中的历史记录"""
        selected_id = history_select.value
        if selected_id:
            history = load_history()
            entry = next((e for e in history if str(e["id"]) == selected_id), None)

            if entry:
                # 恢复原文到输入框
                target_article_input.value = entry["original_text"]

                # 恢复额外指令
                additional_instructions = entry.get("additional_instructions", "")
                additional_instructions_input.value = additional_instructions

                # 恢复结果到显示区域
                style_name = entry.get("style_name", "未命名风格")
                result_div.text = f"""
                <h3>使用 "{style_name}" 风格重写结果:</h3>
                <div style="border: 1px solid #4CAF50; padding: 15px; margin: 10px 0; background-color: #f9f9f9; box-sizing: border-box;">
                    <div style="white-space: pre-wrap; overflow-wrap: break-word;">{html.escape(entry["result_text"])}</div>
                </div>
                """

                # 启用复制按钮
                copy_button.disabled = False

                # 显示恢复成功消息
                def show_success():
                    restore_history_button.label = "恢复成功"

                    def reset_button():
                        restore_history_button.label = "恢复选中记录"

                    doc.add_timeout_callback(reset_button, 2000)

                doc.add_next_tick_callback(show_success)

    def clear_history():
        """清除所有历史记录"""
        save_history([])
        update_history_select()
        history_select.value = ""
        clear_history_button.label = "已清除"

        def reset_button():
            clear_history_button.label = "清除历史记录"

        doc.add_timeout_callback(reset_button, 2000)

    # 绑定事件
    restore_history_button.on_click(restore_selected_history)
    clear_history_button.on_click(clear_history)

    # 清除额外指令
    def clear_instructions():
        additional_instructions_input.value = ""
        clear_instructions_button.label = "已清除"

        def reset_button():
            clear_instructions_button.label = "清除额外指令"

        doc.add_timeout_callback(reset_button, 2000)

    clear_instructions_button.on_click(clear_instructions)

    # 当下拉列表选择变化时启用/禁用恢复按钮
    def on_history_select_change(attr, old, new):
        restore_history_button.disabled = not bool(new)

    history_select.on_change("value", on_history_select_change)

    # 初始化历史记录下拉列表
    update_history_select()

    # 自动恢复最近一次的历史记录
    def auto_restore_last_history():
        history = load_history()
        if history:
            # 找到最新的记录（id最大的）
            last_entry = max(history, key=lambda x: x["id"])

            # 恢复原文到输入框
            target_article_input.value = last_entry["original_text"]

            # 恢复额外指令
            additional_instructions = last_entry.get("additional_instructions", "")
            additional_instructions_input.value = additional_instructions

            # 恢复结果到显示区域
            style_name = last_entry.get("style_name", "未命名风格")
            result_div.text = f"""
            <h3>使用 "{style_name}" 风格重写结果:</h3>
            <div style="border: 1px solid #4CAF50; padding: 15px; margin: 10px 0; background-color: #f9f9f9; box-sizing: border-box;">
                <div style="white-space: pre-wrap; overflow-wrap: break-word;">{html.escape(last_entry["result_text"])}</div>
            </div>
            """

            # 启用复制按钮
            copy_button.disabled = False

            # 自动选中对应的历史记录
            history_select.value = str(last_entry["id"])

    # 在文档加载完成后自动恢复最近的历史记录
    doc.add_next_tick_callback(auto_restore_last_history)

    def analyze_and_rewrite():
        # 禁用按钮并显示分析中状态
        analyze_button.label = "重写中..."
        analyze_button.button_type = "default"
        analyze_button.disabled = True
        result_div.text = "<p style='color: blue;'>正在重写文章，请稍候...</p>"

        def async_analysis():
            try:
                target_article = target_article_input.value.strip()
                if not target_article:
                    result_div.text = "<p style='color: red;'>请输入需要转换的文章</p>"
                    return

                current_tabs_widget = left_column.children[2]
                if not style_tabs:
                    result_div.text = "<p style='color: red;'>请先创建一个风格</p>"
                    return

                if len(style_tabs) == 0:
                    result_div.text = "<p style='color: red;'>请先创建一个风格</p>"
                    return

                active_tab_idx = getattr(current_tabs_widget, "active", 0)
                if active_tab_idx is None or active_tab_idx >= len(style_tabs):
                    result_div.text = "<p style='color: red;'>请先选择一个风格</p>"
                    return

                active_style = style_tabs[active_tab_idx].style_data
                style_description = active_style.get("description", "")
                if not style_description:
                    result_div.text = "<p style='color: red;'>请先生成风格描述</p>"
                    return

                style_tabs[active_tab_idx].update_data()
                save_styles(styles_list)

                style_name = active_style.get("name", "未命名风格")

                # 合并额外指令：风格的额外指令 + 全局额外指令
                style_instructions = active_style.get("additional_instructions", "").strip()
                global_instructions = additional_instructions_input.value.strip()

                # 风格指令在前，全局指令在后
                if style_instructions and global_instructions:
                    combined_instructions = f"{style_instructions}\n\n{global_instructions}"
                elif style_instructions:
                    combined_instructions = style_instructions
                else:
                    combined_instructions = global_instructions

                result = analyze_article_with_style(
                    target_article,
                    style_description,
                    style_name,
                    combined_instructions,
                    provider,
                    model,
                )
                result_div.text = f"""
                <h3>使用 "{style_name}" 风格重写结果:</h3>
                <div style="border: 1px solid #4CAF50; padding: 15px; margin: 10px 0; background-color: #f9f9f9; box-sizing: border-box;">
                    <div style="white-space: pre-wrap; overflow-wrap: break-word;">{html.escape(result)}</div>
                </div>
                """
                # 启用复制按钮
                copy_button.disabled = False

                # 保存历史记录（使用合并后的额外指令）
                add_history_entry(target_article, result, style_name, combined_instructions)
                update_history_select()
            except Exception as e:
                result_div.text = f"<p style='color: red;'>重写出错: {str(e)}</p>"
            finally:
                # 恢复按钮状态
                analyze_button.label = "重写"
                analyze_button.button_type = "primary"
                analyze_button.disabled = False

        # 使用异步执行避免阻塞UI
        doc.add_next_tick_callback(async_analysis)

    analyze_button.on_click(analyze_and_rewrite)

    initial_tabs = create_style_tabs()
    tabs_widget = initial_tabs

    generate_style_button = Button(label="生成风格描述", button_type="success", width=150, height=40)

    def generate_selected_style():
        current_tabs_widget = left_column.children[2]
        if not style_tabs:
            return

        active_tab_idx = getattr(current_tabs_widget, "active", 0)
        if active_tab_idx is None or active_tab_idx >= len(style_tabs):
            return

        active_tab = style_tabs[active_tab_idx]
        articles = active_tab.style_data.get("articles", [])
        if not articles:
            active_tab.desc_input.value = "错误：没有参考文章，请先添加参考文章"
            return

        style_name = active_tab.style_data.get("name", "未命名风格")
        reference_articles = [a["content"] for a in articles]

        generate_style_button.label = "生成中..."
        generate_style_button.button_type = "default"
        generate_style_button.disabled = True

        def update_ui(result=None, error=None):
            if error:
                current_tabs_widget = left_column.children[2]
                active_tab_idx = getattr(current_tabs_widget, "active", 0)
                if active_tab_idx is not None and active_tab_idx < len(style_tabs):
                    style_tabs[active_tab_idx].desc_input.value = f"生成失败: {error}"
            elif result is not None:
                current_tabs_widget = left_column.children[2]
                active_tab_idx = getattr(current_tabs_widget, "active", 0)
                if active_tab_idx is not None and active_tab_idx < len(style_tabs):
                    style_tabs[active_tab_idx].style_data["description"] = result
                    style_tabs[active_tab_idx].desc_input.value = result
                    save_styles(styles_list)
            generate_style_button.label = "生成风格"
            generate_style_button.button_type = "success"
            generate_style_button.disabled = False

        from concurrent.futures import ThreadPoolExecutor

        executor = ThreadPoolExecutor(max_workers=1)

        def background_task():
            try:
                result = generate_style_description_from_articles(reference_articles, style_name, provider, model)

                def callback_success():
                    update_ui(result=result, error=None)

                doc.add_next_tick_callback(callback_success)
            except Exception as e:
                error_msg = str(e)

                def callback_error():
                    update_ui(result=None, error=error_msg)

                doc.add_next_tick_callback(callback_error)

        executor.submit(background_task)

    generate_style_button.on_click(generate_selected_style)

    left_column = column(
        Div(text="<h2>风格管理</h2>", sizing_mode="stretch_width"),
        row(add_style_button, style_select, delete_style_button, generate_style_button),
        initial_tabs,
        sizing_mode="stretch_width",
    )

    right_column = column(
        Div(text="<h2>风格转换</h2>", sizing_mode="stretch_width"),
        style_select_div,
        target_article_input,
        row(analyze_button, clear_instructions_button),
        additional_instructions_input,
        row(copy_button),
        result_div,
        # 历史记录部分
        history_div,
        history_select,
        row(restore_history_button, clear_history_button),
        sizing_mode="stretch_width",
    )

    layout = column(
        Div(text="<h1>文章风格分析与重写工具</h1>", sizing_mode="stretch_width"),
        row(left_column, right_column, sizing_mode="stretch_both"),
        sizing_mode="stretch_width",
    )

    doc.add_root(layout)
    doc.title = "文章风格分析工具"


def main():
    parser = argparse.ArgumentParser(description="文章风格分析与重写工具")
    parser.add_argument(
        "--provider",
        type=str,
        default="antigravity",
        help="LLM 提供商 (ollama/antigravity/dashscope)",
    )
    parser.add_argument("--model", type=str, default=None, help="LLM 模型名称")
    args = parser.parse_args()

    def make_document_with_args(doc: Document):
        return make_document(doc, provider=args.provider, model=args.model)

    apps = {"/": Application(FunctionHandler(make_document_with_args))}

    port = 6006
    server = Server(apps, port=port, session_token_expiration=3600)

    glog_info(colored(f"使用 LLM 提供商: {args.provider}", "cyan"))
    if args.model:
        glog_info(colored(f"使用 LLM 模型: {args.model}", "cyan"))
    print("服务器正在启动...")
    print(f"访问 http://localhost:{port}/ 使用文章风格分析工具")

    try:
        server.start()
        server.io_loop.add_callback(server.show, "/")
        server.io_loop.start()
    except KeyboardInterrupt:
        print("正在停止服务器...")
        server.io_loop.stop()
        print("服务器已停止")


if __name__ == "__main__":
    main()
