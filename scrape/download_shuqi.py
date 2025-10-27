import argparse
import os
import re
import time
import glob
import datetime as dttm
from bs4 import BeautifulSoup

# import pandas as pd
# import requests
# import html2text
import commentjson
import orjson
from pathlib import Path
from termcolor import colored
from selenium import webdriver


from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver

from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.webdriver import WebDriver as EdgeWebDriver

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

group_num: int = 2000


def create_drive(use_edge_web_driver: bool):
    # proxy = ""

    if use_edge_web_driver:
        options = EdgeOptions()
    else:
        options = ChromeOptions()

    options.add_argument("--no-sandbox")

    options.add_argument("log-level=3")

    # options.add_argument("--headless")

    options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--disable-infobars")
    # options.add_argument("--disable-extensions")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--remote-debugging-port=9222")

    home_dir = Path.home()

    # if use_edge_web_driver:
    #     # "user-data-dir=C:\\Users\\rapto\\AppData\\Local\\Microsoft\\Edge\\User Data"
    #     user_data_dir = os.path.join(
    #         home_dir, "AppData\\Local\\Microsoft\\Edge\\User Data"
    #     )
    # else:
    #     # "user-data-dir=C:\\Users\\rapto\\AppData\\Local\\Google\\Chrome\\User Data"
    #     user_data_dir = os.path.join(
    #         home_dir, "AppData\\Local\\Google\\Chrome\\User Data"
    #     )
    user_data_dir = os.path.join(home_dir, "AppData\\Local\\Google\\Chrome\\User Data")

    data_dir_arg = f"user-data-dir={user_data_dir}"
    print(data_dir_arg)

    options.add_argument(data_dir_arg)
    options.add_experimental_option("detach", True)  # prevent window from closing

    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    # https://sites.google.com/chromium.org/driver
    # https://googlechromelabs.github.io/chrome-for-testing/

    # driver = webdriver.Chrome(options=options)
    if use_edge_web_driver:
        driver_name = "msedgedriver.exe"
        service = EdgeService(executable_path=driver_name)
        driver = EdgeWebDriver(service=service, options=options)

    else:
        driver_name = "chromedriver.exe"
        service = ChromeService(executable_path=driver_name)
        driver = ChromeWebDriver(service=service, options=options)

    # driver.add_cookie(
    #     {
    #         "name": "passport_csrf_token",
    #         "value": "17d30b65f519f3f58bc6d96f34fb8e0e",
    #     }
    # )

    return driver


driver = None

valid_size = 250
# # "text/html; charset=utf-8"

# h = html2text.HTML2Text()
# # Ignore converting links from HTML
# h.ignore_links = True


# output_doc = BeautifulSoup()
# output_doc.append(output_doc.new_tag("html"))
# output_doc.html.append(output_doc.new_tag("body"))
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


def scroll_till_end():
    SCROLL_PAUSE_TIME = 1.0

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def get_html_from_file(fp):
    with open(fp, "r", encoding="utf-8") as f:
        html = f.read()

    return html


def get_articles_data_wp(html, flter):
    data = []

    soup = BeautifulSoup(html, "html.parser")
    # print(soup.title.text)

    uls = soup.find_all("ul", class_="album__list js_album_list")
    if not uls:
        return data

    ul = uls[0]
    articles = ul.find_all(
        "li", class_="album__list-item js_album_item js_wx_tap_highlight wx_tap_cell"
    )
    for article in articles:
        item = {}

        link_ = article.attrs["data-link"]
        title = article.attrs["data-title"]

        pos = link_.find("&chksm=")
        link = link_[:pos]

        valid = check_if_filtered(flter, title)
        if valid:
            item = {
                "link": link,
                # "title": title,
                "title": "",
            }
            data.append(item)
        pass
    pass

    # df = pd.DataFrame(data)

    # df.to_csv(f"{path}/articles.csv")

    return data


def get_articles_data_tt(html, flter, is_article: bool):
    data = []

    try:
        soup = BeautifulSoup(html, "html.parser")
        # print(soup.title.text)

        cls = (
            "profile-article-card-wrapper" if is_article else "profile-wtt-card-wrapper"
        )

        articles = soup.find_all("div", class_=cls)
        for article in articles:
            item = {}

            if is_article:
                link_el = article.find("a", class_="title")
                link = link_el.attrs["href"]
                title = link_el.text
            else:
                links = article.findAll("a", {"target": "_blank"})
                link_el = None
                for i in range(1, len(links)):
                    link = links[i]
                    if not link.has_attr("title"):
                        link_el = link
                        break

                link = link_el.attrs["href"]
                # title = link_el.text
                # title = ""
                title = link_el.contents[0]

            if isinstance(title, str):
                valid = check_if_filtered(flter, title)
                if valid:
                    item = {
                        "link": link,
                        "title": title,
                    }
                    data.append(item)
            pass
    except Exception as ex:
        print(ex)

    # df = pd.DataFrame(data)

    # df.to_csv(f"{path}/articles.csv")

    return data


