import argparse
import datetime as dttm
import glob
import os
import re
import time
from pathlib import Path

# import pandas as pd
# import requests
# import html2text
import commentjson
import orjson
from bs4 import BeautifulSoup
from selenium import webdriver

# from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions

# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from termcolor import colored

# # from webdriver_manager.chrome import ChromeDriverManager

# # # _driver = webdriver.Chrome(ChromeDriverManager().install())
# # ChromeDriverManager().install()
# _driver = webdriver.Chrome()
# # _driver.get("https://www.google.com")
# # print(_driver.capabilities)  # 正常访问属性
# _driver.quit()

# # from webdriver_manager.microsoft import EdgeChromiumDriverManager

# # # _driver = webdriver.Chrome(ChromeDriverManager().install())
# # EdgeChromiumDriverManager().install()
# _driver = webdriver.Edge()
# # _driver.get("https://www.google.com")
# # print(_driver.capabilities)  # 正常访问属性
# _driver.quit()


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
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    home_dir = Path.home()

    if use_edge_web_driver:
        # "user-data-dir=C:\\Users\\rapto\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default"
        user_data_dir = os.path.join(
            home_dir, "AppData\\Local\\Microsoft\\Edge\\User Data\\Default"
        )

        # use chromes' user data
        # user_data_dir = os.path.join(
        #     home_dir, "AppData\\Local\\Google\\Chrome\\User Data"
        # )
    else:
        # "user-data-dir=C:\\Users\\rapto\\AppData\\Local\\Google\\Chrome\\User Data"
        user_data_dir = os.path.join(
            home_dir, "AppData\\Local\\Google\\Chrome\\User Data"
        )
    # user_data_dir = os.path.join(home_dir, "AppData\\Local\\Google\\Chrome\\User Data")

    data_dir_arg = f"user-data-dir={user_data_dir}"
    print(data_dir_arg)

    options.add_argument(data_dir_arg)
    options.add_experimental_option("detach", True)  # prevent window from closing

    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    # https://sites.google.com/chromium.org/driver
    # https://googlechromelabs.github.io/chrome-for-testing/

    # https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/?form=MA13LH#downloads

    if use_edge_web_driver:
        # driver_name = "msedgedriver.exe"
        # service = EdgeService(executable_path=driver_name)
        # driver = EdgeWebDriver(service=service, options=options)
        driver = webdriver.Chrome(options=options)

    else:
        # driver_name = "chromedriver.exe"
        # service = ChromeService(executable_path=driver_name)
        # driver = ChromeWebDriver(service=service, options=options)
        driver = webdriver.Edge(options=options)

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
    else:
        assert False, ""

    # reversed_articles_data = list(reversed(articles_data))
    reversed_articles_data = articles_data

    update_items = []
    for item in reversed_articles_data:
        link = item["link"]

        link_num = None
        if origin == "tt":
            pos = link.find(tt_article_link)
            if pos >= 0:
                prefix_len = len(tt_article_link) if is_article else len(w_link)
                link_num = link[prefix_len:-1]
            else:
                pos = link.find(article_prefix)
                link_split = link.split("/")
                link_num = link_split[-1]
                if not link_num:
                    link_num = link_split[-2]
                    item["link"] = f"{toutiao_www_link}{link}"
        elif origin == "wp":
            pos = link.find(wp_prefix)
            if pos >= 0:
                link_num = link[len(wp_prefix) : -1]
        else:
            assert False, ""

        updated = False
        article_fp = f"{article_path}/{link_num}.txt"
        if os.path.exists(article_fp):
            if not cache:
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

    if sort_reversed:
        cls = "album-sort__wrp js_album_sort"
        # cls = "js_positive_order"

        try:
            # # Locate the iframe using the updated method
            # iframe = driver.find_element(By.TAG_NAME, "iframe")
            # # Switch to the iframe
            # driver.switch_to.frame(iframe)

            # el = driver.find_element(By.CLASS_NAME, cls)

            # Wait for the button to be clickable
            # el = WebDriverWait(driver, 10).until(
            #     EC.element_to_be_clickable(By.XPATH, f"//div[@class='{cls}']")
            # )

            WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.XPATH, f"//div[@class='{cls}']"))
            )

            xp = f"//div[@class='{cls}']/div[@class='js_negative_order order_opr_con']/span['album-sort__word']"
            # xp = '//*[@id="js_content_overlay"]/div[1]/div/div[5]/div[1]/div[1]/span'
            # xp = f"//div[@class='{cls}']"
            el = driver.find_element(By.XPATH, xp)

            # button = WebDriverWait(driver, 10).until(
            #     EC.element_to_be_clickable((By.XPATH, xp))
            # )
            # button.click()

            if el:
                # time.sleep(5.0)
                driver.implicitly_wait(2)

                print("sort reversed")

                # driver.execute_script("arguments[0].click();", el)
                el.click()

                time.sleep(1.0)
            else:
                print(f"{cls} not found")
        # except Exception as ex:
        except Exception as ex:
            print(ex)
            print(f"element {cls} click failed")
            # driver.save_screenshot('after_error.png')

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


