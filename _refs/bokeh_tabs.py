from datetime import datetime

import numpy as np
import requests
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.document import Document
from bokeh.models import ColumnDataSource, TabPanel, Tabs
from bokeh.plotting import figure
from bokeh.server.server import Server
from tornado.web import RequestHandler

from bbt.base.logger import glog_error, glog_info


class ReconnectHandler(RequestHandler):
    """处理重新连接的请求"""

    def get(self):
        glog_info("收到重新连接请求")
        self.write("连接已重新建立")


def make_document(doc: Document):
    # 创建三个不同的数据源
    close_source = ColumnDataSource(data={"Close": [], "DateTime": []})
    moving_avg_source = ColumnDataSource(data={"MA": [], "DateTime": []})
    volatility_source = ColumnDataSource(data={"Volatility": [], "DateTime": []})

    # 存储最近10个价格点用于计算移动平均和波动率
    price_history = []

    # 创建三个图表
    close_fig = figure(
        x_axis_type="datetime",
        width=950,
        height=400,
        tooltips=[("Close", "@Close")],
        title="Bitcoin Close Price (实时更新)",
    )
    close_fig.line(
        x="DateTime",
        y="Close",
        line_color="tomato",
        line_width=3.0,
        source=close_source,
    )
    close_fig.xaxis.axis_label = "时间"
    close_fig.yaxis.axis_label = "价格 ($)"

    ma_fig = figure(
        x_axis_type="datetime",
        width=950,
        height=400,
        tooltips=[("5点移动平均", "@MA")],
        title="比特币价格5点移动平均",
    )
    ma_fig.line(
        x="DateTime",
        y="MA",
        line_color="navy",
        line_width=3.0,
        source=moving_avg_source,
    )
    ma_fig.xaxis.axis_label = "时间"
    ma_fig.yaxis.axis_label = "移动平均 ($)"

    vol_fig = figure(
        x_axis_type="datetime",
        width=950,
        height=400,
        tooltips=[("波动率", "@Volatility")],
        title="比特币价格波动率 (标准差)",
    )
    vol_fig.line(
        x="DateTime",
        y="Volatility",
        line_color="green",
        line_width=3.0,
        source=volatility_source,
    )
    vol_fig.xaxis.axis_label = "时间"
    vol_fig.yaxis.axis_label = "波动率"

    # 创建三个TabPanel
    tab1 = TabPanel(child=close_fig, title="实时价格")
    tab2 = TabPanel(child=ma_fig, title="移动平均")
    tab3 = TabPanel(child=vol_fig, title="价格波动")

    # 将所有Tab组合在一起
    tabs = Tabs(tabs=[tab1, tab2, tab3])

    # 定义回调函数
    def update_chart():
        try:
            resp = requests.get(
                "https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD",
                timeout=5,
            )
            hist_data = resp.json()
            current_price = hist_data["USD"]
            current_time = datetime.now()

            # 更新价格历史记录
            price_history.append(current_price)
            if len(price_history) > 10:
                price_history.pop(0)

            # 更新实时价格图表
            close_source.stream({"Close": [current_price], "DateTime": [current_time]})

            # 如果有足够的数据点，计算移动平均和波动率
            if len(price_history) >= 5:
                ma = np.mean(price_history[-5:])
                volatility = np.std(price_history[-5:])

                moving_avg_source.stream({"MA": [ma], "DateTime": [current_time]})

                volatility_source.stream({"Volatility": [volatility], "DateTime": [current_time]})
        except Exception as e:
            glog_error(f"更新图表时出错: {str(e)}")

    # 添加文档加载时的处理
    def on_document_ready(event):
        glog_info("文档已加载")
        doc.add_periodic_callback(update_chart, 200)

    # 只使用支持的事件
    doc.on_event("document_ready", on_document_ready)

    doc.add_root(tabs)


# 创建Bokeh应用
apps = {"/": Application(FunctionHandler(make_document))}

# 启动服务器
server = Server(apps, port=5006, extra_patterns=[("/reconnect", ReconnectHandler)])

glog_info("服务器正在启动...")
server.start()
glog_info("多Tab比特币价格监控仪表板已启动: http://localhost:5006/")

try:
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()
except KeyboardInterrupt:
    glog_info("正在停止服务器...")
    server.io_loop.stop()
    glog_info("服务器已停止")
