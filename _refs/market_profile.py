import warnings
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from bokeh.layouts import column, row
from bokeh.models import Button, ColumnDataSource, DataTable, Div, HoverTool, Select, Slider, Span, TableColumn
from bokeh.palettes import Plasma256, Viridis256
from bokeh.plotting import figure, output_file, save, show
from bokeh.transform import linear_cmap

warnings.filterwarnings("ignore")


def generate_sample_data(days=30, ticker="SPY"):
    """
    生成示例市场数据用于演示。

    使用随机游走模型生成模拟的OHLCV（开盘、最高、最低、收盘、成交量）数据，
    适用于在没有实时数据源时进行功能测试和演示。

    Args:
        days: 生成数据的天数，默认30天
        ticker: 股票代码标识，默认"SPY"

    Returns:
        tuple: (DataFrame, ticker)
            - DataFrame: 包含以下列的数据框：
                - Date: 日期时间索引（小时级别）
                - Open: 开盘价
                - High: 最高价
                - Low: 最低价
                - Close: 收盘价
                - Volume: 成交量（对数正态分布）
            - ticker: 股票代码字符串

    Note:
        - 使用固定随机种子(42)确保结果可复现
        - 价格基于4500的基准价格，带有轻微上升趋势
        - 成交量使用对数正态分布模拟真实市场的成交量分布特征
    """
    np.random.seed(42)

    # 生成日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq="1H")

    # 生成价格数据
    n_periods = len(dates)
    base_price = 4500

    # 随机游走生成价格
    prices = [base_price]
    for i in range(1, n_periods):
        change = np.random.normal(0, 5)
        prices.append(prices[-1] + change)

    # 添加一些趋势
    trend = np.linspace(0, 100, n_periods)
    prices = [p + t * 0.2 for p, t in zip(prices, trend)]

    # 生成成交量
    volumes = np.random.lognormal(mean=6, sigma=0.8, size=n_periods).astype(int)

    # 创建DataFrame
    df = pd.DataFrame(
        {
            "Date": dates,
            "Open": [p - np.random.uniform(0, 2) for p in prices],
            "High": [p + np.random.uniform(1, 3) for p in prices],
            "Low": [p - np.random.uniform(1, 3) for p in prices],
            "Close": prices,
            "Volume": volumes,
        }
    )

    return df, ticker


def calculate_volume_profile(df, price_bins=20):
    """
    计算成交量分布（Volume Profile）。

    Volume Profile 是一种技术分析工具，显示在不同价格水平上的成交量分布。
    它帮助交易者识别：
    - 高成交量节点（HVN）：价格在此处有大量交易，通常形成支撑/阻力
    - 低成交量节点（LVN）：价格快速穿越的区域，可能成为突破点
    - 控制点（POC）：成交量最大的价格水平

    算法原理：
    1. 对于每根K线，计算其价格范围（High - Low）
    2. 将该K线的成交量均匀分配到价格范围内的各个价格水平
    3. 累加所有K线在各价格水平的成交量，得到完整的成交量分布

    成交量分配逻辑：
    - 如果K线没有价格波动（High == Low），所有成交量分配给收盘价
    - 否则，将价格范围分成 price_bins 个区间，成交量均匀分配
    - 这种方法假设成交量在K线的价格范围内均匀分布（简化假设）

    Args:
        df: 包含OHLCV数据的DataFrame，必须包含 High, Low, Close, Volume 列
        price_bins: 每根K线价格范围内的分割数量，值越大精度越高，默认20

    Returns:
        DataFrame: 包含以下列：
            - Price: 价格水平
            - Volume: 该价格水平的累计成交量

    Example:
        >>> volume_profile = calculate_volume_profile(df, price_bins=30)
        >>> poc_price = volume_profile.loc[volume_profile["Volume"].idxmax(), "Price"]
    """
    # 计算每个K线的价格范围
    df["PriceRange"] = df["High"] - df["Low"]

    # 为每个价格水平分配成交量
    volume_by_price = {}

    for idx, r in df.iterrows():
        if r["PriceRange"] == 0:
            # 如果价格没有变化，将所有成交量分配给收盘价
            price_level = round(r["Close"], 2)
            volume_by_price[price_level] = volume_by_price.get(price_level, 0) + r["Volume"]
        else:
            # 假设成交量在高低价格之间均匀分布
            price_step = r["PriceRange"] / price_bins
            volume_per_step = r["Volume"] / price_bins

            for i in range(price_bins):
                price_level = round(r["Low"] + i * price_step, 2)
                volume_by_price[price_level] = volume_by_price.get(price_level, 0) + volume_per_step

    # 转换为DataFrame
    volume_profile = pd.DataFrame(list(volume_by_price.items()), columns=["Price", "Volume"])
    volume_profile = volume_profile.sort_values("Price")

    return volume_profile


