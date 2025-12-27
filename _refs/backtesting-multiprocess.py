import os
import time
from multiprocessing import Pool

import pandas as pd
import pandas_ta_classic as ta

from backtesting import Backtest, Strategy
from backtesting.lib import crossover


class RsiOscillator(Strategy):
    upper_bound = 70
    lower_bound = 30
    rsi_window = 14

    # Do as much initial computation as possible
    def init(self):
        self.rsi = self.I(ta.rsi, pd.Series(self.data.Close), self.rsi_window)

    # Step through bars one by one
    # Note that multiple buys are a thing here
    def next(self):
        if crossover(self.rsi, self.upper_bound):
            self.position.close()

        elif crossover(self.lower_bound, self.rsi):
            self.buy()


def do_backtest(filename, number):
    print(filename)
    data = pd.read_csv(
        f"data/{filename}",
        names=[
            "OpenTime",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "CloseTime",
            "QuoteVolume",
            "NumTrades",
            "TakerBuyBaseVol",
            "TakerBuyQuoteVol",
            "Unused",
        ],
    )

    data["OpenTime"] = pd.to_datetime(data["OpenTime"], unit="ms")
    data.set_index("OpenTime", inplace=True)

    bt = Backtest(data, RsiOscillator, cash=10_000_000, commission=0.002)
    stats = bt.run()
    sym = filename.split("-")[0]
    return (sym, stats["Return [%]"])


if __name__ == "__main__":
    start_time = time.time()

    # params = [(filename, 10) for filename in os.listdir("data")]
    params = zip(os.listdir("data"), range(len(os.listdir("data"))))

    with Pool() as pool:
        # results = pool.map(do_backtest, os.listdir("data"))
        results = pool.starmap(do_backtest, params)
        pass

    time_taken = time.time() - start_time
    print(f"Took {time_taken} seconds")

    print(results)