def get_articles_data_shuqi(html, flter, is_article: bool):
    data = []

    try:
        soup = BeautifulSoup(html, "html.parser")
        # print(soup.title.text)

        cls = "ellipsis line level-0"

        articles = soup.find_all("li", class_=cls)
        for article in articles:
            item = {}

            title = article.text
            idx = article.attrs["data-index"]

            item = {
                "title": title,
                "idx": int(idx),
            }

            data.append(item)
        pass
    except Exception as ex:
        print(ex)

    return data


def check_if_filtered(flter, title):
    valid = False
    if title and isinstance(title, str):
        if not flter:
            valid = True
        else:
            if isinstance(flter, list):
                for f in flter:
                    v = title.find(f) >= 0
                    if v:
                        valid = True
                        break
                    pass
                pass
            else:
                valid = title.find(flter) >= 0
    else:
        pass
    return valid


toutiao_www_link = "https://www.toutiao.com"
article_prefix = "/article/"
tt_article_link = "https://www.toutiao.com/article/"
w_link = "https://www.toutiao.com/w/"

wp_prefix = "http://mp.weixin.qq.com/s?__biz="


def get_update_items(
    article_path,
    flter,
    html,
    origin,
    is_article: bool,
    cache: bool = True,
):
    if origin == "tt":
        articles_data = get_articles_data_tt(html, flter=flter, is_article=is_article)
    elif origin == "wp":
        articles_data = get_articles_data_wp(html, flter=flter)
    elif origin == "shuqi":
        articles_data = get_articles_data_shuqi(
            html, flter=flter, is_article=is_article
        )
    else:
        assert False, ""

    # reversed_articles_data = list(reversed(articles_data))
    reversed_articles_data = articles_data

    update_items = []
    for item in reversed_articles_data:
        # title = item["title"]
        idx = item["idx"]

        updated = False
        article_fp = f"{article_path}/{idx}.txt"
        if os.path.exists(article_fp):
            if cache:
                pass
            else:
                fs = os.path.getsize(article_fp)
                if fs < valid_size:
                    updated = True
            pass
        else:
            updated = True
            pass

        if updated:
            update_items.append(item)
            # title = item["title"]
            # print(f"UPDATE: {title}, {link}")
            pass

    return reversed_articles_data, update_items


def get_all_update_items(
    origin,
    link,
    article_path,
    flter,
    cache,
    max_articles,
    is_article: bool,
    sort_reversed=False,
    max_checks: int = 0,
):
    # r = requests.get(link, proxies=proxy)
    # # r.encoding = "utf-8"
    # html = r.text
    driver.get(link)
    driver.implicitly_wait(2.0)
    time.sleep(2.0)

    SCROLL_PAUSE_TIME = 1.0

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    last_all_items = []
    last_update_items = []
    last_checks = 0
    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        html = driver.page_source
        all_items, update_items = get_update_items(
            article_path,
            flter,
            html,
            origin,
            is_article=is_article,
            cache=cache,
        )

        if max_articles > 0 and len(all_items) > max_articles:
            print(f"stop here, {max_articles} reached")
            break

        updated_items = len(update_items)
        if max_checks > 0 and updated_items > max_checks:
            print(f"stop checkingg here, {max_checks} reached")
            break

        if not cache and updated_items > last_checks:
            print(f"{updated_items} updated items")
            pass

        if cache:
            if len(all_items) > len(last_all_items):
                if len(update_items) > len(last_update_items):
                    pass
                else:
                    # no update
                    break
            else:
                pass

            last_all_items = all_items
            last_update_items = update_items
        else:
            pass

        last_checks = updated_items

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        pass

    # input("press enter to continue\n")
    html = driver.page_source
    all_items, update_items = get_update_items(
        article_path,
        flter,
        html,
        origin,
        is_article=is_article,
        cache=cache,
    )

    updated_items = len(update_items)
    print(f"{updated_items} updated items")

    return update_items