def calculate_market_profile(df, time_slices=24):
    """
    计算市场概况（Market Profile / TPO - Time Price Opportunity）。

    Market Profile 由芝加哥期货交易所（CBOT）的 Peter Steidlmayer 在1980年代开发，
    是一种将价格和时间结合分析的方法。TPO 表示价格在特定时间段内被"访问"的次数。

    核心概念：
    - TPO（Time Price Opportunity）：价格在某时间段内出现的机会
    - 初始平衡区（Initial Balance）：开盘后第一小时的价格范围
    - 价值区域（Value Area）：包含约70%TPO的价格范围
    - 控制点（POC）：TPO最多的价格水平

    算法原理：
    1. 将价格范围分成30个水平区间
    2. 将时间分成24个小时段（或指定的时间片数）
    3. 对于每根K线，在其价格范围内的所有价格水平上，对应时间段的TPO计数+1
    4. 生成一个 价格×时间 的矩阵，显示每个价格在每个时间段的活跃程度

    交易应用：
    - 价格倾向于在高TPO区域停留（价值区域）
    - 价格快速穿越低TPO区域
    - POC 常作为日内支撑/阻力参考

    Args:
        df: 包含OHLCV数据的DataFrame，必须包含 Date, High, Low 列
        time_slices: 时间分片数量，默认24（按小时）

    Returns:
        DataFrame: TPO矩阵
            - index: 价格水平
            - columns: 时间标签（如 "00:00", "01:00", ...）
            - values: 该价格在该时间段的TPO计数
    """
    # 确定价格区间
    min_price = df["Low"].min()
    max_price = df["High"].max()

    # 创建价格区间
    price_step = (max_price - min_price) / 30
    price_levels = np.arange(min_price, max_price + price_step, price_step)

    # 确定时间区间
    df["Hour"] = pd.to_datetime(df["Date"]).dt.hour
    time_labels = [f"{h:02d}:00" for h in range(time_slices)]

    # 初始化TPO矩阵
    tpo_matrix = pd.DataFrame(0, index=price_levels, columns=time_labels)

    # 填充TPO矩阵
    for idx, r in df.iterrows():
        # 确定时间标签
        hour = int(pd.to_datetime(r["Date"]).hour)
        time_label = f"{hour:02d}:00"

        # 确定价格范围
        low_price = r["Low"]
        high_price = r["High"]

        # 找到价格区间内的所有价格水平
        price_mask = (price_levels >= low_price) & (price_levels <= high_price)
        price_in_range = price_levels[price_mask]

        # 增加这些价格水平的TPO计数
        for price in price_in_range:
            tpo_matrix.loc[price, time_label] += 1

    return tpo_matrix


