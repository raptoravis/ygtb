from datetime import timedelta

import dash_bootstrap_components as dbc
import pandas as pd
import pandas_ta_classic as ta
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html
from plotly.subplots import make_subplots

# https://www.youtube.com/watch?v=5GhiWjNygkY


# https://data.binance.vision/?prefix=data/spot/monthly/klines/ETHUSDT/1h/
def get_ohlc_df(csv_file: str):
    ohlc_df = pd.read_csv(
        csv_file,
        names=[
            "opentime",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "timestamp",
            "assetvolume",
            "trades",
            "tbbasevolume",
            "tbquotevolume",
            "ignore",
        ],
    )
    ohlc_df["opentime"] = pd.to_datetime(ohlc_df.opentime, errors="coerce")
    ohlc_df["timestamp"] = pd.to_datetime(ohlc_df.timestamp, errors="coerce")
    ohlc_df["rsi"] = ta.rsi(ohlc_df.close)
    ohlc_df = ohlc_df.set_index("timestamp")
    return ohlc_df


def generate_trades_df(ohlc_df: pd.DataFrame):
    rsi_upper_threshold = 70
    rsi_lower_threshold = 30

    trade_value = 100
    trades = []

    current_trade = {}

    for i in range(len(ohlc_df) - 1):
        if ohlc_df.iloc[i].rsi > rsi_upper_threshold and len(current_trade) != 0:
            trades.append(
                {
                    "entry_price": current_trade["entry_price"],
                    "entry_time": current_trade["entry_time"],
                    "trade_size": current_trade["remaining_size"],
                    "exit_price": ohlc_df.iloc[i + 1].open,
                    "exit_time": ohlc_df.iloc[i + 1].name,
                    "profit_pct": (
                        ohlc_df.iloc[i + 1].open / current_trade["entry_price"]
                    )
                    - 1,
                }
            )

            current_trade = {}

        elif ohlc_df.iloc[i].rsi < rsi_lower_threshold and len(current_trade) == 0:
            current_trade["entry_price"] = ohlc_df.iloc[i + 1].open
            current_trade["entry_time"] = ohlc_df.iloc[i + 1].name
            current_trade["initial_size"] = trade_value / current_trade["entry_price"]
            current_trade["remaining_size"] = current_trade["initial_size"]

    trades_df = pd.DataFrame(trades)
    return trades_df


def generate_plot(ohlc_df: pd.DataFrame, trades: pd.DataFrame):
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.75, 0.25],
        vertical_spacing=0.1,
    )

    fig.add_trace(
        go.Candlestick(
            x=ohlc_df.index,
            open=ohlc_df.open,
            high=ohlc_df.high,
            low=ohlc_df.low,
            close=ohlc_df.close,
            # increasing_line_color="rgba(107,107,107,0.8)",
            # decreasing_line_color="rgba(210,210,210,0.8)",
            name="OHLC",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=trades.entry_time,
            y=trades.entry_price,
            mode="markers",
            customdata=trades,
            marker_symbol="diamond-dot",
            marker_size=13,
            marker_line_width=2,
            marker_line_color="rgba(0,0,0,0.7)",
            marker_color="rgba(0,255,0,0.7)",
            hovertemplate="Entry Time: %{customdata[1]}<br>"
            + "Entry Price: %{y:.2f}<br>"
            + "Size: %{customdata[2]:.5f}<br>"
            + "Profit_pct: %{customdata[5]:.3f}",
            name="Entries",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=trades.exit_time,
            y=trades.exit_price,
            mode="markers",
            customdata=trades,
            marker_symbol="diamond-dot",
            marker_size=13,
            marker_line_width=2,
            marker_line_color="rgba(0,0,0,0.7)",
            marker_color="rgba(255,0,0,0.7)",
            hovertemplate="Exit Time: %{customdata[4]}<br>"
            + "Exit Price: %{y:.2f}<br>"
            + "Size: %{customdata[2]:.5f}<br>"
            + "Profit_pct: %{customdata[5]:.3f}",
            name="Exits",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(go.Scatter(x=ohlc_df.index, y=ohlc_df.rsi, name="RSI"), row=2, col=1)

    bar_freq = timedelta(hours=0)

    fig.add_trace(
        go.Scatter(
            x=trades.entry_time - bar_freq,
            y=ohlc_df.rsi.loc[trades.entry_time - bar_freq],
            mode="markers",
            customdata=trades,
            marker_symbol="circle-dot",
            marker_size=8,
            marker_line_width=1,
            marker_line_color="rgba(0,0,0,0.7)",
            marker_color="rgba(0,255,0,0.7)",
            name="Indicator Entry",
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=trades.exit_time - bar_freq,
            y=ohlc_df.rsi.loc[trades.exit_time - bar_freq],
            mode="markers",
            customdata=trades,
            marker_symbol="circle-dot",
            marker_size=8,
            marker_line_width=1,
            marker_line_color="rgba(0,0,0,0.7)",
            marker_color="rgba(255,0,0,0.7)",
            name="Indicator Exits",
        ),
        row=2,
        col=1,
    )

    fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark")
    return fig


def create_dropdown(option, id_value):
    return html.Div(
        [
            html.H4(
                id_value.replace("-", " ").upper(),
                # style={"padding": "0px 30px 0px 30px", "text-size": "15px"},
            ),
            dcc.Dropdown(option, id=id_value, value=option[0]),
        ],
        # style={"padding": "0px 30px 0px 30px"},
    )


app = Dash(external_stylesheets=[dbc.themes.CYBORG])

app.layout = html.Div(
    [
        html.Div(
            [
                create_dropdown(
                    ["ETHUSDT-1h-2025-07", "ETHUSDT-1h-2025-08", "ETHUSDT-1h-2025-09"],
                    "data-file-select",
                ),
            ],
            style={
                "display": "flex",
                "margin": "auto",
                # "width": "800px",
                "justify-content": "space-around",
            },
        ),
        dcc.Graph(id="figs"),
        # dcc.Interval(id="interval", interval=2000),
    ]
)


@app.callback(
    Output("figs", "figure"),
    Input("data-file-select", "value"),
)
def update_figure(data_name):
    ohlc_df = get_ohlc_df(csv_file=f"_data/{data_name}.csv")

    # ohlc_df = ohlc_df.iloc[range_values[0] : range_values[1]]

    trades = generate_trades_df(ohlc_df)

    fig = generate_plot(ohlc_df, trades)

    return fig


if __name__ == "__main__":
    app.run(debug=True)
    pass
