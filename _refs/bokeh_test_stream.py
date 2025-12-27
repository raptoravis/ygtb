# bokeh serve --show main.py
# https://www.youtube.com/watch?v=TKrZMO_Zc4c&t=646sc
# https://coderzcolumn.com/tutorials/data-science/bokeh-work-with-realtime-streaming-data
from datetime import datetime

import bokeh
import requests
from bokeh.io import curdoc
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

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
    global data_source
    resp = requests.get(
        "https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD"
    )
    hist_data = resp.json()
    new_row = {
        "Close": [hist_data["USD"]],
        "DateTime": [
            datetime.now(),
        ],
    }
    data_source.stream(new_row)


print(f"bokeh version {bokeh.__version__}")

curdoc().add_periodic_callback(update_chart, 200)

curdoc().add_root(fig)