def generate_txts(
    article_items,
    filter_original_text: bool = True,
    start_idx: int = 0,
    gn: int = 2000,
):
    group_idx = []
    group_txts = []
    txts = ""

    for idx, item in enumerate(article_items):
        # link = item["link"]
        # title = item["title"]

        txt = item["txt"]

        if txt.find("给你个建议，求人办事，事前露财，拉高办事成本") > -1:
            pass

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
                r"(材料：|【材料】)(.*?\n)*?(\s*译文：\s*|【译文】)",
                r"\1\n 略\n\3",
                txt,
            )

            txt = re.sub(
                r"(《资治通鉴》原文)(.*?\n)*?(\s*译文：\s*)",
                r"\1\n 略\n\3",
                txt,
            )

            txt = re.sub(
                r"要看(全文)*的关注微信公众号：.*?\n(阅读：.*?\n)*",
                r"",
                txt,
            )
            txt = re.sub(
                r"关注微信公众号：.*?\n(阅读：.*?\n)*",
                r"",
                txt,
            )

            txt = re.sub(
                r"关注公众号.*?\n",
                r"",
                txt,
            )

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
                r"点击阅读原文.*?\n",
                r"",
                txt,
            )

            txt = re.sub(
                r"【鸣谢】.*?\n",
                r"",
                txt,
            )

            txt = re.sub(
                r"作者简介：.*?\n",
                r"",
                txt,
            )

            txt = re.sub(
                r"Original 刘志强2018 小学生小强",
                r"",
                txt,
            )

            txt = re.sub(
                r"读资治通鉴，悟人生哲理.*?\n",
                r"",
                txt,
            )

            txt = re.sub(
                r"欢迎与作者交流(.*\n)*",
                r"",
                txt,
            )

            txt = re.sub(
                r"欢迎和作者交流(.*\n)*",
                r"",
                txt,
            )

            txt = re.sub(
                r"资治通鉴.*\n\d+.*\n企业经营.*\n\d+(.*\n)*",
                r"",
                txt,
            )

            txt = re.sub(
                r"这是作者的第\d+篇原创文章，欢迎关注！.*\n",
                r"",
                txt,
            )

            txt = re.sub(
                r"关注.*\n推荐(.*\n)*收藏.*\n分享.*\n",
                r"",
                txt,
            )

            txt = re.sub(
                r"举报.*\n评论(.*\n)*",
                r"",
                txt,
            )

            txt = re.sub(
                r"文章来自微信公众号：记忆承载。欢迎前往关注阅读全文。.*?\n",
                r"",
                txt,
            )

            txt = re.sub(
                r"文章来自微信公众号.*关注阅读全文。.*?\n",
                r"",
                txt,
            )

            txt = re.sub(
                r"原创 刘志强2018 小学生小强.*?\n",
                r"",
                txt,
            )

            txt = re.sub(
                r"好消息！《资治通鉴读史悟道·卷贰》已经出版，点击即可雅购⬇*?\n",
                r"",
                txt,
            )

            txt = re.sub(
                r"欢迎把本号设为星标(.*\n)*people underline.*\n",
                r"",
                txt,
            )

            txt = re.sub(
                r"(更多精彩文章请|people underline)",
                r"",
                txt,
            )

            txt = re.sub(
                r"敖让的净化号，无广告，更悟道！.*\n*(\d+)篇原创内容",
                r"",
                txt,
            )

            txt = re.sub(
                r"(我|敖让)的备用号(.*\n)*敖让的净化号，无广告，更悟道！",
                r"",
                txt,
            )
            txt = re.sub(
                r"(我|敖让)的备用号(.*\n)*（早关注，不迷路）",
                r"",
                txt,
            )
            txt = re.sub(
                r"敖让的净化号，无广告，更悟道！",
                r"",
                txt,
            )
            txt = re.sub(
                r"\n(欢迎把本号设为星标|敖让随笔|战国纵横|铁血前汉|秦并天下|更多精彩文章|后汉风云|三国争霸|收费文章)(.*\n)*people underline.*\n",
                r"",
                txt,
            )

            txt = re.sub(
                r"(\d+)篇原创内容",
                r"",
                txt,
            )

            txt = re.sub(
                r"Original (敖让|读史悟道) 资治通鉴读史悟道",
                r"",
                txt,
            )

            txt = re.sub(
                r"Original 王上北 上北知行观",
                r"",
                txt,
            )

            txt = re.sub(
                r"点击阅读作者更多文章：(.*\n)*",
                r"",
                txt,
            )

            txt = re.sub(
                r"全品类优惠码：(.*\n)*",
                r"",
                txt,
            )
            txt = re.sub(
                r"（全文完）(.*\n)*",
                r"",
                txt,
            )
            txt = re.sub(
                r"历史解读，敖让的个人号，(.*\n)",
                r"",
                txt,
            )

            txt = re.sub(
                r"更多精彩文章请(.*\n)*公众号",
                r"",
                txt,
            )
            txt = re.sub(
                # r"(Editor's Note|公众号)",
                r"Editor's Note",
                r"",
                txt,
            )
            txt = re.sub(
                r"\n(铁血前汉|三国争霸|资治通鉴)\n(\d+)(.*\n)*(Read more|下一篇\n.*\n)",
                r"",
                txt,
            )
            txt = re.sub(
                r"\n(铁血前汉|三国争霸|资治通鉴|敖让随笔)\n(\d+)",
                r"",
                txt,
            )
            txt = re.sub(
                r"点击【阅读原文】.*\n",
                r"",
                txt,
            )

            txt = re.sub(
                r"点击阅读读史悟道更多精彩文章(.*\n)*",
                r"",
                txt,
            )

            txt = re.sub(
                r"(我|敖让)的备用号(：|，)早关注，不迷路.*\n.*",
                r"",
                txt,
            )

            txt = re.sub(
                r"通告公示：.*\n.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"资治通鉴读史悟道(.*\n){,4}公众号",
                r"",
                txt,
            )
            txt = re.sub(
                r"(我的备用号|备用小号|备用号)(.*\n){,4}公众号",
                r"",
                txt,
            )
            txt = re.sub(
                r"(敖让的小店)(.*\n)*(小程序|Mini Program)",
                r"",
                txt,
            )
            txt = re.sub(
                r"\d+.*\n 微信豆兑换(.*\n){,3}.*(微信豆兑换|\d+微信豆\))",
                r"",
                txt,
            )

            txt = re.sub(
                r"(【冠名】|本文由读史悟道官方指定用茶)(.*\n).*共饮一壶茶",
                r"",
                txt,
            )
            txt = re.sub(
                r"同读一本书.*(点击了解更多|共饮一壶茶)",
                r"",
                txt,
            )
            txt = re.sub(
                r"视频原创：(.*\n){,6}.*【材料】",
                r"【材料】",
                txt,
            )
            txt = re.sub(
                r"可试读(.*\n){,6}.*微信豆兑换",
                r"",
                txt,
            )
            txt = re.sub(
                r"好消息(.*\n){,6}.*点击即可雅(阅|购)⬇",
                r"",
                txt,
            )

            txt = re.sub(
                r"(.*\n)关注\n",
                r"\1\n",
                txt,
            )
            txt = re.sub(
                r"喜欢此内容的人还喜欢(.*\n)*.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"(猜你喜欢：|阅读更多文章，可关注智圆行方读书|往期回顾|往期精彩|您的【点赞】是最好的鼓励！|更多文章，点击下方公众号名片)(.*\n){,10}.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"资治通鉴原文(.*\n)*.*译文：",
                r"资治通鉴原文:\n略\n译文：",
                txt,
            )

            txt = re.sub(
                r"(看更多内容， 点击下方公众号关注|智圆行方读书\n分享读书心得，解读|未经授权，谢绝转载！)(.*\n){,8}.*公众号",
                r"",
                txt,
            )
            txt = re.sub(
                r"(交流群只交流和扯淡，不提供训练服务。|推荐服务：|推荐社群：|服务内容：|推荐\d+大社群|\d+ 不要脸交流群|加V：)(.*\n){,10}.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"本文是付费阅读，上车(.*\n){0,2}堵住人性的漏洞=管理(.*\n)*.*(所有群，服务周期为一年。|(资治通鉴权谋\n\d+\n)?权谋\n\d+\n)",
                r"",
                txt,
            )
            txt = re.sub(
                r"本文是付费阅读，上车(.*\n){0,2}",
                r"",
                txt,
            )
            txt = re.sub(
                r"资治通鉴权谋\n\d+\n人情世故\n\d+\n送礼的艺术\n\d+\n",
                r"",
                txt,
            )
            txt = re.sub(
                r"未经授权，(严禁|谢绝)转载！(.*\n)*.*推荐阅读(.*\n)*.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"(欢迎个人转发至朋友圈|点个【 在看 】)(.*\n)*.*个人观点，仅供参考",
                r"",
                txt,
            )
            txt = re.sub(
                r"喜欢文章就帮忙给一个或吧↓↓个人观点，仅供参考.*",
                r"",
                txt,
            )

            txt = re.sub(
                r"Original (.*) \1",
                r"\1",
                txt,
            )
            txt = re.sub(
                r"——END——(.*\n)*",
                r"",
                txt,
            )
            txt = re.sub(
                r"\n公众号\n",
                r"",
                txt,
            )
            txt = re.sub(
                r"点击上方△蓝字△关注我.*\n每天为你深度解读《资治通鉴.*\n",
                r"",
                txt,
            )
            txt = re.sub(
                r"点击下方关注我.*\n发送关键字.*\n",
                r"",
                txt,
            )
            txt = re.sub(
                r"PS：.*\n如果你觉得上面内容还不过瘾(.*\n)*.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"PS：.*\n很多朋友问我有没有书出版(.*\n)*.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"PS：.*\n探花TV(.*\n)*.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"(点亮【 在看 】|您的【点赞】)(.*\n)*.*个人观点，仅供参考(.*\n)*.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"(最后，做一下我的《资治通鉴》解读专栏推广)(.*\n)*.*关注我，每天为你分享读史感悟(.*\n)*.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"(更多《资治通鉴》的*解读|观看更多内容，欢迎订阅我的专栏|最后给我的专栏做个推|最后，给我《资治通鉴》解读专栏)(.*\n)*.*关注我，每天为你分享读史感悟(.*\n)*.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"(做个专栏宣传|我的《资治通鉴》解读专栏|关注我，每天为你分享读史感悟。\n更多内容|更多《资治通鉴》解读内容，点击下方文章链接|关注我，每天为你分享读史.*\n往期内容)(.*\n)*.*",
                r"",
                txt,
            )

            txt = re.sub(
                r"(关注我，每天为你分享读史感悟。|更多干货，关注“ 职场智谋 ” 微信公众号)",
                r"",
                txt,
            )

            if filter_original_text:
                txt = re.sub(
                    r"\n原文(.*?\n){,5}?(\n译文\s*)",
                    r"\n原文\n 略\n\2",
                    txt,
                )

            txt = re.sub(
                r"点击上方蓝字关注我",
                r"",
                txt,
            )

            txt = re.sub(
                r"(阅读更多文章|更多精彩内容)，请关注首发(.*\n)*.*",
                r"",
                txt,
            )

            txt = re.sub(
                r"公众号【鉴史悟道】,通过历史故事的分解(.*\n)*.*",
                r"",
                txt,
            )

            txt = re.sub(
                r"上北知行观\n不是每一次阅读，都能带来成长(.*\n)*.*",
                r"",
                txt,
            )

            txt = re.sub(
                r"来都来了，点个在看再走吧(.*\n)*.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"【免责声明】文章描述过程、图片都来源于网络(.*\n)*.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"各位亲爱的读者，阅读此文前(.*\n)",
                r"",
                txt,
            )

            txt = re.sub(
                r"专栏\n(.*\n){,5}查看\n",
                r"",
                txt,
            )
            txt = re.sub(
                r".{,8}\n\d+\n",
                r"",
                txt,
            )

            txt = re.sub(
                r"点击下方关注我(.*\n)*内部资料领取方式在文末(.*\n)*谋略那些事.*\n",
                r"",
                txt,
            )
            txt = re.sub(
                r"点击下方关注我(.*\n)*谋略那些事(.*\n)*启发当下学以致用(.*\n)*",
                r"",
                txt,
            )
            txt = re.sub(
                r"(发个小广告|有很多朋友让我推荐)(.*\n)*价格不贵，一包华子而已，就能收获大佬的宝贵经验，很值！.*\n",
                r"",
                txt,
            )
            txt = re.sub(
                r"(发个小广告|有很多朋友让我推荐)(.*\n)*这本书个人读了.*\n",
                r"",
                txt,
            )
            txt = re.sub(
                r"点击下方关注我(.*\n)*谋略那些事.*\n",
                r"",
                txt,
            )
            txt = re.sub(
                r"解读《资治通鉴》，通过历史迷雾，启发当下学以致用。.*\n",
                r"",
                txt,
            )
            txt = re.sub(
                r"立志花15年讲完《资治通鉴》(.*\n){,5}谋略那些事.*\n",
                r"",
                txt,
            )
            txt = re.sub(
                r"PS：.*\n我建了一个私密分享群，目前提供六种服务(.*\n)*Comment.*\n",
                r"",
                txt,
            )
            txt = re.sub(
                r"最后推荐一个非常棒的深度历史类公众号(.*\n)*.*一见误终身。.*\n",
                r"",
                txt,
            )
            txt = re.sub(
                r"点击下方关注我.*(了解“私密分享群”|了解宝书《职场避坑指南》|了解社群|领取方式在文末|合集在文末领取)",
                r"",
                txt,
            )
            txt = re.sub(
                r"点击上方△蓝字△关注我.*(你深度解读《资治通鉴)",
                r"",
                txt,
            )
            txt = re.sub(
                r"点击上方关注我.*(电子版送您|领取电子版|送您电子版)",
                r"",
                txt,
            )
            txt = re.sub(
                r"▼点击下方名片(发送|关注).*(送私密干货。)",
                r"",
                txt,
            )
            txt = re.sub(
                r"发送关键字【\s*1.*",
                r"",
                txt,
            )

            txt = re.sub(
                r"专注硬核历史创作，深挖被人忽视的历史细节。《大汉荣耀四百年》正在连载中。.*（[一二三四五六七八九]*十[一二三四五六七八九]*）",
                r"",
                txt,
            )
            txt = re.sub(
                r"星球发送关键字【.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"不奢求您的打赏，有个赞就够了.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"喜欢的话请关注我的公众号，长期更新觉得文章还可以的话.*",
                r"",
                txt,
            )

            txt = re.sub(
                r"想第一时间读到我的文章，欢迎扫描下方的二维码关注我.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"请看丹阳论道付费课程：你想成功上位吗.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"想第一时间读到我的文章欢迎扫描下方的二维码.*",
                r"",
                txt,
            )

            txt = re.sub(
                r"《鬼谷子大智慧》已成书，实体版已断货，请加微信.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"解读《资治通鉴》目录.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"PS：如果你觉得上面内容还不过瘾.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"PS：专属群，专注个人成长内容分享，每天会分享.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"年近不惑、以书解惑。精华分享群每天分享.*",
                r"",
                txt,
            )

            txt = re.sub(
                r"最后推荐一个非常棒的深度历史类公众号，我也经常看.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"关键字【.*",
                r"",
                txt,
            )

            txt = re.sub(
                r"如果没有关注我的朋友，扫描二维码后.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"PS：我建了一个私密分享群.*",
                r"",
                txt,
            )

            txt = re.sub(
                r"全文完，感谢阅读，如果喜欢请三连.*",
                r"",
                txt,
            )

            txt = re.sub(
                r"PS：上面文章还不过瘾，这里还有一个精选分享群.*",
                r"",
                txt,
            )

            txt = re.sub(
                r"不求您的打赏，但求您能点个赞、您看成吗？.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"今天的内容又有点长，您也别打赏了，就点个赞和再看好吗？.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"不知不觉.*多字，.*您也别打赏了，能否点个赞？.*",
                r"",
                txt,
            )
            txt = re.sub(
                r"福利:.*再次恳请大家谅解.*",
                r"",
                txt,
            )

            if len(txt) > 0:
                valid_texts = re.search(r"\S", txt)
                if valid_texts:
                    txts += f"\n第{idx_t:04}章\n\n{txt}\n"

                    if idx_t % gn == 0:
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
        m = driver.find_element(By.TAG_NAME, value="body")
        # meta = m.text
        meta = ""
    except Exception as ex:
        print(link, title, ex)

    content = None

    # it = 0
    # while it < 5:
    #     try:
    #         content = m.text
    #         break
    #     except Exception as ex:
    #         print(link, title, ex)
    #         pass
    #     time.sleep(0.3)
    #     it += 1
    #     pass

    # if content is None:
    #     return ""

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
        link = item["link"]
        title = item["title"]
        dt = item.get("date", "")

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

                add_dt = False
                dts = re.search(r"(\d+-\d+-\d+ \d+:\d+)", txt)
                if dts:
                    dt = dttm.datetime.strptime(dts.group(), "%Y-%m-%d %H:%M")
                else:
                    match = re.search(r"\d+-\d+-\d+-\d+-\d+_", file_name)
                    if match:
                        dts = match.group()
                        dts = dts[:-1]
                        dt = dttm.datetime.strptime(dts, "%Y-%m-%d-%H-%M")
                        add_dt = True
                    else:
                        # dt = dttm.datetime.now()
                        mod_time = os.path.getmtime(file_name)
                        dt = dttm.datetime.fromtimestamp(mod_time)
                    # continue
                    pass

                if add_dt:
                    dts = dt.strftime("%Y-%m-%d %H:%M")
                    txt = f"{dts}\n\n{txt}"
                    pass

                txt = f"{txt}\n\n"
                article_item = {
                    "link": file_base_name,
                    "title": title,
                    "date": dt,
                    "txt": txt,
                }
                article_items.append(article_item)

    return article_items


