# https://www.youtube.com/watch?v=nBzrMw8hkmY
import requests
from bs4 import BeautifulSoup
import pandas as pd

proxy = ""
current_page = 1

data = []
proceed = True
while proceed:
    url = f"https://books.toscrape.com/catalogue/page-{current_page}.html"

    page = requests.get(url, proxies=proxy)
    # print(page.text)

    soup = BeautifulSoup(page.text, "html.parser")
    # print(soup.title.text)

    if soup.title.text == "404 Not Found":
        proceed = False

    else:
        all_books = soup.find_all("li", class_="col-xs-6 col-sm-4 col-md-3 col-lg-3")
        for book in all_books:
            item = {}

            item["title"] = book.find("img").attrs["alt"]
            link = book.find("a").attrs["href"]
            item["link"] = f"https://books.toscrape.com/{link}"
            item["price"] = book.find("p", class_="price_color").text[2:]
            item["stock"] = book.find("p", class_="instock availability").text.strip()
            data.append(item)
            pass
        pass

    current_page += 1
    # print(data)

df = pd.DataFrame(data)

df.to_csv(".torextrader/datacache/book.csv")

# https://www.toutiao.com/c/user/token/MS4wLjABAAAAhIQQ1-9RNTm8W8CUcDGNjOwJWE14yrkMotgE5YwmQ0Y/