def create_visualization(show_tpo=True):
    """
    创建基于 Bokeh 的交互式市场概况可视化界面。

    生成包含以下组件的完整分析仪表板：

    图表组件：
    1. 价格蜡烛图（p1）：显示OHLC价格走势和20日移动平均线
    2. 成交量分布图（p2）：水平条形图显示各价格水平的成交量
       - 使用 Viridis 色板，颜色深浅表示成交量大小
       - 红色虚线：POC（控制点，成交量最大处）
       - 绿色虚线：VAH（价值区域高点）
       - 蓝色虚线：VAL（价值区域低点）
    3. 市场概况图（p3）：TPO热力图，显示价格-时间分布（可选）
       - 使用 Plasma 色板，颜色表示TPO计数

    关键指标计算：
    - POC（Point of Control）：成交量最大的价格水平
    - VAH（Value Area High）：价值区域上边界
    - VAL（Value Area Low）：价值区域下边界
    - 价值区域：包含70%总成交量的价格范围

    价值区域计算方法：
    1. 按成交量从大到小排序各价格水平
    2. 累加成交量直到达到总成交量的70%
    3. 这些价格水平的最高点为VAH，最低点为VAL

    Args:
        show_tpo: 是否显示市场概况（TPO）图表，默认True

    Returns:
        bokeh.layouts.column: 完整的可视化布局，可直接用于 show() 或 save()

    Note:
        - 控制面板的Python回调在静态HTML中不工作，需要Bokeh Server
        - 所有图表共享Y轴范围，支持联动缩放
    """
    # 获取数据
    df, ticker = generate_sample_data(30, "SPY")

    # 计算成交量分布
    volume_profile = calculate_volume_profile(df)

    # 计算市场概况（仅在需要显示时计算）
    market_profile = None
    market_profile_melted = None
    market_profile_source = None
    if show_tpo:
        market_profile = calculate_market_profile(df)
        market_profile_melted = market_profile.reset_index().melt(id_vars="index", var_name="Time", value_name="Count")
        market_profile_melted.columns = ["Price", "Time", "Count"]
        market_profile_melted["Alpha"] = market_profile_melted["Count"] / market_profile_melted["Count"].max()
        market_profile_source = ColumnDataSource(market_profile_melted)

    # 准备数据源
    volume_source = ColumnDataSource(volume_profile)

    # 价格时间序列数据
    price_source = ColumnDataSource(df)

    # 创建主图表
    p1 = figure(
        title=f"{ticker} - 价格与成交量分布",
        width=1000,
        height=400,
        x_axis_type="datetime",
        tools="pan,wheel_zoom,box_zoom,reset,save",
    )

    # 绘制价格蜡烛图
    inc = df["Close"] > df["Open"]
    dec = df["Open"] > df["Close"]

    # 蜡烛图
    p1.segment(df["Date"], df["High"], df["Date"], df["Low"], color="black")
    p1.vbar(df["Date"][inc], 0.5, df["Open"][inc], df["Close"][inc], fill_color="#06982d", line_color="black")
    p1.vbar(df["Date"][dec], 0.5, df["Open"][dec], df["Close"][dec], fill_color="#ae1325", line_color="black")

    # 添加移动平均线
    df["SMA20"] = df["Close"].rolling(window=20).mean()
    p1.line(df["Date"], df["SMA20"], line_width=2, color="blue", legend_label="SMA 20")

    p1.legend.location = "top_left"
    p1.xaxis.axis_label = "日期"
    p1.yaxis.axis_label = "价格"
    p1.add_tools(
        HoverTool(
            tooltips=[
                ("日期", "@Date{%F %H:%M}"),
                ("开盘", "@Open{0.2f}"),
                ("最高", "@High{0.2f}"),
                ("最低", "@Low{0.2f}"),
                ("收盘", "@Close{0.2f}"),
                ("成交量", "@Volume{0,0}"),
            ],
            formatters={"@Date": "datetime"},
        )
    )

    # 计算POC（需要先计算volume_profile）
    volume_profile["normalized_volume"] = volume_profile["Volume"] / volume_profile["Volume"].max()
    poc_price = volume_profile.loc[volume_profile["Volume"].idxmax(), "Price"]

    # 在价格图上添加POC线（与成交量分布图同步）
    poc_line_p1 = Span(location=poc_price, dimension="width", line_color="red", line_width=2, line_dash="dashed")
    p1.add_layout(poc_line_p1)

    # 成交量分布图
    p2 = figure(
        title="成交量分布 (Volume Profile)",
        width=300,
        height=400,
        y_range=p1.y_range,
        tools="pan,wheel_zoom,box_zoom,reset,save",
    )

    # 创建颜色映射
    # max_volume = volume_profile["Volume"].max()
    volume_source = ColumnDataSource(volume_profile)

    mapper = linear_cmap(field_name="normalized_volume", palette=Viridis256, low=0, high=1)

    p2.hbar(
        y="Price",
        right="Volume",
        height=0.8,
        source=volume_source,
        fill_color=mapper,
        line_color="black",
        line_width=0.5,
    )

    # 添加价值区域线 (POC - 成交量最高点)
    poc_line = Span(location=poc_price, dimension="width", line_color="red", line_width=2, line_dash="dashed")
    p2.add_layout(poc_line)

    # 计算VAH和VAL (价值区域高点和低点)
    total_volume = volume_profile["Volume"].sum()
    volume_sorted = volume_profile.sort_values("Volume", ascending=False)
    cumulative_volume = 0
    value_area_prices = []

    for idx, r in volume_sorted.iterrows():
        cumulative_volume += r["Volume"]
        value_area_prices.append(r["Price"])
        if cumulative_volume >= total_volume * 0.7:  # 70%成交量区域
            break

    vah = max(value_area_prices)
    val = min(value_area_prices)

    vah_line = Span(location=vah, dimension="width", line_color="green", line_width=2, line_dash="dashed")
    val_line = Span(location=val, dimension="width", line_color="blue", line_width=2, line_dash="dashed")
    p2.add_layout(vah_line)
    p2.add_layout(val_line)

    p2.xaxis.axis_label = "成交量"
    p2.yaxis.axis_label = "价格"
    p2.add_tools(
        HoverTool(tooltips=[("价格", "@Price{0.2f}"), ("成交量", "@Volume{0,0}"), ("占比", "@normalized_volume{0.0%}")])
    )

    # 市场概况图 (TPO图) - 根据条件显示
    p3 = None
    poc_line2 = None
    if show_tpo:
        p3 = figure(
            title="市场概况 (Market Profile / TPO)",
            width=600,
            height=400,
            y_range=p1.y_range,
            x_range=list(market_profile.columns),
            tools="pan,wheel_zoom,box_zoom,reset,save",
        )

        # 为不同TPO计数创建颜色映射
        mapper_tpo = linear_cmap(
            field_name="Count",
            palette=Plasma256,
            low=market_profile_melted["Count"].min(),
            high=market_profile_melted["Count"].max(),
        )

        # 绘制矩形表示TPO
        p3.rect(
            x="Time",
            y="Price",
            width=0.9,
            height=(market_profile.index[1] - market_profile.index[0]) * 0.9,
            source=market_profile_source,
            fill_color=mapper_tpo,
            line_color=None,
            alpha="Alpha",
        )

        # 添加POC线
        poc_line2 = Span(location=poc_price, dimension="width", line_color="red", line_width=2, line_dash="dashed")
        p3.add_layout(poc_line2)

        p3.xaxis.axis_label = "时间"
        p3.yaxis.axis_label = "价格"
        p3.xaxis.major_label_orientation = 45

        p3.add_tools(HoverTool(tooltips=[("时间", "@Time"), ("价格", "@Price{0.2f}"), ("TPO计数", "@Count")]))

    # 创建信息面板
    info_div = Div(
        text=f"""
    <div style="font-family: Arial, sans-serif; padding: 10px; background-color: #f5f5f5; border-radius: 5px;">
        <h3>市场概况分析</h3>
        <p><b>标的:</b> {ticker}</p>
        <p><b>数据期间:</b> {df["Date"].iloc[0].strftime("%Y-%m-%d")} 到 {df["Date"].iloc[-1].strftime("%Y-%m-%d")}</p>
        <p><b>控制点(POC):</b> {poc_price:.2f} (成交量最大处)</p>
        <p><b>价值区域高点(VAH):</b> {vah:.2f}</p>
        <p><b>价值区域低点(VAL):</b> {val:.2f}</p>
        <p><b>价值区域宽度:</b> {vah - val:.2f} ({(vah - val) / poc_price * 100:.2f}%)</p>
        <p><b>总成交量:</b> {int(df["Volume"].sum()):,}</p>
    </div>
    """,
        width=300,
        height=200,
    )

    # 创建数据表格
    summary_data = {
        "指标": [
            "POC (控制点)",
            "VAH (价值区域高点)",
            "VAL (价值区域低点)",
            "价值区域宽度",
            "总成交量",
            "价格区间",
            "数据点数",
        ],
        "数值": [
            f"{poc_price:.2f}",
            f"{vah:.2f}",
            f"{val:.2f}",
            f"{vah - val:.2f}",
            f"{int(df['Volume'].sum()):,}",
            f"{df['Low'].min():.2f} - {df['High'].max():.2f}",
            len(df),
        ],
    }
    summary_df = pd.DataFrame(summary_data)
    summary_source = ColumnDataSource(summary_df)

    columns = [TableColumn(field="指标", title="指标"), TableColumn(field="数值", title="数值")]
    data_table = DataTable(source=summary_source, columns=columns, width=300, height=200, index_position=None)

    # 创建控制面板
    ticker_select = Select(
        title="选择标的:", value="SPY", options=["SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "TSLA", "BTC-USD"]
    )

    period_select = Select(title="选择周期:", value="1mo", options=["5d", "1mo", "3mo", "6mo", "1y"])

    price_bins_slider = Slider(title="价格区间数量:", start=10, end=50, value=20, step=5)

    data_source_select = Select(title="数据源:", value="sample", options=[("sample", "示例数据"), ("real", "实时数据")])

    def update_data():
        new_df, new_ticker = generate_sample_data(
            days=30 if period_select.value == "1mo" else 90, ticker=ticker_select.value
        )

        # 重新计算成交量分布
        new_volume_profile = calculate_volume_profile(new_df, price_bins_slider.value)

        # 更新数据源
        price_source.data = ColumnDataSource.from_df(new_df)

        # 更新成交量分布
        max_volume = new_volume_profile["Volume"].max()
        new_volume_profile["normalized_volume"] = new_volume_profile["Volume"] / max_volume
        volume_source.data = ColumnDataSource.from_df(new_volume_profile)

        # 更新市场概况（仅在显示时更新）
        if show_tpo:
            new_market_profile = calculate_market_profile(new_df)
            new_market_profile_melted = new_market_profile.reset_index().melt(
                id_vars="index", var_name="Time", value_name="Count"
            )
            new_market_profile_melted.columns = ["Price", "Time", "Count"]
            new_market_profile_melted["Alpha"] = (
                new_market_profile_melted["Count"] / new_market_profile_melted["Count"].max()
            )
            market_profile_source.data = ColumnDataSource.from_df(new_market_profile_melted)

        # 更新图表范围
        p1.y_range.start = new_df["Low"].min() * 0.99
        p1.y_range.end = new_df["High"].max() * 1.01

        # 更新POC线（同步更新价格图和成交量分布图上的POC线）
        poc_price = new_volume_profile.loc[new_volume_profile["Volume"].idxmax(), "Price"]
        poc_line.location = poc_price
        poc_line_p1.location = poc_price
        if poc_line2:
            poc_line2.location = poc_price

        # 更新信息面板
        total_volume = new_volume_profile["Volume"].sum()
        volume_sorted = new_volume_profile.sort_values("Volume", ascending=False)
        cumulative_volume = 0
        value_area_prices = []

        for idx, r in volume_sorted.iterrows():
            cumulative_volume += r["Volume"]
            value_area_prices.append(r["Price"])
            if cumulative_volume >= total_volume * 0.7:
                break

        vah = max(value_area_prices)
        val = min(value_area_prices)

        dt = new_df["Date"].iloc[-1].strftime("%Y-%m-%d")
        info_div.text = f"""
        <div style="font-family: Arial, sans-serif; padding: 10px; background-color: #f5f5f5; border-radius: 5px;">
            <h3>市场概况分析</h3>
            <p><b>标的:</b> {new_ticker}</p>
            <p><b>数据期间:</b> {new_df["Date"].iloc[0].strftime("%Y-%m-%d")} 到 {dt}</p>
            <p><b>控制点(POC):</b> {poc_price:.2f} (成交量最大处)</p>
            <p><b>价值区域高点(VAH):</b> {vah:.2f}</p>
            <p><b>价值区域低点(VAL):</b> {val:.2f}</p>
            <p><b>价值区域宽度:</b> {vah - val:.2f} ({(vah - val) / poc_price * 100:.2f}%)</p>
            <p><b>总成交量:</b> {int(new_df["Volume"].sum()):,}</p>
        </div>
        """

        # 更新表格
        new_summary_data = {
            "指标": [
                "POC (控制点)",
                "VAH (价值区域高点)",
                "VAL (价值区域低点)",
                "价值区域宽度",
                "总成交量",
                "价格区间",
                "数据点数",
            ],
            "数值": [
                f"{poc_price:.2f}",
                f"{vah:.2f}",
                f"{val:.2f}",
                f"{vah - val:.2f}",
                f"{int(new_df['Volume'].sum()):,}",
                f"{new_df['Low'].min():.2f} - {new_df['High'].max():.2f}",
                len(new_df),
            ],
        }
        new_summary_df = pd.DataFrame(new_summary_data)
        summary_source.data = ColumnDataSource.from_df(new_summary_df)

    # 添加更新按钮
    update_button = Button(label="更新图表", button_type="success")
    update_button.on_click(update_data)

    # 布局控制面板
    controls = column(
        Div(text="<h3>控制面板</h3>"),
        ticker_select,
        period_select,
        data_source_select,
        price_bins_slider,
        update_button,
        info_div,
        data_table,
    )

    # 主布局 - 根据是否显示TPO调整布局
    if show_tpo:
        charts = row(column(p1, p3), p2)
    else:
        charts = row(p1, p2)
    layout = column(Div(text="<h1>基于Volume Profile的Market Profile分析</h1>"), row(charts, controls))

    return layout


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="市场概况可视化工具")
    parser.add_argument("--show-tpo", action="store_true", default=False, help="是否显示TPO市场概况图（默认不显示）")
    args = parser.parse_args()

    # 创建并显示可视化
    layout = create_visualization(show_tpo=args.show_tpo)

    # 保存为HTML文件
    output_file("market_profile_visualization.html")
    save(layout)
    print("可视化已保存为 'market_profile_visualization.html'")

    # 显示可视化
    show(layout)
