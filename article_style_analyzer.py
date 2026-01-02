import argparse
import json
import os
from datetime import datetime

from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.document import Document
from bokeh.layouts import column, row
from bokeh.models import Button, Div, TabPanel, Tabs, TextAreaInput, TextInput
from bokeh.server.server import Server
from crewai import Agent, Crew, Process, Task
from termcolor import colored

from utils import get_llm, glog_info

ARTICLES_FILE = "data/articles.json"


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


def analyze_article_with_style(
    article_text, reference_articles, style_name, style_description, provider, model
):
    llm = get_llm(provider=provider, model=model)
    analyzer = Agent(
        role="文章风格分析师",
        goal="分析参考文章的风格并用这种风格重写目标文章",
        backstory="你是一个专业的写作风格分析专家，能够准确捕捉文章的写作风格、语气、用词习惯和结构特点。",
        llm=llm,
        verbose=True,
    )

    reference_text = "\n\n".join(
        [f"参考文章{i + 1}:\n{ref}" for i, ref in enumerate(reference_articles)]
    )

    task = Task(
        description=f"""参考以下文章的风格特点，用相同的风格重写目标文章。

风格名称: {style_name}
风格描述: {style_description}

参考文章:
{reference_text}

目标文章:
{article_text}

请分析参考文章的：
1. 写作风格（正式/随意/学术/文学等）
2. 语言特点（用词习惯、句式结构）
3. 情感基调（严肃/轻松/热情/客观等）
4. 文章结构（开头/正文/结尾的组织方式）

然后用这种风格重写目标文章，保持原文的核心内容不变。
""",
        agent=analyzer,
        expected_output="重写后的文章内容",
    )

    crew = Crew(
        agents=[analyzer],
        tasks=[task],
        process=Process.sequential,
    )

    result = crew.kickoff()
    return str(result)


class StyleTab:
    def __init__(
        self, style_data, styles_list, update_ui_callback, delete_style_callback
    ):
        self.style_data = style_data
        self.styles_list = styles_list
        self.update_ui_callback = update_ui_callback
        self.delete_style_callback = delete_style_callback

        self.name_input = TextInput(
            value=style_data.get("name", ""),
            title="风格名称",
            width=560,
        )

        self.desc_input = TextAreaInput(
            value=style_data.get("description", ""),
            title="风格描述",
            placeholder="描述这个风格的特点...",
            rows=4,
            width=680,
        )

        self.desc_input = TextAreaInput(
            value=style_data.get("description", ""),
            title="风格描述",
            placeholder="描述这个风格的特点...",
            rows=4,
            width=700,
        )

        self.article_input = TextAreaInput(
            title="输入参考文章",
            placeholder="在这里输入文章内容...",
            value="",
            rows=15,
            width=700,
        )

        self.add_article_button = Button(
            label="添加文章", button_type="success", width=120, height=40
        )
        self.delete_style_button = Button(
            label="删除风格", button_type="danger", width=120, height=40
        )

        self.articles_preview_div = Div(text="", width=700)

        self.add_article_button.on_click(self.add_article)
        self.delete_style_button.on_click(self.delete_style)

        self.update_articles_display()

        self.delete_article_button = Button(
            label="删除选中的文章", button_type="danger", width=680, height=40
        )
        self.delete_article_button.on_click(self.delete_article)

        self.panel = TabPanel(
            child=column(
                row(self.name_input, self.delete_style_button),
                self.desc_input,
                self.article_input,
                row(self.add_article_button),
                self.articles_preview_div,
                self.delete_article_button,
            ),
            title=style_data.get("name", "未命名风格"),
        )

    def update_articles_display(self):
        articles = self.style_data.get("articles", [])
        if not articles:
            self.articles_preview_div.text = "<p>暂无参考文章</p>"
        else:
            html = "<h4>参考文章列表（点击下方按钮删除最后一篇）:</h4>"
            for i, article in enumerate(articles):
                is_last = i == len(articles) - 1
                border_color = "#4CAF50" if is_last else "#ddd"
                bg_color = "#e8f5e9" if is_last else "#f5f5f5"
                last_label = " <strong>[将被删除]</strong>" if is_last else ""
                html += f"""
                <div style="border: 1px solid {border_color}; padding: 8px; margin: 5px 0; background-color: {bg_color};">
                    <p><strong>文章 {i + 1}{last_label}</strong> - <small>添加时间: {article.get("time", "N/A")}</small></p>
                    <p>{article["content"]}...</p>
                </div>
                """
            self.articles_preview_div.text = html

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

    def delete_article(self):
        articles = self.style_data.get("articles", [])
        if articles:
            self.style_data["articles"] = articles[:-1]
            save_styles(self.styles_list)
            self.update_articles_display()

    def delete_style(self):
        self.delete_style_callback(self.style_data)

    def update_data(self):
        self.style_data["name"] = self.name_input.value or "未命名风格"
        self.style_data["description"] = self.desc_input.value or ""
        self.update_ui_callback()


