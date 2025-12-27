import os

from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.document import Document
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Slider
from bokeh.plotting import figure
from bokeh.server.server import Server
from bokeh.themes import Theme
from bokeh_sampledata.sea_surface_temperature import sea_surface_temperature


def bkapp(doc: Document):
    df = sea_surface_temperature.copy()
    source = ColumnDataSource(data=df)

    plot = figure(
        x_axis_type="datetime",
        y_range=(0, 25),
        y_axis_label="Temperature (Celsius)",
        title="Sea Surface Temperature at 43.18, -70.43",
    )
    plot.line("time", "temperature", source=source)

    def callback(attr, old, new):
        if new == 0:
            data = df
        else:
            data = df.rolling(f"{new}D").mean()
        source.data = ColumnDataSource.from_df(data)

    slider = Slider(start=0, end=30, value=0, step=1, title="Smoothing by N Days")
    slider.on_change("value", callback)

    doc.add_root(column(slider, plot))

    path = os.path.dirname(os.path.abspath(__file__))
    fn = os.path.join(path, "theme.yaml")
    print(fn)
    doc.theme = Theme(filename=fn)


# Setting num_procs here means we can't touch the IOLoop before now, we must
# let Server handle that. If you need to explicitly handle IOLoops then you
# will need to use the lower level BaseServer class.
server = Server({"/": Application(FunctionHandler(bkapp))})

server.start()

if __name__ == "__main__":
    print("Opening Bokeh application on http://localhost:5006/")

    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()