def scrape_item(
    idx,
    item,
    scrape,
    nocache,
    max_articles,
    is_article: bool,
    max_checks: int = 0,
):
    link = item["link"]
    name = item["name"]
    flter = item["filter"]
    if link:
        # origin = item.get("origin", "tt")
        origin = "tt"
        if link.find("mp.weixin.qq.com") > -1:
            origin = "wp"
        elif link.find("www.toutiao.com") > -1:
            origin = "tt"
        else:
            assert False, "only toutiao or wp supported"

        sort_reversed = item.get("reversed", False)
        include_title = item.get("include_title", False)

        uid = link[-20:]
        uid = re.sub(r"/", r"_", uid)
        uid = re.sub("['?']", r"", uid)
        uid = re.sub(r"&", r"_", uid)
        uid = re.sub(r"=", r"_", uid)
        # uid = uid.replace("/?&", "_")

        if is_article:
            if isinstance(flter, list):
                article_path = f".torextrader/toutiao/article_{uid}_{name}"
                for f in flter:
                    article_path = f"{article_path}_{f}"
            else:
                article_path = f".torextrader/toutiao/article_{uid}_{name}_{flter}"
        else:
            if isinstance(flter, list):
                article_path = f".torextrader/toutiao/w_{uid}_{name}"
                for f in flter:
                    article_path = f"{article_path}_{f}"
            else:
                article_path = f".torextrader/toutiao/w_{uid}_{name}_{flter}"
    else:
        article_path = item["article_path"]
        pass

    cache_config_info = ""
    if nocache:
        cache_config = item.get("cache", None)
        if cache_config is not None:
            cache_config_info = f"{cache_config}"
            nocache = not cache_config
        else:
            if origin == "wp":
                nocache = False
            pass
        pass

    cache_info = "nocache" if nocache else "cache"
    if cache_config_info:
        cache_info += f"[config={cache_config_info}]"
    print(colored(f">{idx}", "yellow"), f"{name} {cache_info} {flter} {link}")

    # articles_path = f".torextrader/toutiao/{name}_{filter}"
    # paths = [article_path, articles_path]

    paths = [article_path]

    for path in paths:
        if not os.path.exists(path):
            os.makedirs(path)

    try:
        if scrape:
            all_update_items = get_all_update_items(
                origin=origin,
                link=link,
                article_path=article_path,
                flter=flter,
                cache=not nocache,
                max_articles=max_articles,
                is_article=is_article,
                sort_reversed=sort_reversed,
                max_checks=max_checks,
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
        else:
            all_update_items = []

        return article_path, all_update_items

    except Exception as ex:
        print(ex)

    return article_path, []


# def test_link():
#     # put chromedriver.exe at the same folder of current .py
#     service = ChromeService(executable_path="chromedriver.exe")
#     driver = ChromeWebDriver(service=service, options=options)

#     driver.get("https://www.google.com")

#     WebDriverWait(driver, 2).until(
#         EC.presence_of_element_located((By.CLASS_NAME, "glFyf"))
#     )
#     input_element = driver.find_element(By.CLASS_NAME, value="glFyf")

#     input_element.clear()
#     input_element.send_keys("tech with tim" + Keys.ENTER)

#     WebDriverWait(driver, 2).until(
#         EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "Tech With Tim"))
#     )
#     link = driver.find_element(By.PARTIAL_LINK_TEXT, "Tech With Tim")
#     link.click()

#     pass


# def test_cookie():
#     # put chromedriver.exe at the same folder of current .py
#     service = ChromeService(executable_path="chromedriver.exe")
#     driver = ChromeWebDriver(service=service, options=options)

#     driver.get("https://orteil.dashnet.org/cookieclicker/")

#     # https://orteil.dashnet.org/cookieclicker/

#     cookie_id = "bigCookie"
#     cookies_id = "cookies"
#     product_price_prefix = "productPrice"
#     product_prefix = "product"

#     WebDriverWait(driver, 5).until(
#         EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'English')]"))
#     )

#     language = driver.find_element(By.XPATH, "//*[contains(text(), 'English')]")
#     language.click()

#     WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, cookie_id)))

#     cookie = driver.find_element(By.ID, cookie_id)

#     while True:
#         cookie.click()
#         cookies_count = driver.find_element(By.ID, cookies_id).text.split(" ")[0]
#         cookies_count = int(cookies_count.replace(",", ""))

#         for i in range(4):
#             product_price = driver.find_element(
#                 By.ID, product_price_prefix + str(i)
#             ).text.replace(",", "")

#             if not product_price.isdigit():
#                 continue

#             product_price = int(product_price)

#             if cookies_count >= product_price:
#                 product = driver.find_element(By.ID, product_prefix + str(i))
#                 product.click()
#                 break


def main():
    # fp = (
    #     ".torextrader/toutiao/花言大帅的头条主页 - 今日头条(www.toutiao.com).html",
    # )
    # html = get_html_from_file(fp)

    parser = argparse.ArgumentParser()

    # parser.add_argument(
    #     "-k",
    #     "--link",
    #     help="合集链接",
    #     type=str,
    #     default="https://www.toutiao.com/c/user/token/MS4wLjABAAAAhIQQ1-9RNTm8W8CUcDGNjOwJWE14yrkMotgE5YwmQ0Y",
    # )
    # parser.add_argument(
    #     "-t", "--filter", help="标题关键字", type=str, default="资治通鉴"
    # )
    # parser.add_argument("-n", "--name", help="作品名字", type=str, default="花言大帅")

    parser.add_argument("-x", "--index", help="index", type=int, default=None)
    parser.add_argument("-m", "--checks", help="max checks", type=int, default=None)
    parser.add_argument("-a", "--max", help="max items", type=int, default=None)
    parser.add_argument(
        "-n", "--nocache", help="refresh all articles", action="store_true"
    )
    parser.add_argument(
        "-f", "--force", help="force to check all the articles", action="store_true"
    )
    parser.add_argument(
        "--all",
        help="include all items, otherwise ignore those wp",
        action="store_true",
    )

    parser.add_argument("-s", "--scrape", help="scrape", action="store_true")
    # parser.add_argument("-e", "--edge", help="use edge", action="store_true")
    parser.add_argument("-r", "--chrome", help="use chrome", action="store_true")

    parser.add_argument(
        "-c",
        "--config",
        default=".torextrader/scrape_toutiao_config.json",
        type=str,
        help="config file",
    )

    args = parser.parse_args()
    max_items = args.max
    max_items = max_items if max_items is not None and max_items > 0 else 0
    max_articles_default = max_items

    max_checks = args.checks
    max_checks = max_checks if max_checks is not None and max_checks > 0 else 0

    # use_edge_web_driver = args.edge
    use_edge_web_driver = not args.chrome

    global driver
    driver = create_drive(use_edge_web_driver)

    # time.sleep(50.0)
    force = args.force
    articles_path = ".torextrader/toutiao"
    all = args.all

    if args.config and args.config != "none":
        config: dict = load_json(args.config)
        items = config["items"]

        if args.index is not None:
            idx = args.index

            if idx >= len(items) or idx < 0:
                print(f"invalid index: {idx}")
                return

            item = items[idx]

            handle_item(
                args,
                max_articles_default,
                max_checks,
                force,
                articles_path,
                idx,
                item,
                all=all,
            )
            pass

        else:
            for idx, item in enumerate(items):
                handle_item(
                    args,
                    max_articles_default,
                    max_checks,
                    force,
                    articles_path,
                    idx,
                    item,
                    all=all,
                )
                pass
    else:
        print("no config specified")
        return

    driver.quit()

    pass


def handle_item(
    args,
    max_articles_default,
    max_checks,
    force,
    articles_path,
    idx,
    item,
    all: bool = False,
):
    name = item.get("name", None)
    flter = item.get("filter", None)

    group_idx = []
    group_txts = []

    all_update_items = []

    print(colored(f">>> {idx}", "yellow"))

    items_txt = item.get("article_path", None)
    if all:
        if not force and items_txt is not None:
            force = True
            pass
    elif items_txt is not None:
        print(
            colored(
                f"items already downloaded ignored: {items_txt}, please pass '--all'",
                "yellow",
            )
        )
        return

    is_array = False
    if "subitems" in item:
        is_array = True
        subitems = item["subitems"]
        force_t = True
        for ix, itm in enumerate(subitems):
            sn, update_items, group_idx, group_txts = generate_item(
                args,
                max_articles_default,
                max_checks,
                force_t,
                ix,
                itm,
                group_idx,
                group_txts,
            )
            all_update_items = [*all_update_items, *update_items]
            if name is None:
                name = sn
            pass
        pass
    else:
        sn, update_items, group_idx, group_txts = generate_item(
            args,
            max_articles_default,
            max_checks,
            force,
            idx,
            item,
            group_idx,
            group_txts,
        )
        all_update_items = [*all_update_items, *update_items]
        pass

    gn = item.get("group_num", group_num)

    if group_idx and group_txts:
        grp_idxs = []
        grp_txts = []

        if is_array:
            num_total = group_idx[-1]
            txts = ""

            num_grps = len(group_idx)
            for i in range(num_grps):
                idx = group_idx[i]
                txt = group_txts[i]

                txts += txt
                last_total = idx
                if last_total >= gn:
                    grp_idxs.append(last_total)
                    grp_txts.append(txts)
                    txts = ""

            if txts:
                grp_idxs.append(last_total)
                grp_txts.append(txts)
        else:
            grp_idxs = group_idx
            grp_txts = group_txts
            num_total = group_idx[-1]

        if force or all_update_items:
            if flter:
                if isinstance(flter, list):
                    for f in flter:
                        name = f"{name}_{f}"
                else:
                    name = f"{name}_{flter}"
                pass
            # print(colored(f"generate files {name} from {num_total} txts...", "green")
            write_txts(articles_path, name, grp_idxs, grp_txts)
            pass
        else:
            print(colored(f"no updated articles for {num_total} txts", "yellow"))
            pass
        pass
    pass


def generate_item(
    args, max_articles_default, max_checks, force, idx, item, group_idx, group_txts
):
    name = item.get("name", None)
    max_articles = item.get("max", max_articles_default)
    is_article = item.get("is_article", True)

    article_path, update_items = scrape_item(
        idx,
        item,
        scrape=args.scrape,
        nocache=args.nocache,
        max_articles=max_articles,
        is_article=is_article,
        max_checks=max_checks,
    )

    if force or update_items:
        filter_original_text = item.get("filter_original_text", True)
        article_items = get_articles_items(article_path)
        sorted_article_items = sorted(article_items, key=lambda x: x["date"])
        if max_articles > 0 and len(sorted_article_items) > max_articles:
            sorted_article_items = sorted_article_items[-max_articles:]

        print(colored(f"generate txts from {len(article_items)} articles...", "green"))

        start_idx = group_idx[-1] if group_idx else 0

        gn = item.get("group_num", group_num)
        group_idx_t, group_txts_t = generate_txts(
            sorted_article_items,
            filter_original_text=filter_original_text,
            start_idx=start_idx,
            gn=gn,
        )
        group_idx = [*group_idx, *group_idx_t]
        group_txts = [*group_txts, *group_txts_t]
        pass
    return name, update_items, group_idx, group_txts


main()