def make_document(doc: Document, provider, model):
    styles_list = load_styles()

    add_style_button = Button(
        label="添加新风格", button_type="primary", width=680, height=40
    )

    style_tabs = []
    tabs_widget = Tabs(tabs=[])

    def create_style_tabs():
        nonlocal style_tabs
        style_tabs = []

        for style_data in styles_list:
            style_tab = StyleTab(
                style_data,
                styles_list,
                update_style_tabs,
                delete_style,
            )
            style_tabs.append(style_tab)

        return Tabs(tabs=[tab.panel for tab in style_tabs])

    def update_style_tabs():
        nonlocal tabs_widget
        save_styles(styles_list)
        new_tabs_widget = create_style_tabs()
        left_column.children[2] = new_tabs_widget
        tabs_widget = new_tabs_widget

    def add_style():
        new_style = {
            "name": "新风格",
            "description": "",
            "articles": [],
        }
        styles_list.append(new_style)
        save_styles(styles_list)
        update_style_tabs()

    def delete_style(style_data):
        if style_data in styles_list:
            styles_list.remove(style_data)
            save_styles(styles_list)
            update_style_tabs()

    add_style_button.on_click(add_style)

    target_article_input = TextAreaInput(
        title="输入需要风格转换的文章",
        placeholder="在这里输入需要转换的文章...",
        value="",
        rows=20,
        width=700,
    )

    style_select_div = Div(text="<p>选择要使用的风格（在左侧切换tab）</p>", width=700)

    analyze_button = Button(
        label="分析并重写", button_type="primary", width=680, height=50
    )

    result_div = Div(text="", width=700)

    def analyze_and_rewrite():
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
        articles = active_style.get("articles", [])
        if not articles:
            result_div.text = "<p style='color: red;'>当前风格下没有参考文章</p>"
            return

        try:
            style_tabs[active_tab_idx].update_data()
            save_styles(styles_list)

            reference_articles = [a["content"] for a in articles]
            style_name = active_style.get("name", "未命名风格")
            style_description = active_style.get("description", "")
            result = analyze_article_with_style(
                target_article,
                reference_articles,
                style_name,
                style_description,
                provider,
                model,
            )
            result_div.text = f"""
            <h3>使用 "{style_name}" 风格重写结果:</h3>
            <div style="border: 1px solid #4CAF50; padding: 15px; margin: 10px 0; background-color: #f9f9f9;">
                <p>{result.replace(chr(10), "<br>")}</p>
            </div>
            """
        except Exception as e:
            result_div.text = f"<p style='color: red;'>分析出错: {str(e)}</p>"

    analyze_button.on_click(analyze_and_rewrite)

    initial_tabs = create_style_tabs()
    tabs_widget = initial_tabs

    left_column = column(
        Div(text="<h2>风格管理</h2>", width=700),
        add_style_button,
        initial_tabs,
    )

    right_column = column(
        Div(text="<h2>风格转换</h2>", width=700),
        style_select_div,
        target_article_input,
        analyze_button,
        result_div,
    )

    layout = column(
        Div(text="<h1>文章风格分析与重写工具</h1>", width=1400),
        row(left_column, right_column),
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
    server = Server(apps, port=port)

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
