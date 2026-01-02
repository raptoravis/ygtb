import argparse
import os
import time

import pandas as pd
from crewai import Agent, Crew, Process, Task
from crewai.tools import tool
from ddgs import DDGS
from polygon import RESTClient
from termcolor import colored
from utils import get_llm, glog_info

)

POLYGON_API_KEY = os.environ["POLYGON_API_KEY"]


polygon_client = RESTClient(api_key=POLYGON_API_KEY)

_stock_cache = {}


def get_tickers(locale):
    # get exchanges
    exchanges = pd.DataFrame(
        polygon_client.get_exchanges(asset_class="stocks", locale=locale)
    )

    # exchanges MIC for use in list tickers
    # print(exchanges.mic)

    # remove duplicates and remove None
    exchangeList = list(set(exchanges.mic))
    exchangeList.remove(None)

    # get all tickers from all US exchanges
    usTickers = []
    for x in exchangeList:
        # page through response
        for t in polygon_client.list_tickers(
            market="stocks", exchange=x, active=True, limit=1000
        ):
            # add to list
            usTickers.append(t.ticker)
        # print exchange when finished
        print(x)

    # final ticker list
    finalTickerList = set(usTickers)
    glog_info(finalTickerList)
    pass


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


# Define agent creation functions that will be called after LLM is configured
def create_scout_agent(llm):
    return Agent(
        role="金融情报搜集员",
        goal="搜集指定股票 {ticket} 的实时价格、基本面数据以及最近3天的重磅新闻",
        backstory="你是一名顶级市场调查员，擅长从互联网的海量信息中挖掘最关键的金融情报。",
        verbose=True,
        allow_delegation=False,
        tools=[fetch_stock_price, search_tool],
        llm=llm,
    )


def create_analyst_agent(llm):
    return Agent(
        role="资深股票分析师",
        goal="根据搜集到的数据和新闻，分析该股票的投资逻辑和潜在风险",
        backstory="你有20年的华尔街从业经验，擅长透过现象看本质，能敏锐地发现财报和新闻背后的猫腻。",
        verbose=True,
        allow_delegation=False,
        llm=llm,
    )


def create_writer_agent(llm):
    return Agent(
        role="私人投资顾问",
        goal="将分析结果汇总成一篇通俗易懂的中文投资研报，并给出最终建议（买入/卖出/观望）",
        backstory="你的客户是忙碌的上班族，你需要用最简练的语言告诉他们结论，不需要复杂的术语。",
        verbose=True,
        allow_delegation=False,
        llm=llm,
    )


# 定义具体任务 - agents will be assigned after they are created with proper LLM
task1 = Task(
    description="获取 {ticket} 的最新股价数据，并搜索过去48小时关于该公司的重要新闻。",
    expected_output="包含股价数据和3条关键新闻摘要的报告。",
)

task2 = Task(
    description="阅读情报员提供的数据，分析 {ticket} 的当前形势。关注市盈率是否过高？新闻是利好还是利空？",
    expected_output="一份包含基本面分析、情绪分析和风险提示的草稿。",
)

task3 = Task(
    description="""
    根据分析师的草稿，用中文写一份精美的Markdown格式研报。
    包括：1.核心数据 2.新闻摘要 3.深度分析 4.最终操作建议。
    """,
    expected_output="一份完整的中文投资研报。",
)

parser = argparse.ArgumentParser(description="股票分析研报生成工具")
parser.add_argument(
    "-t", "--ticket", type=str, default="NVDA", help="股票代码，例如：NVDA, AAPL"
)
parser.add_argument(
    "--provider",
    type=str,
    default="antigravity",
    choices=["dashscope", "ollama", "antigravity"],
    help="模型提供商: dashscope, ollama 或 antigravity",
)
parser.add_argument(
    "--model",
    type=str,
    default="",
    help="当使用ollama时指定模型名称，例如: codellama, llama3",
)
args = parser.parse_args()


if __name__ == "__main__":
    # Select the appropriate LLM based on provider
    llm = get_llm(provider=args.provider, model=args.model)

    # Create agents with the selected LLM
    scout = create_scout_agent(llm)
    analyst = create_analyst_agent(llm)
    writer = create_writer_agent(llm)

    # Assign agents to tasks
    task1.agent = scout
    task2.agent = analyst
    task3.agent = writer

    # 组队出发！
    crew = Crew(
        agents=[scout, analyst, writer],
        tasks=[task1, task2, task3],
        manager_llm=llm,
        process=Process.sequential,
    )

    glog_info(colored(f"正在分析股票: {args.ticket}", "cyan"))
    glog_info(colored(f"使用模型提供商: {args.provider}", "cyan"))
    if args.provider == "ollama":
        glog_info(colored(f"使用Ollama模型: {args.model}", "cyan"))

    result = crew.kickoff(inputs={"ticket": args.ticket})

    glog_info("################## 研报生成完毕 ##################")
