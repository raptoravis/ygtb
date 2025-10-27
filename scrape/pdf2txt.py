import argparse
import os
import re
import time
import glob
import datetime as dttm
import pandas as pd
import commentjson
import orjson
from pathlib import Path


import pdftotext
from pypdf import PdfReader
import pypdfium2


def load_json(filename: str) -> dict:
    """
    Load data from json file in temp path.
    """
    filepath: Path = Path(filename)
    use_comments = True

    data = {}

    if filepath.exists():
        with open(filepath, mode="r", encoding="UTF-8") as f:
            if use_comments:
                data: dict = commentjson.load(f)
            else:
                c = f.read()
                if len(c) > 0:
                    data: dict = orjson.loads(c)
                else:
                    data = {}
        return data
    else:
        # save_json(filename, {})
        return data


def get_articles_items(article_path):
    article_items = []

    for path in Path(article_path).rglob("*.pdf"):
        file_name = str(path)
        print(file_name)

        if os.path.isfile(file_name):
            file_base_name = path.stem
            # Load your PDF
            with open(file_name, "rb") as fp:
                txt = ""

                # # If it's password-protected
                # # pdf = pdftotext.PDF(f, "secret")
                pdf = pdftotext.PDF(fp)
                for page in pdf:
                    txt += f"{str(page)}\n\n"

                # pdf = pypdfium2.PdfDocument(file_name)

                # # # Iterate over all the pages
                # for page in pdf:
                #     # Load a text page helper
                #     textpage = page.get_textpage()

                #     # Extract text from the whole page
                #     text_all = textpage.get_text_range()

                #     txt += f"{str(text_all)}\n\n"

                # Read all the text into one string
                # txt = "\n\n".join(pdf)

                # print(txt)

                # reader = PdfReader(file_name)
                # for page in reader.pages:
                #     txt += page.extract_text() + "\n"

                title = file_base_name
                dt = os.path.getmtime(file_name)

                article_item = {
                    "link": file_base_name,
                    "title": title,
                    "date": dt,
                    "txt": txt,
                }
                article_items.append(article_item)

    return article_items


def generate_txts(
    article_items,
    articles_path,
    filter,
    name,
):
    group_num = 1000

    group_idx = []
    group_txts = []
    txts = ""

    for idx, item in enumerate(article_items):
        # link = item["link"]
        # title = item["title"]

        txt = item["txt"]

        if txt is not None:
            idx_t = idx + 1

            txt = re.sub(
                r"【原文】(.*?\n)*?(【\s*译文\s*】|【\s*原文华译\s*】|【\s*闲扯\s*】|【\s*解析\s*】|【\s*读解\s*】|【\s*华译\s*】)",
                r"【原文】\n 略\n\2",
                txt,
            )

            # txt = re.sub(
            #     r"【原文】((.*)\n)*?【注释】((.*)\n)*?【译文】",
            #     r"【原文】\n 略\n【译文】",
            #     txt,
            # )

            txt = re.sub(
                r"蔡根谈解读资治通鉴三个特点：1､尽量白话文（译文主要摘抄自《华杉讲透资治通鉴》一书；2､借古说今，会更多在营销管理领域进行解读；3､只摘比较典型的片段，不做长篇连载。",
                r"",
                txt,
            )

            txt = re.sub(
                r"点赞关注不迷路，可关注微信公众号:通鉴风云，防止失联，后期更多精彩文章(。)*",
                r"",
                txt,
            )

            txt = re.sub(
                r"读资治通鉴，悟人生哲理。笔者自17年研究资治通鉴迄今已是六年四遍，将300万字神书浓缩为18万字读书笔记，皆是智慧经验，学习前人经验少走弯路回头路，感叹古今多少事都付笑谈中。感谢大家关注支持！",
                r"",
                txt,
            )

            txt = re.sub(
                r"编者按：.*?\n",
                r"",
                txt,
            )

            txt = re.sub(
                r"#.*?#",
                r"",
                txt,
            )

            txt = re.sub(
                r"关注我，带你成为学霸，走向人生巅峰！",
                r"",
                txt,
            )

            txt = re.sub(
                r"作者简介：.*?\n",
                r"",
                txt,
            )

            txt = re.sub(
                r"读资治通鉴，悟人生哲理.*?\n",
                r"",
                txt,
            )

            txts += f"第{idx_t:04}章\n\n{txt}\n"

            if idx_t % group_num == 0:
                group_idx.append(idx_t)
                group_txts.append(txts)
                txts = ""

        pass

    if txts:
        group_idx.append(len(article_items))
        group_txts.append(txts)

    last_idx = 1
    for i, txts in enumerate(group_txts):
        idx = group_idx[i]

        # fn = f"{articles_path}/{last_idx:04}_{idx:04}_{name}"
        # fn = f"{articles_path}/{last_idx:04}_{name}"
        if last_idx > 1:
            fn = f"{articles_path}/{last_idx:04}_{name}"
        else:
            fn = f"{articles_path}/{name}"

        if filter:
            fn = f"{fn}_{filter}.txt"
        else:
            fn = f"{fn}.txt"
            pass

        with open(
            fn,
            "w",
            encoding="utf-8",
        ) as fp:
            fp.write(txts)
            last_idx = idx
            print(f"{fn} generated")

    pass


def handle_item(item, force, nocache, max_articles):
    link = item["link"]
    name = item["name"]
    filter = item["filter"]

    print(f"{link}")
    print(f"{name} {filter}")

    articles_path = ".torextrader/pdf2txt/"
    paths = [articles_path]

    for path in paths:
        if not os.path.exists(path):
            os.makedirs(path)

    article_items = get_articles_items(link)
    generate_txts(
        article_items,
        articles_path,
        filter=filter,
        name=name,
    )


max_articles_default = 800


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-f", "--force", help="force to check all the articles", action="store_true"
    )

    parser.add_argument(
        "-n", "--nocache", help="refresh all articles", action="store_true"
    )
    parser.add_argument("-x", "--index", help="index", type=int, default=None)
    parser.add_argument(
        "-c",
        "--config",
        default=".torextrader/pdftotxt.json",
        type=str,
        help="config file",
    )

    args = parser.parse_args()

    if args.config and args.config != "none":
        config: dict = load_json(args.config)
        items = config["items"]

        if args.index is not None:
            idx = args.index

            if idx >= len(items) or idx < 0:
                print(f"invalid index: {idx}")
                return

            item = items[idx]
            max_articles = item.get("max", max_articles_default)
            handle_item(item, args.force, args.nocache, max_articles)
        else:
            for item in items:
                max_articles = item.get("max", max_articles_default)
                handle_item(item, args.force, args.nocache, max_articles)
                pass
    else:
        print("no config specified")
        return

    pass


main()
