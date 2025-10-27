import time
import os
import re
import glob
import argparse
import datetime as dttm

from appium import webdriver

# from appium.webdriver.webdriver import WebDriver
from appium.webdriver.common.mobileby import MobileBy

# from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.extensions.action_helpers import ActionHelpers

# from appium.webdriver.common.touch_action import TouchAction
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.mouse_button import MouseButton
from selenium.webdriver.common.actions.pointer_input import PointerInput

from appium.options.android import UiAutomator2Options

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# https://www.cnblogs.com/sgh1023/p/11748072.html

# Appium地址
DRIVER_SERVER = "http://localhost:4723"
# DRIVER_SERVER = "http://localhost:4723/wd/hub"

# 等待元素加载时间
TIMEOUT = 30

# 1. install nodejs and appium: npm install -g appium-installer
# 1. install android studio
# 1. ANDROID_HOME=C:\Users\rapto\AppData\Local\Android\Sdk
# 1. path: %ANDROID_HOME%\platform-tools
# 1. path: %ANDROID_HOME%\tools
# 1. path: %ANDROID_HOME%\tools\bin
# 1. launch the virtual device
# 1. appium --use-plugins=element-wait --allow-cors
# 1. modify the deviceName (adb devices)


# adb shell dumpsys window displays | findstr mCurrentFocus

# D:\dev>adb shell dumpsys window displays | findstr mCurrentFocus
#   mCurrentFocus=Window{bacc65d u0 com.greenline.guahao/com.greenline.guahao.webkit.MainProcessCommonWebActivity}

# adb shell
#   dumpsys window displays | grep -E 'mCurrentFocus|mFocusedApp'
#   dumpsys window displays | grep -E mCurrentFocus


# HWBKL:/ $ dumpsys window displays | grep -E mCurrentFocus
#   mCurrentFocus=Window{bd521ad u0 com.ss.android.article.news/com.ss.android.detail.*}


# HWBKL:/ $ dumpsys window displays | grep -E mFocusedApp
#     mFocusedApp=AppWindowToken{b9b0b83 token=Token{b9a89ee ActivityRecord{b9b0b05 u0 com.ss..news/com.*}}}
#     mFocusedApp=Token{b9a89ee ActivityRecord{b9b0b05 u0 com.ss.android.article.news/com.ss.android.detail.* t42567}}

# "dumpsys window displays | grep -E mCurrentFocus" outputs info with appPackage / appActivity
# com.greenline.guahao/com.greenline.guahao.webkit.MainProcessCommonWebActivity
# com.ss.android.article.news/com.ss.android.detail.feature.detail2.learning.activity.LearningArticleDetailActivity


