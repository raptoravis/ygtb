import sys
from pathlib import Path as PPath

import pandas as pd
import pandas_ta_classic as ta
import plotly.express as px

# 1. <.parent> contains this file1.py
# 2. <.parent.parent> contains folder1
# 3. <.parent.parent.parent> contains Project
sys.path.append(str(PPath(__file__).parent.parent))

from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# https://www.youtube.com/watch?v=lXJclKmQR-k&list=PLnSVMZC68_e48lA4aRYL1yHYZ9nEq9AiH&index=6

# Binance data can be found here: https://data.binance.vision/?prefix=data/spot/monthly/klines/BTCUSDT/
df = pd.read_csv(
    "_data/BTCUSDT-1m-2025-YTD.csv",
    usecols=[0, 1, 2, 3, 4],
    names=["Date", "Open", "High", "Low", "Close"],
)
df["Date"] = pd.to_datetime(df["Date"])
df.set_index("Date", inplace=True)
print(df)


class RsiOscillator(Strategy):
    upper_bound = 25
    lower_bound = 75
    rsi_window = 23

    # Do as much initial computation as possible
    def init(self):
        self.rsi = self.I(ta.rsi, self.data.Close.s, length=self.rsi_window)

    # Step through bars one by one
    # Note that multiple buys are a thing here
    def next(self):
        if self.position and crossover(self.rsi, self.upper_bound):
            self.position.close()

        elif crossover(self.lower_bound, self.rsi):
            self.buy(size=1)


"""
def optim_func(series):
    if series["# Trades"] < 20:
        return -1
    else:
        return series["Equity Final [%]"]


stats = bt.optimize(
        upper_bound = range(50,85,5),
        lower_bound = range(15,45,5),
        rsi_window = range(10,30,1),
        maximize=optim_func,
        #maximize='Win Rate [%]',
        constraint = lambda param: param.lower_bound < param.upper_bound)
"""

returns = []
minutes_in_day = 24 * 60
for x in range(30 * minutes_in_day, len(df) + 1, minutes_in_day):
    bt = Backtest(
        df.iloc[x - 30 * minutes_in_day : x],
        RsiOscillator,
        cash=10_000_000,
        commission=0.002,
    )

    stats = bt.run(upper_bound=75, lower_bound=25, rsi_window=23)

    print(stats["Return [%]"])
    returns.append(stats["Return [%]"])

fig = px.box(returns, points="all")
fig.update_layout(
    xaxis_title="Strategy",
    yaxis_title="Returns (%)",
)
fig.show()
