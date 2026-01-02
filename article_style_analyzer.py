import argparse
import json
import os
from datetime import datetime

from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.document import Document
from bokeh.layouts import column, row
from bokeh.models import Button, Div, TextAreaInput
from bokeh.server.server import Server
from crewai import Agent, Crew, Process, Task
from termcolor import colored

from utils import get_llm, glog_info

ARTICLES_FILE = "data/articles.json"


def load_articles():
    if os.path.exists(ARTICLES_FILE):
        with open(ARTICLES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_articles(articles):
    os.makedirs(os.path.dirname(ARTICLES_FILE), exist_ok=True)
    with open(ARTICLES_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)


def analyze_article_with_style(article_text, reference_articles, provider, model):
    llm = get_llm(provider=provider, model=model)
    analyzer = Agent(
        role="文章风格分析师",
        goal="分析参考文章的风格并用这种风格重写目标文章",
        backstory="你是一个专业的写作风格分析专家，能够准确捕捉文章的写作风格、语气、用词习惯和结构特点。",
        llm=llm,
        verbose=True,
    )

    reference_text = "\n\n".join([f"参考文章{i + 1}:\n{ref}" for i, ref in enumerate(reference_articles)])

    task = Task(
        description=f"""参考以下文章的风格特点，用相同的风格重写目标文章。

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


def make_document(doc: Document, provider, model):
    articles = load_articles()

    article_input = TextAreaInput(
        title="输入文章内容",
        placeholder="在这里输入文章内容...",
        value="",
        rows=10,
        width=800,
    )

    add_button = Button(label="添加文章", button_type="success", width=150, height=50)

    articles_div = Div(text="", width=800)

    target_article_input = TextAreaInput(
        title="输入需要风格转换的文章",
        placeholder="在这里输入需要转换的文章...",
        value="",
        rows=10,
        width=800,
    )

    analyze_button = Button(label="分析并重写", button_type="primary", width=150, height=50)

    result_div = Div(text="", width=800)

    def update_articles_display():
        if not articles:
            articles_div.text = "<p>暂无已保存的文章</p>"
        else:
            html = "<h3>已保存的文章:</h3>"
            for i, article in enumerate(articles):
                html += f"""
                <div style="border: 1px solid #ccc; padding: 10px; margin: 10px 0;">
                    <p><strong>文章 {i + 1}</strong> (添加时间: {article.get("time", "N/A")})</p>
                    <p>{article["content"][:200]}...</p>
                    <button onclick="delete_article({i})">删除</button>
                </div>
                """
            articles_div.text = html

    def add_article():
        content = article_input.value.strip()
        if content:
            articles.append(
                {
                    "content": content,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            save_articles(articles)
            article_input.value = ""
            update_articles_display()

    def analyze_and_rewrite():
        target_article = target_article_input.value.strip()
        if not target_article:
            result_div.text = "<p style='color: red;'>请输入需要转换的文章</p>"
            return

        if not articles:
            result_div.text = "<p style='color: red;'>请先添加参考文章</p>"
            return

        try:
            reference_articles = [a["content"] for a in articles]
            result = analyze_article_with_style(target_article, reference_articles, provider, model)
            result_div.text = f"""
            <h3>重写结果:</h3>
            <div style="border: 1px solid #4CAF50; padding: 15px; margin: 10px 0; background-color: #f9f9f9;">
                <p>{result}</p>
            </div>
            """
        except Exception as e:
            result_div.text = f"<p style='color: red;'>分析出错: {str(e)}</p>"

    add_button.on_click(add_article)
    analyze_button.on_click(analyze_and_rewrite)

    update_articles_display()

    layout = column(
        Div(text="<h2>文章风格分析与重写工具</h2>", width=800),
        article_input,
        row(add_button),
        articles_div,
        Div(text="<hr>", width=800),
        Div(text="<h2>风格转换</h2>", width=800),
        target_article_input,
        row(analyze_button),
        result_div,
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
