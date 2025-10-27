import time
import os
import re
import glob
import argparse
import datetime as dttm


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
        # link = item["link"]
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
                r"转述师：金北平.*?\n",
                r"创建时间.*?\n",
                r"更新时间.*?\n",
                r"URL.*?\n",
            ]:
                txt = re.sub(t, r"", txt)
                pass

            txt = re.sub(r"(.*?)\n{2}", r"\1", txt)
            txt = re.sub(r" +", r"", txt)

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


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--uid", help="uid", type=int, default=1)
    args = parser.parse_args()

    uid = args.uid
    filter = ""
    name = "熊逸讲透资治通鉴"
    article_path = f".torextrader/toutiao/article_{uid}_{name}"

    export = True
    if export:
        article_items = get_articles_items(article_path)
        print(f"generate combined articles from {len(article_items)} articles...")

        def sork_item(x):
            f = re.search(r"(\d+)\s*", x)
            t = f.group()
            n = int(t)
            return n

        sorted_article_items = sorted(article_items, key=lambda x: sork_item(x["link"]))

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
