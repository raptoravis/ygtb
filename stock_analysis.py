import os
import time

from crewai import Agent, Crew, Process, Task
from crewai.tools import tool
from ddgs import DDGS
from dotenv import load_dotenv
from polygon import RESTClient
from termcolor import colored


def glog_info(msg: str):
    print(msg)


HOME_PATH: str = os.path.join(os.path.expanduser("~"), ".bbt")
credentials_env_path = os.path.join(HOME_PATH, "credentials.env")
load_dotenv(credentials_env_path, verbose=True)
glog_info(colored(f"credentials_env_path: {credentials_env_path}"))

# 配置API KEY (这里用OpenAI，国内可用DeepSeek/Moonshot)


DASHSCOPE_API_KEY = os.environ["DASHSCOPE_API_KEY"]
DASHSCOPE_BASE_URL = os.environ["DASHSCOPE_BASE_URL"]
DASHSCOPE_MODEL = os.environ["DASHSCOPE_MODEL"]
POLYGON_API_KEY = os.environ["POLYGON_API_KEY"]

os.environ["OPENAI_API_KEY"] = DASHSCOPE_API_KEY
os.environ["OPENAI_BASE_URL"] = DASHSCOPE_BASE_URL

llm = DASHSCOPE_MODEL
polygon_client = RESTClient(api_key=POLYGON_API_KEY)

_stock_cache = {}


# === 工具 1: 获取股价和基本面 ===
@tool
def fetch_stock_price(ticket: str) -> str:
    """获取股票的实时价格、市值、市盈率等关键基本面数据"""
    if ticket in _stock_cache:
        return str(_stock_cache[ticket])

    time.sleep(2)

    try:
        from datetime import datetime, timedelta

        ticker_data = polygon_client.get_ticker_details(ticket)
        time.sleep(1)

        end_date = datetime.now()
        start_date = end_date - timedelta(days=5)
        aggs = polygon_client.get_aggs(
            ticket,
            1,
            "day",
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
        )

        current_price = None
        if aggs and len(aggs) > 0:
            current_price = aggs[-1].close

        pe_ratio = None
        # try:
        #     financials_url = f"https://api.polygon.io/vX/reference/financials?ticker={ticket}&apikey={POLYGON_API_KEY}"
        #     financials_resp = requests.get(financials_url).json()
        #     if financials_resp.get("results") and len(financials_resp["results"]) > 0:
        #         pe_data = (
        #             financials_resp["results"][0]
        #             .get("financials", {})
        #             .get("income_statement", {})
        #             .get("basics", {})
        #         )
        #         pe_ratio = pe_data.get("price_earnings_ratio")
        # except Exception as ex:
        #     glog_info(ex)
        #     pass

        result = {
            "current_price": current_price,
            "market_cap": ticker_data.market_cap,
            "pe_ratio": pe_ratio,
            "ticker": ticket,
        }
        _stock_cache[ticket] = result
        return str(result)
    except Exception as e:
        if ticket in _stock_cache:
            return f"API受限，使用缓存数据: {_stock_cache[ticket]}"
        return f"获取数据失败: {str(e)}"


# === 工具 2: 搜索最新新闻 ===
@tool
def search_tool(query: str) -> str:
    """使用DuckDuckGo搜索互联网信息"""
    ddgs = DDGS()
    results = list(ddgs.text(query, max_results=5))
    return "\n".join([f"{r['title']}: {r['body']}" for r in results])


# 角色 1：数据猎手
scout = Agent(
    role="金融情报搜集员",
    goal="搜集指定股票 {ticket} 的实时价格、基本面数据以及最近3天的重磅新闻",
    backstory="你是一名顶级市场调查员，擅长从互联网的海量信息中挖掘最关键的金融情报。",
    verbose=True,
    allow_delegation=False,
    tools=[fetch_stock_price, search_tool],
    llm=llm,
)

# 角色 2：高级分析师
# 任务：分析数据，看多还是看空
analyst = Agent(
    role="资深股票分析师",
    goal="根据搜集到的数据和新闻，分析该股票的投资逻辑和潜在风险",
    backstory="你有20年的华尔街从业经验，擅长透过现象看本质，能敏锐地发现财报和新闻背后的猫腻。",
    verbose=True,
    allow_delegation=False,
    llm=llm,
)

# 角色 3：投资顾问
# 任务：写报告
writer = Agent(
    role="私人投资顾问",
    goal="将分析结果汇总成一篇通俗易懂的中文投资研报，并给出最终建议（买入/卖出/观望）",
    backstory="你的客户是忙碌的上班族，你需要用最简练的语言告诉他们结论，不需要复杂的术语。",
    verbose=True,
    allow_delegation=False,
    llm=llm,
)
# 定义具体任务
task1 = Task(
    description="获取 {ticket} 的最新股价数据，并搜索过去48小时关于该公司的重要新闻。",
    agent=scout,
    expected_output="包含股价数据和3条关键新闻摘要的报告。",
)

task2 = Task(
    description="阅读情报员提供的数据，分析 {ticket} 的当前形势。关注市盈率是否过高？新闻是利好还是利空？",
    agent=analyst,
    expected_output="一份包含基本面分析、情绪分析和风险提示的草稿。",
)

task3 = Task(
    description="""
    根据分析师的草稿，用中文写一份精美的Markdown格式研报。
    包括：1.核心数据 2.新闻摘要 3.深度分析 4.最终操作建议。
    """,
    agent=writer,
    expected_output="一份完整的中文投资研报。",
)

# 组队出发！
crew = Crew(
    agents=[scout, analyst, writer],
    tasks=[task1, task2, task3],
    process=Process.sequential,
)

# 比如我们想看：英伟达
result = crew.kickoff(inputs={"ticket": "NVDA"})

glog_info("################## 研报生成完毕 ##################")
# glog_info(str(result))
pass