class ScrapeLearning:
    def __init__(self):
        print("init ScrapeLearning")
        self.desired_caps = dict(
            platformName="Android",
            # deviceName="127.0.0.1:21513",
            deviceName="emulator-5554",
            # deviceName="A7QDU18B20004140",
            # "platformVersion": "5.1",
            # app="d:/downloads/sss.apk",
            appPackage="com.ss.android.article.news",
            # appActivity="com.ss.android.newmedia.activity.browser.BrowserActivity",  # 主页
            appActivity="com.ss.android.detail.feature.detail2.learning.activity.LearningArticleDetailActivity",
            noReset=True,
            fullReset=False,
            autoLaunch=False,
            automationName="UiAutomator2",
        )
        # self.driver = WebDriver(
        self.driver = webdriver.Remote(
            DRIVER_SERVER,
            desired_capabilities=None,
            # desired_capabilities=self.desired_caps,
            options=UiAutomator2Options().load_capabilities(self.desired_caps),
        )

        print("done init ScrapeLearning")

        pass

    # def scroll_to_element(self, elementId, elementName: str, scrollDown: bool):
    #     if scrollDown:
    #         direction = "down"
    #     else:
    #         direction = "up"

    #     scrollObject = dict(direction=direction, element=elementId, text=elementName)
    #     self.driver.execute_script("mobile: scrollTo", scrollObject)

    def scroll_to_next_visible(self):
        next_btn = None
        txt = {}
        tt = ""

        root_view = None

        try:
            WebDriverWait(self.driver, TIMEOUT).until(
                EC.presence_of_element_located(
                    (MobileBy.XPATH, '//android.view.View[@resource-id="root"]')
                )
            )
        except Exception:
            pass

        try:
            root_view = self.driver.find_element(
                by=MobileBy.XPATH,
                value='//android.view.View[@resource-id="root"]',
            )

        # except Exception as ex:
        except Exception:
            # print("find_elements next btn", ex)
            print("failed to find root")
            pass

        if root_view is None:
            return next_btn, tt

        for idx in range(20):
            try:
                text_views = root_view.find_elements(
                    by=MobileBy.XPATH, value="//android.widget.TextView"
                )

                for text_view in text_views:
                    if text_view.text == "上一章":
                        break

                    t = txt.get(text_view.id, None)
                    if t is None:
                        txt[text_view.id] = text_view.text

            except Exception:
                # print(ex)
                pass

            try:
                next_btn = self.driver.find_element(
                    by=MobileBy.XPATH,
                    value='//android.widget.TextView[@text="下一章"]',
                )

                if next_btn and next_btn.is_displayed():
                    break
            except Exception:
                # print(ex)
                pass

            self.scroll_down_up(down=True)
        pass

        if next_btn:
            print(f"scroll_to_next_visible btn {next_btn.id}")
        else:
            print("scroll_to_next_visible failed to find next btn")

        # first = True
        for id, t in txt.items():
            tt += t
            tt += "\n"

            # if first:
            #     print(t)
            #     first = False
            pass

        return next_btn, tt

    def scroll_to_header_visible(self):
        header = None

        try:
            WebDriverWait(self.driver, TIMEOUT).until(
                EC.presence_of_element_located(
                    (MobileBy.XPATH, '//android.view.View[@resource-id="root"]')
                )
            )
        except Exception:
            pass

        for idx in range(20):
            try:
                header = self.driver.find_element(
                    by=MobileBy.XPATH,
                    # value='//android.widget.TextView[@resource-id="title"]',
                    value='//android.view.View[@resource-id="author"]/android.view.View',
                )

                if header and header.is_displayed():
                    break

            except Exception:
                # print(ex)
                pass

            self.scroll_down_up(down=False)
        pass

        if header:
            print(f"scroll_to_header_visible header {header.id}")
        else:
            print("scroll_to_header_visible failed to find header")

        return header

    def scroll_down_up(self, down: bool):
        start_x = 300
        # self.driver.swipe(start_x, 1000, start_x, 200, 2000)

        actions = ActionChains(self.driver)
        actions.w3c_actions = ActionBuilder(
            self.driver,
            mouse=PointerInput(interaction.POINTER_TOUCH, "touch"),
            duration=250,
        )

        if down:
            start_y = 1100
            end_y = 280
        else:
            start_y = 280
            end_y = 1100

        actions.w3c_actions.pointer_action.move_to_location(start_x, start_y)
        actions.w3c_actions.pointer_action.pointer_down()
        actions.w3c_actions.pointer_action.move_to_location(start_x, end_y)
        actions.w3c_actions.pointer_action.release()
        actions.perform()

        time.sleep(1)
        pass

    def entry(self, article_path, idx):

        # contents = self.driver.find_elements(
        #     by=MobileBy.XPATH, value="//android.view.View[@text='目录']"
        # )
        # print(contents)

        if not os.path.exists(article_path):
            os.makedirs(article_path)

        last_idx = idx
        while True:
            # time.sleep(1)

            self.scroll_to_header_visible()

            btn, txt = self.scroll_to_next_visible()

            if txt:
                fn = f"{article_path}/{last_idx:04}.txt"

                pos_nl = txt.find("\n")
                if pos_nl > 0:
                    title = txt[:pos_nl]
                else:
                    title = ""

                print(f"title {title}")

                with open(
                    fn,
                    "w",
                    encoding="utf-8",
                ) as fp:
                    fp.write(txt)
                    last_idx += 1
                    print(f"{fn} generated")

            if btn:
                print(f"btnid {btn.id}\n")

                try:
                    btn.click()
                except Exception as ex:
                    print("scroll and click", ex)

                time.sleep(3)
                # break
            else:
                print("next btn is not found")
                break
            pass

        print("to the end")
        pass


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
                r"毛主席把《资治通鉴》读了十七遍(.*\n)*",
                r"点击下方即可订阅本专栏.*\n",
                r"以上是专栏【资治通鉴中的权与谋】(.*\n)*",
                r"专栏【资治通鉴中的权与谋】现在优惠中.*\n",
                r"专栏【资治通鉴中的权与谋】.*\n",
                r"专栏其他精彩文章(.*\n)*",
                r"专栏精彩文章(.*\n)*",
                r"关注\n",
            ]:
                txt = re.sub(t, r"", txt)
                pass

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

    parser.add_argument("-s", "--scrape", help="scrape the app", action="store_true")
    parser.add_argument(
        "-e", "--export", help="export the articles", action="store_true"
    )
    parser.add_argument("-d", "--uid", help="uid", type=int, default=1)
    parser.add_argument("-x", "--idx", help="index", type=int, default=None)
    args = parser.parse_args()

    uid = args.uid
    filter = ""
    name = "权谋资治通鉴"
    article_path = f".torextrader/toutiao/article_{uid}_{name}"

    scrape = args.scrape
    if scrape:
        if args.idx is None:
            article_items = get_articles_items(article_path)
            idx = len(article_items) + 1
        else:
            idx = args.idx

        scaper = ScrapeLearning()
        scaper.entry(article_path, idx=idx)
        pass

    export = args.export
    if export:
        article_items = get_articles_items(article_path)
        print(f"generate combined articles from {len(article_items)} articles...")

        sorted_article_items = sorted(article_items, key=lambda x: x["date"])

        name = f"{name}_{uid:02}"

        articles_path = ".torextrader/toutiao/权谋资治通鉴"

        paths = [articles_path]

        for path in paths:
            if not os.path.exists(path):
                os.makedirs(path)

        generate_txts(
            sorted_article_items,
            articles_path,
            filter=filter,
            name=name,
        )
    pass


main()
