# at the root of this project, bokeh serve --show main.py
from math import pi

import pandas as pd

# from bokeh.io import curdoc
from bokeh.plotting import figure, show

noheaders = False
# Simulate the header row isn't there if noheaders requested
skiprows = 1 if noheaders else 0
header = None if noheaders else 0

data = pd.read_csv(
    "_data/2006-day-001.txt",
    skiprows=skiprows,
    header=header,
    # parse_dates=[0],
    parse_dates=True,
    index_col=0,
)

data.reset_index(inplace=True)

inc = data["Close"] > data["Open"]
dec = data["Open"] > data["Close"]

w = 12 * 60 * 60 * 1000  # trading time in ms

TOOLS = "pan,wheel_zoom,box_zoom,reset,save"

p = figure(
    x_axis_type="datetime", width=1000, tools=TOOLS, title="Pfizer Candlestick Chart"
)
p.xaxis.major_label_orientation = pi / 4
p.grid.grid_line_alpha = 0.3

p.segment(data["Date"], data["High"], data["Date"], data["Low"], color="black")
p.vbar(
    data["Date"][inc],
    w,
    data["Open"][inc],
    data["Close"][inc],
    fill_color="blue",
    line_color="black",
)
p.vbar(
    data["Date"][dec],
    w,
    data["Open"][dec],
    data["Close"][dec],
    fill_color="red",
    line_color="black",
)

# curdoc().add_root(p)
show(p)
