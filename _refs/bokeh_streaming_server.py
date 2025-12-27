# main.py
from datetime import datetime

import requests
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.document import Document
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.server.server import Server


def make_document(doc: Document):
    # data source
    data_source = ColumnDataSource(data={"Close": [], "DateTime": []})

    # Create Line Chart
    fig = figure(
        x_axis_type="datetime",
        width=950,
        height=450,
        tooltips=[("Close", "@Close")],
        title="Bitcoin Close Price Live (Every Second)",
    )

    fig.line(
        x="DateTime",
        y="Close",
        line_color="tomato",
        line_width=3.0,
        source=data_source,
    )

    fig.xaxis.axis_label = "Date"
    fig.yaxis.axis_label = "Price ($)"

    # Define Callbacks
    def update_chart():
        resp = requests.get(
            "https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD"
        )
        hist_data = resp.json()
        new_row = {
            "Close": [hist_data["USD"]],
            "DateTime": [datetime.now()],
        }
        data_source.stream(new_row)

    doc.add_periodic_callback(update_chart, 200)
    doc.add_root(fig)
    pass


# 创建 Bokeh 应用
apps = {"/": Application(FunctionHandler(make_document))}

# 启动服务器
server = Server(apps, port=5006)
server.start()

print("Server started at http://localhost:5006/")
server.io_loop.add_callback(server.show, "/")
server.io_loop.start()
