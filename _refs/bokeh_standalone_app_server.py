import asyncio
import os
import time
from threading import Lock, Thread
from time import perf_counter

import tornado.ioloop
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.document import Document
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Slider
from bokeh.plotting import figure
from bokeh.server.server import Server
from bokeh.themes import Theme
from bokeh.util.browser import view
from bokeh_sampledata.sea_surface_temperature import sea_surface_temperature


class Webapp:
    def __init__(
        self,
        model_factory_fnc,
        on_session_destroyed=None,
        address="localhost",
        port=5006,
        autostart=True,
    ):
        self._model_factory_fnc = model_factory_fnc
        self._on_session_destroyed = on_session_destroyed
        self._address = address
        self._port = port
        self._autostart = autostart

    def start(self, ioloop=None):
        """
        Serves a backtrader result as a Bokeh application running on
        a web server
        """

        def make_document(doc: Document):
            if self._on_session_destroyed is not None:
                doc.on_session_destroyed(self._on_session_destroyed)

            model = self._model_factory_fnc(doc)
            doc.add_root(model)

            path = os.path.dirname(os.path.abspath(__file__))
            fn = os.path.join(path, "theme.yaml")
            doc.theme = Theme(filename=fn)

            return doc

        self._run_server(
            make_document,
            ioloop=ioloop,
            address=self._address,
            port=self._port,
            autostart=self._autostart,
        )

    @staticmethod
    def _run_server(
        fnc_make_document,
        ioloop=None,
        address="localhost",
        port=5006,
        autostart=True,
    ):
        """
        Runs a Bokeh webserver application. Documents will be created using
        fnc_make_document
        """
        handler = FunctionHandler(fnc_make_document)
        app = Application(handler)

        apps = {"/": app}
        display_address = address if address != "*" else "localhost"
        origin = [f"{address}:{port}" if address != "*" else address]
        server = Server(apps, port=port, io_loop=ioloop, allow_websocket_origin=origin)
        if autostart:
            print(f"Browser is launching at http://{display_address}:{port}")
            view(f"http://{display_address}:{port}")
        else:
            print(f"Open browser at http://{display_address}:{port}")
        if ioloop is None:
            server.run_until_shutdown()
        else:
            server.start()
            ioloop.start()


class LiveClient:
    def __init__(self, doc):
        self.doc = doc

        if doc:
            df = sea_surface_temperature.copy()
            # df["time"] = df.index.to_series().apply(lambda dt: dt.to_pydatetime())
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

            slider = Slider(
                start=0, end=30, value=0, step=1, title="Smoothing by N Days"
            )
            slider.on_change("value", callback)
            self.model = column(slider, plot)


class LivePlotter:
    def __init__(self, iplot=True, autostart=True, **kwargs):
        self._webapp = Webapp(
            self._app_cb_build_root_model,
            on_session_destroyed=self._on_session_destroyed,
            autostart=autostart,
        )
        self._lock = Lock()
        self._clients = {}

        self.started = False
        self.stopped = False

    def _on_session_destroyed(self, session_context):
        with self._lock:
            self._clients[session_context.id].stop()
            del self._clients[session_context.id]

    def _t_server(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = tornado.ioloop.IOLoop.current()
        self._webapp.start(loop)

    def _app_cb_build_root_model(self, doc):
        self.end_perf = perf_counter()
        elapsed = self.end_perf - self.start_perf
        print(f"Since Start {elapsed}")

        client = LiveClient(doc)
        with self._lock:
            self._clients[doc.session_context.id] = client

        end = perf_counter()
        elapsed = end - self.end_perf
        print(f"_app_cb_build_root_model {elapsed}")
        self.end_perf = end

        return client.model

    def start(self):
        """
        Start from backtrader
        """
        self.start_perf = perf_counter()
        if not self.started:
            self.started = True

            t = Thread(target=self._t_server)
            t.daemon = True
            t.start()


if __name__ == "__main__":
    live_potter = LivePlotter()

    live_potter.start()

    time.sleep(100 * 1000.0)
