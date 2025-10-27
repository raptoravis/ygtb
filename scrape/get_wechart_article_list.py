import yaml
import time
import random
import requests
import json

# https://zhuanlan.zhihu.com/p/541713940


def get_headers(config):
    headers = {"Cookie": config["cookie"], "User-Agent": config["user-agent"]}
    return headers


def get_params(config):
    begin = "0"
    params = {
        "sub": "list",
        "search_field": "null",
        "begin": begin,
        "count": "5",
        "query": "",
        "fakeid": config["fakeid"],
        "type": "101_1",
        "free_publish_type": "1",
        "sub_action": "list_ex",
        "fingerprint": config["fingerprint"],
        "token": config["token"],
        "lang": "zh_CN",
        "f": "json",
        "ajax": "1",
    }
    return params


def generate_url(base_url, params=None):
    req = requests.Request("GET", base_url, params=params)
    prepared = req.prepare()
    return prepared.url


def get_article_list(
    headers,
    params,
):
    base_url = "https://mp.weixin.qq.com/cgi-bin/appmsgpublish"

    i = 0
    column_name = "link,create_time,author_name,title,digest"
    data_path = ".torextrader/toutiao/"
    article_list_path = f"{data_path}article_list.csv"
    while True:
        begin = i * 5
        params["begin"] = str(begin)

        # 随机暂停几秒，避免过快的请求导致过快的被查到
        time.sleep(random.randint(1, 10))

        use_url = True
        if use_url:
            url = generate_url(base_url=base_url, params=params)
            resp = requests.get(url, headers=headers, verify=False)
        else:
            resp = requests.get(url, headers=headers, params=params, verify=False)

        # 微信流量控制, 退出
        data = resp.json()
        if data["base_resp"]["ret"] == 200013:
            print("frequencey control, stop at {}".format(str(begin)))
            time.sleep(3600)
            continue

        publish_page_str = data.get("publish_page", None)

        if publish_page_str is None:
            break

        # publish_page = eval(publish_page_str)
        publish_page = json.loads(publish_page_str)

        if i == 0:
            total_count = publish_page["total_count"]
            print("We have " + str(total_count) + " articles.")

            with open(article_list_path, "w", encoding="utf-8") as f:
                f.write(column_name + "\n")

        publish_list = publish_page["publish_list"]
        # 如果返回的内容中为空则结束
        if len(publish_list) == 0:
            print("all ariticle parsed")
            break

        for p in publish_list:
            pi = p.get("publish_info", None)
            if not pi:
                continue
            # publish = eval(pi.replace("true", "True").replace("false", "False"))[
            #     "appmsgex"
            # ][0]
            pij = json.loads(pi)
            publishs = pij["appmsgex"]
            p = publishs[0]

            info = f'"{p["link"]}","{p["create_time"]}","{p["author_name"]}","{p["title"]}","{p["digest"]}"'

            with open(article_list_path, "a", encoding="utf-8") as f:
                f.write(info + "\n")
            print("\n".join(info.split(",")))
            print(
                "\n\n---------------------------------------------------------------------------------\n"
            )

        # 翻页
        i += 1


def main():
    config_path = ".torextrader/gravity.yaml"
    with open(config_path, "r") as file:
        file_data = file.read()
    config = yaml.safe_load(file_data)
    headers = get_headers(config)
    params = get_params(config)
    get_article_list(headers, params)


if __name__ == "__main__":
    main()