def download_link(
    link,
    title,
    link_id,
    article_fp,
    include_title: bool,
    is_article: bool,
    cache: bool = True,
):
    if not cache:
        if os.path.exists(article_fp):
            fs = os.path.getsize(article_fp)
            if fs > valid_size:
                print(
                    colored(
                        f"cached {link}, filesize {fs}, do nothing",
                        "green",
                    )
                )
                return

            print(
                colored(
                    f"not cached {link},  filesize {fs}, to redownload...",
                    "red",
                )
            )
            pass
        pass

    driver.get(link)

    time.sleep(1.0)
    # driver.implicitly_wait(0.1)

    txt = ""
    meta = ""
    try:

        WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        f = driver.find_element(
            By.XPATH, value='//*[@id="app"]/div[1]/div[3]/div[1]/iframe'
        )
        m = f.find_element(By.XPATH, value="/html/body")
        # meta = m.text
        meta = ""
    except Exception as ex:
        print(link, title, ex)

    content = None

    try:
        content = m.text
    except Exception as ex:
        print(link, title, ex)
        pass

    if content is None:
        try:
            m = driver.find_element(By.CLASS_NAME, value="weitoutiao-html")
            if m is not None:
                content = m.text
        except Exception:
            pass

    if content is None:
        try:
            m = driver.find_element(By.CLASS_NAME, value="article-content")
            if m is not None:
                content = m.text
        except Exception:
            pass

    if content is None:
        print("invalid text:", link, title)
        return ""

    try:
        # path = "E:\\downloads\\w.png"
        # with open(path, "wb") as fp:
        #     fp.write(m.screenshot_as_png)

        # txt = re.sub(r"((\d)+)(\s)*，", r"\1 ", content)
        # txt = re.sub(r"\n+", r"\n", txt)
        if include_title:
            txt = f"{title}\n\n\n{meta}\n{content}\n\n\n"
        else:
            txt = f"{meta}\n{content}\n\n\n"

        updated = True
        if os.path.exists(article_fp):
            txt_exist = get_html_from_file(article_fp)
            if len(txt) > len(txt_exist):
                updated = True
            else:
                updated = False

        if updated:
            with open(article_fp, "w", encoding="utf-8") as fp:
                # fp.write(r.text)
                fp.write(txt)
                pass

            fs = os.path.getsize(article_fp)
            color = "green" if fs > valid_size else "red"
            print(
                colored(
                    f"downloaded {link} size {fs} {title}",
                    color,
                )
            )
            pass
        else:
            print(f"same size, {link} {title}")
            pass

        pass

    except Exception as ex:
        print(link, title, ex)

    return txt


def download_links(
    all_update_items,
    article_path,
    include_title: bool,
    is_article: bool,
    cache: bool = True,
):
    for idx, item in enumerate(all_update_items):
        idx = item["idx"]
        title = item["title"]
        dt = item.get("date", "")

        link_num = 1167088 + idx
        link = f"https://t.shuqi.com/reader/7968647?spm=a2o2cg.query.0.0&forceChapterIndex=1&forceChapterId={link_num}"

        prefix_len = len(tt_article_link) if is_article else len(w_link)
        link_id = link[prefix_len:-1]
        article_fp = f"{article_path}/{link_id}.txt"

        print(f">>>downloading {idx:04} {dt} {title} {link_id}...")
        download_link(
            link,
            title,
            link_id,
            article_fp,
            include_title=include_title,
            is_article=is_article,
            cache=cache,
        )

        pass
    pass


def generate_txts(
    article_items,
    filter_original_text: bool = True,
    start_idx: int = 0,
):
    group_idx = []
    group_txts = []
    txts = ""

    for idx, item in enumerate(article_items):
        # link = item["link"]
        # title = item["title"]

        txt = item["txt"]

        # if txt.find("张教主的韭阳神功") > -1:
        #     pass

        if txt is not None:
            local_idx_t = idx + 1
            idx_t = local_idx_t + start_idx

            if filter_original_text:
                txt = re.sub(
                    r"【原文】(.*?\n)*?(【\s*译文\s*】|【\s*原文华译\s*】|【\s*闲扯\s*】|【\s*解析\s*】|【\s*读解\s*】|【\s*华译\s*】)",
                    r"【原文】\n 略\n\2",
                    txt,
                )

            txt = re.sub(
                r"立志花15年讲完《资治通鉴》(.*\n)*谋略那些事.*\n",
                r"",
                txt,
            )
            if len(txt) > 0:
                valid_texts = re.search(r"\S", txt)
                if valid_texts:
                    txts += f"第{idx_t:04}章\n\n{txt}\n"

                    if idx_t % group_num == 0:
                        group_idx.append(local_idx_t)
                        group_txts.append(txts)
                        txts = ""
                pass

        pass

    if txts:
        group_idx.append(len(article_items) + start_idx)
        group_txts.append(txts)

    return group_idx, group_txts


