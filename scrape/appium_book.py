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

from selenium.webdriver.common.by import By
from io import BytesIO
from PIL import Image
from selenium.common.exceptions import TimeoutException

import ddddocr

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
#   mCurrentFocus=Window{bd521ad u0 com.ss.android.article.news/com.ss.android.*.LearningArticleDetailActivity}


# HWBKL:/ $ dumpsys window displays | grep -E mFocusedApp
#     mFocusedApp=AppWindowToken{b9b0b83 token=Token{b9a89ee ActivityRecord{b9b0b05 u0 com.ss.*.article.news/com.ss.*}}}
#     mFocusedApp=Token{b9a89ee ActivityRecord{b9b0b05 u0 com.ss.*.news/com.ss.*.LearningArticleDetailActivity t42567}}

# "dumpsys window displays | grep -E mCurrentFocus" outputs info with appPackage / appActivity
# com.greenline.guahao/com.greenline.guahao.webkit.MainProcessCommonWebActivity
# com.ss.android.article.news/com.ss.android.detail.feature.detail2.learning.activity.LearningArticleDetailActivity


class ScrapeBook:
    def __init__(self):
        print("init ScrapeBook")
        self.desired_caps = dict(
            platformName="Android",
            # deviceName="127.0.0.1:21513",
            # deviceName="emulator-5554",
            deviceName="A7QDU18B20004140",
            # "platformVersion": "5.1",
            # app="d:/downloads/sss.apk",
            # appPackage="com.tencent.mm",
            # appActivity="com.tencent.mm.plugin.webview.ui.tools.MMWebViewUI",
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

        print("done init ScrapeBook")

        pass

    def goto_page(self, driver: webdriver, use50):
        actions = ActionChains(driver)
        actions.w3c_actions = ActionBuilder(
            driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch")
        )

        while True:
            if use50:
                xp_btn_pre_s = '//android.view.View[@resource-id="yuanqu_虹桥院区"]/android.view.View[2]'
            else:
                xp_btn_pre_s = '//android.view.View[@resource-id="yuanqu_虹桥院区"]/android.view.View[4]'
            xp_btn_pre = (
                xp_btn_pre_s
                + '/android.view.View/android.widget.TextView[@text="预约"]'
            )

            btn_pres = driver.find_elements(
                by=MobileBy.XPATH,
                value=xp_btn_pre,
            )

            if btn_pres:
                print(f"found: {xp_btn_pre}")
                # btn_pre = btn_pres[-1]
                btn_pre = btn_pres[0]
                btn_pre.click()
                # break

                # xp = '//android.webkit.WebView[@text="预约"]/android.view.View/android.widget.TextView'
                xp = '//android.widget.TextView[@resource-id="android:id/text1"]'

                # WebDriverWait(driver, 0.01).until(
                #     EC.presence_of_element_located((By.XPATH, xp))
                # )
                els = driver.find_elements(
                    # by=MobileBy.ANDROID_UIAUTOMATOR,
                    # value='new UiSelector().text("qBOdWHB84NoAAAAASUVORK5CYII=")',
                    by=MobileBy.XPATH,
                    value=xp,
                )
                if els:
                    print(f"found {xp}")
                    break
                else:
                    print(f"unfound {xp}")
            else:
                print(f"unfound: {xp_btn_pre}")
                time.sleep(0.1)
                pass
            pass

        actions = ActionChains(driver)
        actions.w3c_actions = ActionBuilder(
            driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch")
        )
        actions.w3c_actions.pointer_action.move_to_location(507, 1802)
        actions.w3c_actions.pointer_action.pointer_down()
        actions.w3c_actions.pointer_action.move_to_location(336, 44)
        actions.w3c_actions.pointer_action.release()
        actions.perform()

        actions = ActionChains(driver)
        actions.w3c_actions = ActionBuilder(
            driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch")
        )
        actions.w3c_actions.pointer_action.move_to_location(500, 1922)
        actions.w3c_actions.pointer_action.pointer_down()
        actions.w3c_actions.pointer_action.move_to_location(367, 263)
        actions.w3c_actions.pointer_action.release()
        actions.perform()

        actions = ActionChains(driver)
        actions.w3c_actions = ActionBuilder(
            driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch")
        )
        actions.w3c_actions.pointer_action.move_to_location(564, 1609)
        actions.w3c_actions.pointer_action.pointer_down()
        actions.w3c_actions.pointer_action.move_to_location(554, 618)
        actions.w3c_actions.pointer_action.release()
        actions.perform()

        actions = ActionChains(driver)
        actions.w3c_actions = ActionBuilder(
            driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch")
        )
        actions.w3c_actions.pointer_action.move_to_location(792, 1865)
        actions.w3c_actions.pointer_action.pointer_down()
        actions.w3c_actions.pointer_action.pause(0.1)
        actions.w3c_actions.pointer_action.release()
        actions.perform()

        actions = ActionChains(driver)
        actions.w3c_actions = ActionBuilder(
            driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch")
        )
        actions.w3c_actions.pointer_action.move_to_location(516, 2014)
        actions.w3c_actions.pointer_action.pointer_down()
        actions.w3c_actions.pointer_action.move_to_location(485, 713)
        actions.w3c_actions.pointer_action.release()
        actions.perform()

        actions = ActionChains(driver)
        actions.w3c_actions = ActionBuilder(
            driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch")
        )
        actions.w3c_actions.pointer_action.move_to_location(554, 1641)
        actions.w3c_actions.pointer_action.pointer_down()
        actions.w3c_actions.pointer_action.move_to_location(516, 478)
        actions.w3c_actions.pointer_action.release()
        actions.perform()
        return True

    def entry(self, use50: bool):
        driver = self.driver

        while True:
            ret = self.goto_page(driver, use50=use50)

            if ret:
                # captcha = driver.find_element(By.CSS_SELECTOR, "#android.widget.Image")
                images = driver.find_elements(
                    # by=MobileBy.ANDROID_UIAUTOMATOR,
                    # value='new UiSelector().text("qBOdWHB84NoAAAAASUVORK5CYII=")',
                    by=MobileBy.XPATH,
                    value='//android.widget.Image[@index="0"]',
                )
                if images:
                    break
            print("no captcha found, goto_page again")
            pass

        captcha_element = images[-1]
        image = Image.open(BytesIO(captcha_element.screenshot_as_png))

        # image = preprocess(image)
        # captcha = tesserocr.image_to_text(image)

        # https://github.com/sml2h3/ddddocr
        # ocr = ddddocr.DdddOcr()
        ocr = ddddocr.DdddOcr(beta=True)  # 切换为第二套ocr模型
        # captcha = ocr.classification(image)
        captcha = ocr.classification(image, png_fix=True)

        captcha = re.sub("[^A-Za-z0-9]", "", captcha)

        print("captcha:", captcha)

        # xp = '//android.view.View[@resource-id="page"]/android.view.View[5]/android.view.View[6]/android.widget.EditText'
        # driver.find_element(
        #     by=MobileBy.XPATH,
        #     value=xp,
        # ).send_keys(captcha)
        xp = "//android.widget.EditText"
        texts = driver.find_elements(
            by=MobileBy.XPATH,
            value=xp,
        )
        text = texts[-1]
        text.send_keys(captcha)

        btn_sumbit = self.driver.find_element(
            by=MobileBy.XPATH,
            value='//android.view.View[@content-desc="提交预约"]',
        )
        btn_sumbit.click()

        time.sleep(0.1)

        actions = ActionChains(driver)
        actions.w3c_actions = ActionBuilder(
            driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch")
        )
        actions.w3c_actions.pointer_action.move_to_location(747, 1318)
        actions.w3c_actions.pointer_action.pointer_down()
        actions.w3c_actions.pointer_action.pause(0.1)
        actions.w3c_actions.pointer_action.release()
        actions.perform()

        pass


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--scrape", help="scrape the app", action="store_true")
    parser.add_argument("-u", "--use50", help="use50", action="store_true")
    args = parser.parse_args()

    scrape = args.scrape
    if scrape:
        scaper = ScrapeBook()
        use50 = args.use50
        scaper.entry(use50)
        pass

    pass


main()
