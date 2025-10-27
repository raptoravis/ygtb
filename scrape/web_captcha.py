import time
import re
import argparse
from selenium import webdriver
from io import BytesIO
from PIL import Image
from retrying import retry
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import numpy as np

# import tesserocr
import ddddocr


# https://cuiqingcai.com/202291.html


def preprocess(image):
    image = image.convert("L")
    array = np.array(image)
    array = np.where(array > 50, 255, 0)
    image = Image.fromarray(array.astype("uint8"))
    return image


def login(browser):
    browser.get("https://captcha7.scrape.center/")
    browser.find_element(By.CSS_SELECTOR, '.username input[type="text"]').send_keys(
        "admin"
    )
    browser.find_element(By.CSS_SELECTOR, '.password input[type="password"]').send_keys(
        "admin"
    )
    captcha = browser.find_element(By.CSS_SELECTOR, "#captcha")
    image = Image.open(BytesIO(captcha.screenshot_as_png))

    # image = preprocess(image)
    # captcha = tesserocr.image_to_text(image)

    # https://github.com/sml2h3/ddddocr
    ocr = ddddocr.DdddOcr()
    captcha = ocr.classification(image)
    # ocr = ddddocr.DdddOcr(beta=True)  # 切换为第二套ocr模型
    # captcha = ocr.classification(image, png_fix=True)

    captcha = re.sub("[^A-Za-z0-9]", "", captcha)

    print("captcha:", captcha)

    browser.find_element(By.CSS_SELECTOR, '.captcha input[type="text"]').send_keys(
        captcha
    )
    browser.find_element(By.CSS_SELECTOR, ".login").click()
    try:
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, '//h2[contains(., "登录成功")]'))
        )
        time.sleep(10)
        browser.close()
        return True
    except TimeoutException:
        return False


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--captcha", help="test captcha", action="store_true")
    args = parser.parse_args()

    captcha = args.captcha
    if captcha:
        browser = webdriver.Chrome()
        login(browser)
        pass
    pass


main()
