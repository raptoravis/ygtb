import time
import os
import re
import glob
import argparse
import datetime as dttm
from termcolor import colored
import torch

if torch.cuda.is_available():
    cuda_available = True
    print(
        colored(
            f"CUDA is available. Using GPU: {torch.cuda.get_device_name(0)}",
            "green",
        )
    )
else:
    cuda_available = False
    print(
        colored(
            "CUDA is not available. Using CPU.",
            "red",
        )
    )


def get_mp3_items(mp3_path):
    wild_dir: str = os.path.join(mp3_path, "**")

    mp3_items = []
    for file_name in glob.iglob(wild_dir, recursive=False):
        if os.path.isfile(file_name):
            file_base_name, ext = os.path.splitext(os.path.basename(file_name))
            dt = os.path.getmtime(file_name)

            article_item = {
                "link": file_base_name,
                "path": file_name,
                "date": dt,
            }
            mp3_items.append(article_item)

    return mp3_items


def get_articles_items(article_path):
    wild_dir: str = os.path.join(article_path, "**")

    article_items = []
    for file_name in glob.iglob(wild_dir, recursive=False):
        if os.path.isfile(file_name):
            file_base_name, ext = os.path.splitext(os.path.basename(file_name))
            with open(file_name, "r", encoding="utf-8") as fp:
                txt = fp.read()
                pos_nl = txt.find("\n")
                if pos_nl > 0:
                    title = txt[:pos_nl]
                else:
                    title = ""

                invalid_txt = re.search(r"手机登录\n扫码登录\n获取验证码\n", txt)
                if invalid_txt:
                    continue

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
        link = item["link"]
        # title = item["title"]

        txt = item["txt"]

        if txt is not None:
            idx_t = idx + 1

            # txt = re.sub(
            #     r"【原文】(.*?\n)*?(【\s*译文\s*】|【\s*原文华译\s*】|【\s*闲扯\s*】|【\s*解析\s*】|【\s*读解\s*】|【\s*华译\s*】)",
            #     r"【原文】\n 略\n\2",
            #     txt,
            # )

            for t in [
                r"创建时间.*?\n",
                r"更新时间.*?\n",
                r"请在预览后及时删除.*?\n",
            ]:
                txt = re.sub(t, r"", txt)
                pass

            txt = re.sub(
                r",",
                r"，",
                txt,
            )

            txt = re.sub(r"(.*?)\n{2}", r"\1", txt)
            txt = re.sub(r" +", r"", txt)

            txts += f"第{idx_t:04}章\n\n{link}\n{txt}\n"

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


# https://www.youtube.com/watch?v=UFdS1tqSpIA
# pip uninstall -y torch torchvision torchaudio
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
# choco install ffmepg
# pip install openai-whisper


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--uid", help="uid", type=int, default=1)
    parser.add_argument("-s", "--scrape", help="scrape the app", action="store_true")
    parser.add_argument(
        "-e", "--export", help="export the articles", action="store_true"
    )
    args = parser.parse_args()

    uid = args.uid
    filter = ""
    name = "熊逸讲透资治通鉴"
    mp3_path = f".torextrader/toutiao/mp3_{uid}_{name}"

    article_path = f".torextrader/toutiao/txt_{uid}_{name}"

    paths = [article_path]
    for path in paths:
        if not os.path.exists(path):
            os.makedirs(path)

    scrape = args.scrape
    if scrape:
        mp3_items = get_mp3_items(mp3_path)

        device = "cuda" if cuda_available else "cpu"
        opts = f"--model medium --language Chinese --output_format txt --device {device} --output_dir {article_path}"

        articles = {}
        article_items_t = get_articles_items(article_path)
        for ai in article_items_t:
            link = ai["link"]
            articles[link] = ai

        total_items = len(mp3_items)
        init_time = time.perf_counter()
        for idx, mp3_item in enumerate(mp3_items):
            link = mp3_item["link"]
            exist_article = articles.get(link, None)
            if exist_article is not None:
                continue

            start_time = time.perf_counter()

            mp3_path = mp3_item["path"]
            cmd_line = f"whisper {mp3_path} {opts}"
            print(
                colored(
                    f"******{idx:003}/{total_items:003} {mp3_path}******",
                    "cyan",
                )
            )
            os.system(cmd_line)

            end_time = time.perf_counter()
            cost = float(end_time - start_time) / 60.0
            cost_total = float(end_time - init_time) / 60.0
            print(
                colored(
                    f"******{idx:003}/{total_items:003} TIME ELPASED: {cost:.2f}m/{cost_total:.2f}m******",
                    "cyan",
                )
            )
            pass

    export = args.export
    if export:
        article_items = get_articles_items(article_path)
        print(f"generate combined articles from {len(article_items)} articles...")

        def sork_item(x):
            f = re.search(r"xy(\d+)(_(\d))*", x)
            ts = f.groups()
            t = ts[0]
            n = int(t) * 10
            if ts[2]:
                n += int(ts[2])
            return n

        sorted_article_items = sorted(article_items, key=lambda x: sork_item(x["link"]))

        # sorted_article_items = sorted(article_items, key=lambda x: x["link"])

        name = f"{name}_{uid:02}"

        articles_path = ".torextrader/toutiao"
        generate_txts(
            sorted_article_items,
            articles_path,
            filter=filter,
            name=name,
        )
    pass


main()