def write_txts(articles_path, name, group_idx, group_txts):
    last_idx = 1
    for i, txts in enumerate(group_txts):
        idx = group_idx[i]

        # fn = f"{articles_path}/{last_idx:04}_{idx:04}_{name}"
        # fn = f"{articles_path}/{last_idx:04}_{name}"
        if last_idx > 1 or len(group_txts) > 1:
            fn = f"{articles_path}/{last_idx:04}_{name}"
        else:
            fn = f"{articles_path}/{name}"

        fn = f"{fn}.txt"

        with open(
            fn,
            "w",
            encoding="utf-8",
        ) as fp:
            fp.write(txts)
            c = idx - last_idx + (1 if last_idx == 1 else 0)
            last_idx = idx
            print(colored(f"{fn} generated from {c} txts", "green"))
        pass
    pass


def get_articles_items(article_path):
    wild_dir: str = os.path.join(article_path, "**")

    article_items = []
    for file_name in glob.iglob(wild_dir, recursive=False):
        if os.path.isfile(file_name):
            file_base_name, ext = os.path.splitext(os.path.basename(file_name))
            with open(file_name, "r", encoding="utf-8") as fp:
                txt = fp.read()

                txt = re.sub(r"\n{5,}", r"", txt)

                if len(txt) == 0:
                    continue

                pos_nl = txt.find("\n")
                if pos_nl > 0:
                    title = txt[:pos_nl]
                else:
                    title = ""

                invalid_txt = re.search(r"手机登录\n扫码登录\n获取验证码\n", txt)
                if invalid_txt:
                    continue

                dts = re.search(r"(\d+-\d+-\d+ \d+:\d+)", txt)
                if dts:
                    dt = dttm.datetime.strptime(dts.group(), "%Y-%m-%d %H:%M")
                else:
                    # dt = os.path.getmtime(file_name)
                    dt = dttm.datetime.now()
                    # continue
                    pass

                article_item = {
                    "link": file_base_name,
                    "title": title,
                    "date": dt,
                    "txt": txt,
                }
                article_items.append(article_item)

    return article_items


def main():
    parser = argparse.ArgumentParser()

    # parser.add_argument("-x", "--index", help="index", type=int, default=None)
    # parser.add_argument("-m", "--checks", help="max checks", type=int, default=None)
    # parser.add_argument("-a", "--max", help="max items", type=int, default=None)
    # parser.add_argument(
    #     "-n", "--nocache", help="refresh all articles", action="store_true"
    # )
    # parser.add_argument(
    #     "-f", "--force", help="force to check all the articles", action="store_true"
    # )

    # parser.add_argument("-s", "--scrape", help="scrape", action="store_true")
    # # parser.add_argument("-e", "--edge", help="use edge", action="store_true")
    parser.add_argument("-r", "--chrome", help="use chrome", action="store_true")

    # parser.add_argument(
    #     "-c",
    #     "--config",
    #     default=".torextrader/scrape_toutiao_config.json",
    #     type=str,
    #     help="config file",
    # )

    args = parser.parse_args()

    # use_edge_web_driver = args.edge
    use_edge_web_driver = not args.chrome

    global driver
    driver = create_drive(use_edge_web_driver)

    nocache = False
    is_article = True
    include_title = True
    article_path = ".torextrader/toutiao/article_7968647"
    link = "https://t.shuqi.com/catalog/7968647/?spm=a2o2cg.query.0.0"
    origin = "shuqi"
    all_update_items = get_all_update_items(
        origin=origin,
        link=link,
        article_path=article_path,
        flter="",
        cache=not nocache,
        max_articles=1000,
        is_article=is_article,
        sort_reversed=True,
        max_checks=1000,
    )

    if all_update_items:
        print(f"downloading {len(all_update_items)} updated articles...")

        # the order the sooner so as to make the older link has an older file
        reversed_all_update_items = list(reversed(all_update_items))
        download_links(
            reversed_all_update_items,
            article_path,
            include_title=include_title,
            is_article=is_article,
            cache=not nocache,
        )

    articles_path = ".torextrader/toutiao"
    filter_original_text = ""
    start_idx = 1

    article_items = get_articles_items(article_path)
    sorted_article_items = sorted(article_items, key=lambda x: x["date"])

    group_idx_t, group_txts_t = generate_txts(
        sorted_article_items,
        filter_original_text=filter_original_text,
        start_idx=start_idx,
    )

    name = ""
    grp_idxs = []
    grp_txts = []

    write_txts(articles_path, name, grp_idxs, grp_txts)

    driver.quit()

    pass


main()
