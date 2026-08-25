import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import ta
import time

from concurrent.futures import ThreadPoolExecutor, as_completed


# =========================================================
# ⚙️ PAGE
# =========================================================

st.set_page_config(
    page_title="EGX AI PRO MAX v8.1 - عربي",
    page_icon="📈",
    layout="wide"
)

st.title("🚀 EGX AI PRO MAX v8.1")
st.caption(
    "📊 فحص EGX • Multi-Timeframe • Entry/Target Engine • Risk Management • Real Historical Backtest"
)


# =========================================================
# 📌 EGX100
# =========================================================

EGX100 = [
    "COMI.CA", "MFPC.CA", "PHDC.CA", "ACRI.CA", "ORAS.CA",
    "HRHO.CA", "TMGH.CA", "FWRY.CA", "SWDY.CA", "ETEL.CA",
    "AMOC.CA", "HELI.CA", "EAST.CA", "EFID.CA", "JUFO.CA",
    "ABUK.CA", "ESRS.CA", "EMFD.CA", "MNHD.CA", "CCAP.CA",
    "CICH.CA", "OCDI.CA", "ORHD.CA", "MASR.CA", "TAQA.CA",
    "ADIB.CA", "SAUD.CA", "QNBA.CA", "CIEB.CA", "FAIT.CA",
    "CANAL.CA", "EXPA.CA", "ARCC.CA", "AJWA.CA", "MICH.CA",
    "SUGR.CA", "POUL.CA", "DOMT.CA", "ISMA.CA", "UEGC.CA",
    "AUTO.CA", "OLFI.CA", "SKPC.CA", "AMER.CA", "TALM.CA",
    "ORWE.CA", "SPMD.CA", "ZMID.CA", "MENA.CA", "DAPH.CA",
    "RAYA.CA", "VERT.CA", "EGAL.CA", "ECAP.CA", "MPRC.CA",
    "NCCW.CA", "SCEM.CA", "ARAB.CA", "GDWA.CA", "ELEC.CA",
    "IRON.CA", "ATQA.CA", "EGCH.CA", "KIMA.CA", "ALCN.CA",
    "MPCO.CA", "ELSH.CA", "MEPA.CA", "ODIN.CA", "EGAS.CA",
    "RACC.CA", "PRCL.CA", "BINV.CA", "EDBM.CA", "MCQE.CA",
    "MOIL.CA", "NIPH.CA", "ISPH.CA", "DICE.CA", "IDHC.CA",
    "UNIT.CA", "PHAR.CA", "TRTO.CA", "ALRA.CA", "FARE.CA",
    "ICFC.CA", "MISr.CA", "MOBI.CA", "ELKA.CA", "NILE.CA",
    "ATLC.CA", "COSG.CA", "MEDA.CA", "AMPI.CA", "COPR.CA"
]

EGX100 = list(dict.fromkeys(EGX100))
TOTAL_STOCKS = len(EGX100)


# =========================================================
# 🎛️ SIDEBAR
# =========================================================

st.sidebar.header("⚙️ إعدادات الفحص")

period_daily = st.sidebar.selectbox(
    "📅 Daily",
    ["3mo", "6mo", "1y", "2y", "3y", "5y", "max"],
    index=6
)

period_weekly = st.sidebar.selectbox(
    "📅 Weekly",
    ["3y", "5y", "10y", "max"],
    index=3
)

period_monthly = st.sidebar.selectbox(
    "📅 Monthly",
    ["10y", "15y", "20y", "max"],
    index=3
)

max_workers = st.sidebar.slider(
    "⚡ الاتصالات المتوازية",
    2,
    16,
    8,
    1
)

top_n = st.sidebar.slider(
    "🏆 أفضل عدد أسهم",
    5,
    100,
    20,
    5
)


# =========================================================
# 💰 RISK
# =========================================================

st.sidebar.markdown("---")
st.sidebar.header("💰 إدارة المخاطر")

capital = st.sidebar.number_input(
    "رأس المال بالجنيه",
    min_value=1000.0,
    max_value=100000000.0,
    value=100000.0,
    step=5000.0
)

risk_percent = st.sidebar.slider(
    "مخاطرة الصفقة %",
    0.5,
    10.0,
    2.0,
    0.5
)


# =========================================================
# 🧪 BACKTEST
# =========================================================

run_backtest = st.sidebar.checkbox(
    "🧪 تشغيل Backtest تاريخي حقيقي",
    value=True
)

backtest_bars = st.sidebar.slider(
    "عدد شموع الاختبار",
    100,
    2000,
    300,
    50
)

backtest_fee_pct = st.sidebar.number_input(
    "عمولة لكل جانب %",
    min_value=0.0,
    max_value=2.0,
    value=0.15,
    step=0.05
)

backtest_slippage_pct = st.sidebar.number_input(
    "Slippage لكل تنفيذ %",
    min_value=0.0,
    max_value=2.0,
    value=0.10,
    step=0.05
)

backtest_risk_pct = st.sidebar.slider(
    "مخاطرة Backtest لكل صفقة %",
    0.25,
    5.0,
    2.0,
    0.25
)

backtest_max_positions = st.sidebar.slider(
    "أقصى مراكز متزامنة",
    1,
    3,
    1,
    1
)


# =========================================================
# ℹ️ INFO
# =========================================================

st.sidebar.markdown("---")

st.sidebar.metric(
    "📊 الأسهم",
    TOTAL_STOCKS
)

st.sidebar.info(
    """
📌 المحرك يشمل:

• Daily / Weekly / Monthly
• EMA20 / EMA50 / EMA200
• RSI
• MACD
• ADX
• ATR
• OBV
• MFI
• Stochastic RSI
• VWAP
• Volume Ratio
• Liquidity
• Relative Strength
• Support / Resistance
• Confirmed Swing
• Fibonacci
• Fibonacci Extensions
• Breakout
• Pullback
• Immediate Entry
• Trend Alignment
• Structural Targets
• Risk Management
• Real Historical Backtest
"""
)


# =========================================================
# 🧠 CONSTANTS
# =========================================================

MIN_DAILY_ROWS = 60
MIN_WEEKLY_ROWS = 80
MIN_MONTHLY_ROWS = 36

EMA200_REQUIRED_ROWS = 200

DOWNLOAD_RETRIES = 3
DOWNLOAD_RETRY_DELAY = 2

BACKTEST_WARMUP = 250

PIVOT_RADIUS = 3

LIQUIDITY_LOOKBACK = 20
RS_LOOKBACK = 20


# =========================================================
# 📥 DATA ENGINE
# =========================================================

@st.cache_data(
    ttl=3600,
    show_spinner=False
)
def load_data(symbols, period, interval):

    if not symbols:
        return pd.DataFrame()

    symbols = tuple(symbols)

    last_error = None

    for attempt in range(DOWNLOAD_RETRIES):

        try:

            data = yf.download(
                tickers=list(symbols),
                period=period,
                interval=interval,
                group_by="ticker",
                threads=True,
                auto_adjust=True,
                progress=False,
                timeout=60
            )

            if data is not None and not data.empty:
                return data

            last_error = "Yahoo returned empty data"

        except Exception as e:

            last_error = str(e)

        if attempt < DOWNLOAD_RETRIES - 1:

            time.sleep(
                DOWNLOAD_RETRY_DELAY * (attempt + 1)
            )

    return pd.DataFrame()


# =========================================================
# 🔍 EXTRACT
# =========================================================

def extract_symbol_data(data, symbol):

    try:

        if data is None or data.empty:
            return pd.DataFrame()

        if isinstance(data.columns, pd.MultiIndex):

            level0 = data.columns.get_level_values(0)
            level1 = data.columns.get_level_values(1)

            if symbol in level0:

                df = data[symbol].copy()

            elif symbol in level1:

                df = data.xs(
                    symbol,
                    axis=1,
                    level=1
                ).copy()

            else:

                return pd.DataFrame()

        else:

            df = data.copy()

        df.columns = [
            str(c).strip()
            for c in df.columns
        ]

        required = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ]

        if not all(
            c in df.columns
            for c in required
        ):
            return pd.DataFrame()

        df = df[required].copy()

        for col in required:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

        df = df.replace(
            [np.inf, -np.inf],
            np.nan
        )

        df = df.dropna(
            subset=[
                "Open",
                "High",
                "Low",
                "Close"
            ]
        )

        df["Volume"] = df["Volume"].fillna(0)

        df = df[
            (df["High"] >= df["Low"]) &
            (df["Close"] > 0) &
            (df["Open"] > 0)
        ]

        df = df.sort_index()

        df = df[
            ~df.index.duplicated(
                keep="last"
            )
        ]

        return df

    except Exception:

        return pd.DataFrame()


# =========================================================
# 📊 DATA QUALITY
# =========================================================

def calculate_data_quality(df):

    if df is None or df.empty:

        return {
            "quality": 0.0,
            "missing": 100.0,
            "rows": 0
        }

    required = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume"
    ]

    total = len(df) * len(required)

    missing = int(
        df[required]
        .isna()
        .sum()
        .sum()
    )

    missing_pct = (
        missing / total * 100
        if total
        else 100
    )

    quality = max(
        0,
        100 - missing_pct
    )

    return {
        "quality": round(quality, 2),
        "missing": round(missing_pct, 2),
        "rows": len(df)
    }


# =========================================================
# 📊 ATR
# =========================================================

def atr(df, period=14):

    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    tr = pd.concat(
        [
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs()
        ],
        axis=1
    ).max(axis=1)

    return tr.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period
    ).mean()


# =========================================================
# 📊 ADX
# =========================================================

def adx(df, period=14):

    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    plus_raw = high.diff()
    minus_raw = -low.diff()

    plus_dm = np.where(
        (plus_raw > minus_raw) &
        (plus_raw > 0),
        plus_raw,
        0
    )

    minus_dm = np.where(
        (minus_raw > plus_raw) &
        (minus_raw > 0),
        minus_raw,
        0
    )

    tr = pd.concat(
        [
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs()
        ],
        axis=1
    ).max(axis=1)

    atr_val = tr.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period
    ).mean()

    plus_di = (
        100 *
        pd.Series(
            plus_dm,
            index=df.index
        ).ewm(
            alpha=1 / period,
            adjust=False,
            min_periods=period
        ).mean()
        /
        (atr_val + 1e-9)
    )

    minus_di = (
        100 *
        pd.Series(
            minus_dm,
            index=df.index
        ).ewm(
            alpha=1 / period,
            adjust=False,
            min_periods=period
        ).mean()
        /
        (atr_val + 1e-9)
    )

    dx = (
        abs(plus_di - minus_di)
        /
        (plus_di + minus_di + 1e-9)
    ) * 100

    return dx.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period
    ).mean()


# =========================================================
# 📈 INDICATORS
# =========================================================

def add_indicators(df):

    df = df.copy()

    if df.empty:
        return df

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # EMA
    df["ema20"] = close.ewm(
        span=20,
        adjust=False
    ).mean()

    df["ema50"] = close.ewm(
        span=50,
        adjust=False
    ).mean()

    if len(df) >= EMA200_REQUIRED_ROWS:

        df["ema200"] = close.ewm(
            span=200,
            adjust=False,
            min_periods=200
        ).mean()

    else:

        df["ema200"] = np.nan

    df["ema200_complete"] = (
        df["ema200"].notna()
    )

    # RSI
    df["rsi"] = ta.momentum.RSIIndicator(
        close,
        window=14
    ).rsi()

    # MACD
    macd = ta.trend.MACD(
        close,
        window_slow=26,
        window_fast=12,
        window_sign=9
    )

    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_hist"] = macd.macd_diff()

    # Volume
    df["vol_ma"] = volume.rolling(
        20,
        min_periods=10
    ).mean()

    df["volume_ratio"] = (
        volume /
        (df["vol_ma"] + 1e-9)
    )

    # OBV
    try:

        obv = ta.volume.OnBalanceVolumeIndicator(
            close,
            volume
        )

        df["obv"] = obv.on_balance_volume()

        df["obv_ma"] = (
            df["obv"]
            .rolling(20, min_periods=10)
            .mean()
        )

        df["obv_slope"] = (
            df["obv"] -
            df["obv"].shift(5)
        )

    except Exception:

        df["obv"] = np.nan
        df["obv_ma"] = np.nan
        df["obv_slope"] = np.nan

    # MFI
    try:

        mfi = ta.volume.MFIIndicator(
            high,
            low,
            close,
            volume,
            window=14
        )

        df["mfi"] = mfi.money_flow_index()

    except Exception:

        df["mfi"] = np.nan

    # Stoch RSI
    try:

        stoch = ta.momentum.StochRSIIndicator(
            close,
            window=14,
            smooth1=3,
            smooth2=3
        )

        df["stoch_rsi"] = stoch.stochrsi()
        df["stoch_rsi_k"] = stoch.stochrsi_k()
        df["stoch_rsi_d"] = stoch.stochrsi_d()

    except Exception:

        df["stoch_rsi"] = np.nan
        df["stoch_rsi_k"] = np.nan
        df["stoch_rsi_d"] = np.nan

    # VWAP
    typical = (
        high + low + close
    ) / 3

    cumulative_volume = volume.cumsum()

    df["vwap"] = (
        typical * volume
    ).cumsum() / (
        cumulative_volume + 1e-9
    )

    df["vwap_distance"] = (
        close - df["vwap"]
    ) / (
        close + 1e-9
    )

    # ATR / ADX
    df["atr"] = atr(df, 14)

    df["atr_pct"] = (
        df["atr"] /
        (close + 1e-9)
    )

    df["adx"] = adx(df, 14)

    # Structure
    df["support"] = (
        low
        .rolling(20, min_periods=10)
        .min()
    )

    df["resistance"] = (
        high
        .rolling(20, min_periods=10)
        .max()
    )

    df["previous_support"] = (
        df["support"].shift(1)
    )

    df["previous_resistance"] = (
        df["resistance"].shift(1)
    )

    # Swing windows
    df["swing_high_20"] = (
        high
        .rolling(20, min_periods=10)
        .max()
        .shift(1)
    )

    df["swing_low_20"] = (
        low
        .rolling(20, min_periods=10)
        .min()
        .shift(1)
    )

    df["swing_high_60"] = (
        high
        .rolling(60, min_periods=20)
        .max()
        .shift(1)
    )

    df["swing_low_60"] = (
        low
        .rolling(60, min_periods=20)
        .min()
        .shift(1)
    )

    # Confirmed pivots
    w = PIVOT_RADIUS * 2 + 1

    pivot_high = (
        high.eq(
            high.rolling(
                w,
                center=True,
                min_periods=w
            ).max()
        )
    )

    pivot_low = (
        low.eq(
            low.rolling(
                w,
                center=True,
                min_periods=w
            ).min()
        )
    )

    df["confirmed_swing_high"] = (
        high.where(pivot_high)
        .shift(PIVOT_RADIUS)
        .ffill()
    )

    df["confirmed_swing_low"] = (
        low.where(pivot_low)
        .shift(PIVOT_RADIUS)
        .ffill()
    )

    idx = pd.Series(
        np.arange(len(df)),
        index=df.index,
        dtype=float
    )

    df["confirmed_high_idx"] = (
        idx.where(pivot_high)
        .shift(PIVOT_RADIUS)
        .ffill()
    )

    df["confirmed_low_idx"] = (
        idx.where(pivot_low)
        .shift(PIVOT_RADIUS)
        .ffill()
    )

    # Confirmed Fibonacci
    bull_leg = (
        df["confirmed_low_idx"].notna() &
        df["confirmed_high_idx"].notna() &
        (
            df["confirmed_low_idx"] <
            df["confirmed_high_idx"]
        )
    )

    fib_hi = df["confirmed_swing_high"]
    fib_lo = df["confirmed_swing_low"]

    fib_range = (
        fib_hi - fib_lo
    ).where(bull_leg)

    for ratio, col in [
        (0.236, "fib_236"),
        (0.382, "fib_382"),
        (0.500, "fib_500"),
        (0.618, "fib_618"),
        (0.786, "fib_786")
    ]:

        df[col] = (
            fib_hi -
            fib_range * ratio
        ).where(
            fib_range > 0
        )

    df["fib_ext_1272"] = (
        fib_hi +
        fib_range * 0.272
    ).where(
        fib_range > 0
    )

    df["fib_ext_1618"] = (
        fib_hi +
        fib_range * 0.618
    ).where(
        fib_range > 0
    )

    df["fib_ext_2000"] = (
        fib_hi +
        fib_range
    ).where(
        fib_range > 0
    )

    # Trend slope
    df["ema20_slope"] = (
        df["ema20"] -
        df["ema20"].shift(5)
    ) / (
        close + 1e-9
    )

    df["ema50_slope"] = (
        df["ema50"] -
        df["ema50"].shift(5)
    ) / (
        close + 1e-9
    )

    # Candle
    candle_range = (
        high - low
    ).replace(0, np.nan)

    df["body_pct"] = (
        abs(close - df["Open"])
        /
        candle_range
    )

    df["bullish_candle"] = (
        close > df["Open"]
    )

    df["close_location"] = (
        close - low
    ) / (
        candle_range + 1e-9
    )

    # Liquidity
    df["turnover"] = (
        close * volume
    )

    df["turnover_ma20"] = (
        df["turnover"]
        .rolling(
            LIQUIDITY_LOOKBACK,
            min_periods=10
        )
        .median()
    )

    df["liquidity_ratio"] = (
        df["turnover"] /
        (
            df["turnover_ma20"] +
            1e-9
        )
    )

    df["return_20d"] = (
        close.pct_change(RS_LOOKBACK)
    )

    # ATR expansion
    df["atr_expansion"] = (
        df["atr"] /
        (
            df["atr"]
            .rolling(20, min_periods=10)
            .mean()
            + 1e-9
        )
    )

    # =====================================================
    # BREAKOUT
    # =====================================================

    df["breakout"] = (
        (close > df["previous_resistance"]) &
        (df["volume_ratio"] >= 1.30) &
        (df["atr_pct"] >= 0.015) &
        (df["atr_pct"] <= 0.12) &
        (df["body_pct"] >= 0.45) &
        df["bullish_candle"] &
        (close > df["ema20"]) &
        (df["ema20"] > df["ema50"])
    )

    # =====================================================
    # PULLBACK
    # =====================================================

    distance_20 = (
        abs(close - df["ema20"])
        /
        (close + 1e-9)
    )

    distance_50 = (
        abs(close - df["ema50"])
        /
        (close + 1e-9)
    )

    near_ema = (
        (distance_20 <= 0.025) |
        (distance_50 <= 0.035)
    )

    trend_bullish = (
        (close > df["ema50"]) &
        (df["ema20"] > df["ema50"]) &
        (df["ema20_slope"] > 0)
    )

    support_near = (
        abs(
            close -
            df["previous_support"]
        )
        /
        (close + 1e-9)
        <= 0.04
    )

    fib_support_near = (
        (
            abs(close - df["fib_382"])
            /
            (close + 1e-9)
            <= 0.025
        )
        |
        (
            abs(close - df["fib_500"])
            /
            (close + 1e-9)
            <= 0.025
        )
        |
        (
            abs(close - df["fib_618"])
            /
            (close + 1e-9)
            <= 0.025
        )
    )

    reduced_selling = (
        (df["volume_ratio"] <= 1.30) &
        (df["close_location"] >= 0.45)
    )

    bullish_confirmation = (
        (
            df["bullish_candle"] &
            (df["body_pct"] >= 0.35)
        )
        |
        (close > df["ema20"])
    )

    pullback_score = (
        trend_bullish.astype(int) * 2 +
        near_ema.astype(int) * 2 +
        support_near.astype(int) +
        fib_support_near.astype(int) +
        reduced_selling.astype(int) +
        bullish_confirmation.astype(int)
    )

    df["pullback_quality_score"] = (
        pullback_score
    )

    df["pullback"] = (
        (pullback_score >= 6) &
        trend_bullish
    )

    return df


# =========================================================
# 🧠 TIMEFRAME SCORE
# =========================================================

def timeframe_score(df):

    if df is None or df.empty:
        return 0.0

    last = df.iloc[-1]

    score = 0

    if (
        np.isfinite(last.get("ema200", np.nan)) and
        last["Close"] > last["ema200"]
    ):
        score += 25

    if last["ema20"] > last["ema50"]:
        score += 20

    if (
        np.isfinite(last.get("ema200", np.nan)) and
        last["ema50"] > last["ema200"]
    ):
        score += 20

    if last["macd"] > last["macd_signal"]:
        score += 15

    if last["rsi"] > 50:
        score += 10

    if last["ema20_slope"] > 0:
        score += 10

    if not bool(
        last.get(
            "ema200_complete",
            False
        )
    ):
        score = min(score, 55)

    return float(score)


# =========================================================
# 📊 HISTORICAL TIMEFRAME CONTEXT
#
# مهم جدًا للـ Backtest:
# Weekly/Monthly لا يتم استخدام الشمعة الحالية غير المكتملة.
# =========================================================

def build_historical_context(df_daily):

    d = df_daily.copy()

    if d.empty:
        return d

    # Daily
    d_ind = add_indicators(d)

    # Weekly
    w = (
        d.resample("W-FRI")
        .agg({
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Volume": "sum"
        })
        .dropna()
    )

    w_ind = add_indicators(w)

    # Monthly
    m = (
        d.resample("ME")
        .agg({
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Volume": "sum"
        })
        .dropna()
    )

    m_ind = add_indicators(m)

    # Convert indexes
    d_idx = pd.DatetimeIndex(
        pd.to_datetime(d_ind.index)
    )

    w_idx = pd.DatetimeIndex(
        pd.to_datetime(w_ind.index)
    )

    m_idx = pd.DatetimeIndex(
        pd.to_datetime(m_ind.index)
    )

    d_ind.index = d_idx
    w_ind.index = w_idx
    m_ind.index = m_idx

    # =====================================================
    # IMPORTANT:
    # For a daily decision, use LAST COMPLETED weekly/monthly
    # candle, not the currently forming one.
    # =====================================================

    w_context = w_ind[
        [
            "Close",
            "ema20",
            "ema50",
            "ema200",
            "ema200_complete",
            "macd",
            "macd_signal",
            "rsi",
            "ema20_slope"
        ]
    ].copy()

    m_context = m_ind[
        [
            "Close",
            "ema20",
            "ema50",
            "ema200",
            "ema200_complete",
            "macd",
            "macd_signal",
            "rsi",
            "ema20_slope"
        ]
    ].copy()

    w_context = w_context.shift(1)
    m_context = m_context.shift(1)

    # Avoid duplicate columns
    w_context.columns = [
        f"w_{c}"
        for c in w_context.columns
    ]

    m_context.columns = [
        f"m_{c}"
        for c in m_context.columns
    ]

    base = d_ind.reset_index()
    base = base.rename(
        columns={
            base.columns[0]: "date"
        }
    )

    w_reset = w_context.reset_index()
    w_reset = w_reset.rename(
        columns={
            w_reset.columns[0]: "date"
        }
    )

    m_reset = m_context.reset_index()
    m_reset = m_reset.rename(
        columns={
            m_reset.columns[0]: "date"
        }
    )

    base = base.sort_values("date")
    w_reset = w_reset.sort_values("date")
    m_reset = m_reset.sort_values("date")

    base = pd.merge_asof(
        base,
        w_reset,
        on="date",
        direction="backward"
    )

    base = pd.merge_asof(
        base,
        m_reset,
        on="date",
        direction="backward"
    )

    base = base.set_index("date")

    # =====================================================
    # Historical alignment
    # =====================================================

    alignment_values = []

    for _, row in base.iterrows():

        daily_score = historical_row_score(
            row,
            prefix=""
        )

        weekly_score = historical_row_score(
            row,
            prefix="w_"
        )

        monthly_score = historical_row_score(
            row,
            prefix="m_"
        )

        alignment = (
            daily_score * 0.40 +
            weekly_score * 0.35 +
            monthly_score * 0.25
        )

        alignment_values.append(
            min(100, max(0, alignment))
        )

    base["historical_alignment"] = (
        alignment_values
    )

    return base


# =========================================================
# 🧠 HISTORICAL ROW SCORE
# =========================================================

def historical_row_score(
    row,
    prefix=""
):

    def val(name):

        try:
            return float(
                row.get(
                    f"{prefix}{name}",
                    np.nan
                )
            )
        except Exception:
            return np.nan

    close = val("Close")
    ema20 = val("ema20")
    ema50 = val("ema50")
    ema200 = val("ema200")
    macd = val("macd")
    signal = val("macd_signal")
    rsi = val("rsi")
    slope = val("ema20_slope")

    score = 0

    if (
        np.isfinite(ema200) and
        np.isfinite(close) and
        close > ema200
    ):
        score += 25

    if (
        np.isfinite(ema20) and
        np.isfinite(ema50) and
        ema20 > ema50
    ):
        score += 20

    if (
        np.isfinite(ema200) and
        np.isfinite(ema50) and
        ema50 > ema200
    ):
        score += 20

    if (
        np.isfinite(macd) and
        np.isfinite(signal) and
        macd > signal
    ):
        score += 15

    if np.isfinite(rsi) and rsi > 50:
        score += 10

    if np.isfinite(slope) and slope > 0:
        score += 10

    if not np.isfinite(ema200):
        score = min(score, 55)

    return float(score)


# =========================================================
# 🧠 MARKET REGIME
# =========================================================

def market_regime(last):

    score = 0

    if (
        np.isfinite(last.get("ema200", np.nan)) and
        last["Close"] > last["ema200"]
    ):
        score += 1

    if last["ema20"] > last["ema50"]:
        score += 1

    if (
        np.isfinite(last.get("ema200", np.nan)) and
        last["ema50"] > last["ema200"]
    ):
        score += 1

    if last["macd"] > last["macd_signal"]:
        score += 1

    if last["rsi"] > 50:
        score += 1

    if last["adx"] > 20:
        score += 1

    if score >= 6:
        return "🚀 قوي جداً"

    if score >= 4:
        return "🟢 صعود"

    if score >= 3:
        return "🟡 محايد"

    return "🔴 هبوط"


# =========================================================
# 🎯 PULLBACK ENTRY
# =========================================================

def calculate_pullback_entry(df):

    last = df.iloc[-1]

    close = float(last["Close"])

    atr_val = float(
        last.get("atr", np.nan)
    )

    if not np.isfinite(atr_val) or atr_val <= 0:
        atr_val = close * 0.03

    candidates = [
        (
            "Confirmed Support",
            last.get(
                "previous_support",
                np.nan
            )
        ),
        (
            "Confirmed Swing Low",
            last.get(
                "confirmed_swing_low",
                np.nan
            )
        ),
        (
            "EMA20",
            last.get(
                "ema20",
                np.nan
            )
        ),
        (
            "EMA50",
            last.get(
                "ema50",
                np.nan
            )
        ),
        (
            "Fib 38.2%",
            last.get(
                "fib_382",
                np.nan
            )
        ),
        (
            "Fib 50%",
            last.get(
                "fib_500",
                np.nan
            )
        ),
        (
            "Fib 61.8%",
            last.get(
                "fib_618",
                np.nan
            )
        )
    ]

    levels = []

    for name, value in candidates:

        try:

            value = float(value)

            if (
                np.isfinite(value) and
                0 < value <= close
            ):

                levels.append(
                    (name, value)
                )

        except Exception:
            pass

    if not levels:

        return (
            close,
            "لا توجد منطقة Pullback مؤكدة"
        )

    max_distance = max(
        atr_val * 1.5,
        close * 0.06
    )

    nearby = [
        x for x in levels
        if close - x[1] <= max_distance
    ]

    if not nearby:

        return (
            close,
            "لا يوجد Pullback قريب"
        )

    priority = {
        "Confirmed Support": 1,
        "Confirmed Swing Low": 2,
        "Fib 61.8%": 3,
        "Fib 50%": 4,
        "Fib 38.2%": 5,
        "EMA50": 6,
        "EMA20": 7
    }

    name, price = min(
        nearby,
        key=lambda x: (
            priority.get(x[0], 99),
            abs(close - x[1])
        )
    )

    return (
        float(price),
        f"منطقة {name} مؤكدة"
    )


# =========================================================
# 🎯 ENTRY ENGINE
# =========================================================

def determine_entry(
    df,
    alignment
):

    last = df.iloc[-1]

    price = float(
        last["Close"]
    )

    ema20 = float(
        last["ema20"]
    )

    ema50 = float(
        last["ema50"]
    )

    breakout = bool(
        last.get(
            "breakout",
            False
        )
    )

    pullback = bool(
        last.get(
            "pullback",
            False
        )
    )

    volume_ratio = float(
        last.get(
            "volume_ratio",
            0
        )
    )

    atr_pct = float(
        last.get(
            "atr_pct",
            0
        )
    )

    body_pct = float(
        last.get(
            "body_pct",
            0
        )
    )

    previous_resistance = float(
        last.get(
            "previous_resistance",
            np.nan
        )
    )

    # =====================================================
    # BREAKOUT
    # =====================================================

    if (
        breakout and
        np.isfinite(previous_resistance) and
        price > previous_resistance and
        volume_ratio >= 1.5 and
        0.015 <= atr_pct <= 0.12 and
        body_pct >= 0.45 and
        alignment >= 60
    ):

        return {
            "type": "دخول اختراق",
            "price": price,
            "reason": (
                "اختراق مقاومة + حجم قوي + "
                "شمعة جيدة + Trend Alignment"
            )
        }

    # =====================================================
    # PULLBACK
    # =====================================================

    if (
        pullback and
        ema20 > ema50 and
        alignment >= 55
    ):

        pb_price, pb_reason = (
            calculate_pullback_entry(df)
        )

        return {
            "type": "دخول عند Pullback",
            "price": pb_price,
            "reason": (
                "اتجاه صاعد + منطقة دعم مؤكدة + "
                pb_reason
            )
        }

    # =====================================================
    # IMMEDIATE
    # =====================================================

    if (
        price > ema20 and
        price > ema50 and
        last["rsi"] >= 50 and
        last["macd"] > last["macd_signal"] and
        price > last["vwap"] and
        volume_ratio >= 1.0 and
        alignment >= 50
    ):

        return {
            "type": "دخول فوري",
            "price": price,
            "reason": (
                "السعر فوق EMA20/50/VWAP + "
                "RSI + MACD + حجم جيد"
            )
        }

    return {
        "type": "انتظار تأكيد",
        "price": price,
        "reason": (
            "لا توجد شروط كافية للدخول"
        )
    }


# =========================================================
# 🎯 STRUCTURAL TARGET ENGINE
# =========================================================

def calculate_targets(
    df_d,
    entry,
    df_w=None,
    df_m=None
):

    last = df_d.iloc[-1]

    levels = []

    def add(
        price,
        reason,
        category
    ):

        try:

            price = float(price)

            if (
                np.isfinite(price) and
                price > entry
            ):

                levels.append({
                    "price": price,
                    "reason": reason,
                    "category": category
                })

        except Exception:
            pass

    # Daily
    add(
        last.get(
            "previous_resistance",
            np.nan
        ),
        "المقاومة اليومية السابقة",
        "Resistance"
    )

    add(
        last.get(
            "resistance",
            np.nan
        ),
        "المقاومة اليومية الحالية",
        "Resistance"
    )

    # Swing
    add(
        last.get(
            "confirmed_swing_high",
            np.nan
        ),
        "آخر Swing High مؤكد",
        "Swing High"
    )

    # Fibonacci extensions
    add(
        last.get(
            "fib_ext_1272",
            np.nan
        ),
        "Fibonacci Extension 127.2%",
        "Fibonacci"
    )

    add(
        last.get(
            "fib_ext_1618",
            np.nan
        ),
        "Fibonacci Extension 161.8%",
        "Fibonacci"
    )

    add(
        last.get(
            "fib_ext_2000",
            np.nan
        ),
        "Fibonacci Extension 200%",
        "Fibonacci"
    )

    # Weekly
    if df_w is not None and not df_w.empty:

        try:

            value = (
                df_w["High"]
                .rolling(
                    20,
                    min_periods=10
                )
                .max()
                .shift(1)
                .iloc[-1]
            )

            add(
                value,
                "مقاومة Weekly سابقة",
                "Weekly"
            )

        except Exception:
            pass

    # Monthly
    if df_m is not None and not df_m.empty:

        try:

            value = (
                df_m["High"]
                .rolling(
                    12,
                    min_periods=6
                )
                .max()
                .shift(1)
                .iloc[-1]
            )

            add(
                value,
                "مقاومة Monthly سابقة",
                "Monthly"
            )

        except Exception:
            pass

    priority = {
        "Resistance": 1,
        "Swing High": 2,
        "Weekly": 3,
        "Monthly": 4,
        "Fibonacci": 5
    }

    levels.sort(
        key=lambda x: x["price"]
    )

    # Deduplicate
    dedup = []

    for level in levels:

        if not dedup:

            dedup.append(level)
            continue

        gap = (
            abs(
                level["price"] -
                dedup[-1]["price"]
            )
            /
            max(
                dedup[-1]["price"],
                1e-9
            )
        )

        if gap >= 0.008:

            dedup.append(level)

        elif priority.get(
            level["category"],
            99
        ) < priority.get(
            dedup[-1]["category"],
            99
        ):

            dedup[-1] = level

    atr_val = float(
        last.get(
            "atr",
            entry * 0.03
        )
    )

    if not np.isfinite(atr_val):
        atr_val = entry * 0.03

    min_gap = max(
        atr_val * 0.40,
        entry * 0.012
    )

    selected = []

    for level in dedup:

        if (
            not selected or
            level["price"] >=
            selected[-1]["price"] + min_gap
        ):

            selected.append(level)

        if len(selected) >= 4:
            break

    return selected


# =========================================================
# 🛡️ RISK ENGINE
# =========================================================

def calculate_risk_engine(
    df_d,
    entry,
    capital,
    risk_percent,
    df_w=None,
    df_m=None
):

    last = df_d.iloc[-1]

    atr_val = float(
        last.get(
            "atr",
            np.nan
        )
    )

    if (
        not np.isfinite(atr_val) or
        atr_val <= 0
    ):

        atr_val = entry * 0.03

    stop_candidates = []

    for level in [
        last.get(
            "previous_support",
            np.nan
        ),
        last.get(
            "confirmed_swing_low",
            np.nan
        )
    ]:

        try:

            level = float(level)

            if (
                np.isfinite(level) and
                0 < level < entry
            ):

                stop_candidates.append(
                    level - atr_val * 0.20
                )

        except Exception:
            pass

    bullish = (
        last["ema20"] >
        last["ema50"]
    )

    stop_candidates.append(
        entry -
        atr_val *
        (
            1.5
            if bullish
            else 1.2
        )
    )

    stop_candidates = [
        x for x in stop_candidates
        if np.isfinite(x) and
        0 < x < entry
    ]

    stop = (
        max(stop_candidates)
        if stop_candidates
        else entry * 0.95
    )

    risk_per_share = (
        entry - stop
    )

    if (
        risk_per_share <= 0 or
        not np.isfinite(risk_per_share)
    ):

        risk_per_share = (
            entry * 0.03
        )

        stop = (
            entry -
            risk_per_share
        )

    allowed_loss = (
        capital *
        risk_percent /
        100
    )

    position_size = (
        allowed_loss /
        risk_per_share
    )

    position_value = (
        position_size *
        entry
    )

    targets = calculate_targets(
        df_d,
        entry,
        df_w,
        df_m
    )

    target_prices = [
        x["price"]
        for x in targets
    ]

    target_reasons = [
        x["reason"]
        for x in targets
    ]

    target_categories = [
        x["category"]
        for x in targets
    ]

    while len(target_prices) < 4:

        target_prices.append(
            np.nan
        )

        target_reasons.append(
            "لا يوجد مستوى سعري هيكلي موثوق"
        )

        target_categories.append(
            "غير متاح"
        )

    profits = []

    rr = []

    for price in target_prices:

        if np.isfinite(price):

            profits.append(
                (
                    price - entry
                )
                /
                entry
                * 100
            )

            rr.append(
                (
                    price - entry
                )
                /
                risk_per_share
            )

        else:

            profits.append(
                np.nan
            )

            rr.append(
                np.nan
            )

    quality_points = {
        "Resistance": 1.0,
        "Swing High": 0.95,
        "Weekly": 0.90,
        "Monthly": 0.90,
        "Fibonacci": 0.80,
        "غير متاح": 0.0
    }

    target_quality = (
        np.mean(
            [
                quality_points.get(
                    x,
                    0
                )
                for x in target_categories
            ]
        )
        * 100
    )

    return {

        "entry": entry,

        "stop": stop,

        "tp1": target_prices[0],
        "tp2": target_prices[1],
        "tp3": target_prices[2],
        "tp4": target_prices[3],

        "tp1_profit_pct": profits[0],
        "tp2_profit_pct": profits[1],
        "tp3_profit_pct": profits[2],
        "tp4_profit_pct": profits[3],

        "tp1_reason": target_reasons[0],
        "tp2_reason": target_reasons[1],
        "tp3_reason": target_reasons[2],
        "tp4_reason": target_reasons[3],

        "tp1_category": target_categories[0],
        "tp2_category": target_categories[1],
        "tp3_category": target_categories[2],
        "tp4_category": target_categories[3],

        "rr1": rr[0],
        "rr2": rr[1],
        "rr3": rr[2],
        "rr4": rr[3],

        "target_quality": target_quality,

        "risk_pct": (
            risk_per_share /
            entry *
            100
        ),

        "position_size": position_size,

        "position_value": position_value,

        "structural_target_count": len(targets)
    }


# =========================================================
# 🧠 CONFIDENCE
# =========================================================

def ai_confidence(
    d,
    w,
    m,
    alignment,
    data_quality
):

    score = 0
    total = 13

    if (
        np.isfinite(d.get("ema200", np.nan)) and
        d["Close"] > d["ema200"]
    ):
        score += 1

    if (
        np.isfinite(w.get("ema200", np.nan)) and
        w["Close"] > w["ema200"]
    ):
        score += 1

    if (
        np.isfinite(m.get("ema200", np.nan)) and
        m["Close"] > m["ema200"]
    ):
        score += 1

    if d["macd"] > d["macd_signal"]:
        score += 1

    if 45 < d["rsi"] < 70:
        score += 1

    if d["volume_ratio"] > 1:
        score += 1

    if d["adx"] > 20:
        score += 1

    if 40 < d["mfi"] < 80:
        score += 1

    if (
        np.isfinite(d["obv"]) and
        np.isfinite(d["obv_ma"]) and
        d["obv"] > d["obv_ma"]
    ):
        score += 1

    if (
        np.isfinite(d["stoch_rsi_k"]) and
        np.isfinite(d["stoch_rsi_d"]) and
        d["stoch_rsi_k"] >
        d["stoch_rsi_d"]
    ):
        score += 1

    if (
        np.isfinite(d["vwap"]) and
        d["Close"] > d["vwap"]
    ):
        score += 1

    if alignment >= 60:
        score += 1

    if data_quality >= 90:
        score += 1

    return score / total


# =========================================================
# 🧠 PROBABILITY
# =========================================================

def estimate_probabilities(
    base_conf,
    rr1,
    rr2,
    rr3,
    rr4,
    alignment,
    adx_val
):

    trend_factor = alignment / 100

    momentum_factor = min(
        1,
        max(
            0.5,
            adx_val / 35
        )
    )

    base = (
        base_conf * 0.60 +
        trend_factor * 0.25 +
        momentum_factor * 0.15
    )

    def probability(
        current,
        rr,
        good_rr,
        bad_rr,
        add_good,
        sub_bad,
        maximum,
        minimum
    ):

        value = current

        if np.isfinite(rr) and rr >= good_rr:
            value += add_good

        elif not np.isfinite(rr) or rr < bad_rr:
            value -= sub_bad

        return min(
            maximum,
            max(
                minimum,
                value
            )
        )

    tp1 = probability(
        base,
        rr1,
        2,
        1.2,
        0.05,
        0.10,
        0.90,
        0.20
    )

    tp2 = probability(
        tp1 * 0.82,
        rr2,
        2,
        1.5,
        0.03,
        0.05,
        0.82,
        0.15
    )

    tp3 = probability(
        tp2 * 0.78,
        rr3,
        2.5,
        2,
        0.03,
        0.05,
        0.75,
        0.10
    )

    tp4 = probability(
        tp3 * 0.72,
        rr4,
        3,
        2.5,
        0.03,
        0.05,
        0.68,
        0.08
    )

    return (
        tp1,
        tp2,
        tp3,
        tp4
    )


# =========================================================
# 🧠 MAIN ANALYSIS
# =========================================================

def analyze(
    df_d,
    df_w,
    df_m,
    capital,
    risk_percent
):

    df_d = add_indicators(df_d)
    df_w = add_indicators(df_w)
    df_m = add_indicators(df_m)

    if len(df_d) < MIN_DAILY_ROWS:
        raise ValueError(
            "بيانات Daily غير كافية"
        )

    if len(df_w) < MIN_WEEKLY_ROWS:
        raise ValueError(
            "بيانات Weekly غير كافية"
        )

    if len(df_m) < MIN_MONTHLY_ROWS:
        raise ValueError(
            "بيانات Monthly غير كافية"
        )

    quality_d = calculate_data_quality(df_d)
    quality_w = calculate_data_quality(df_w)
    quality_m = calculate_data_quality(df_m)

    data_quality = (
        quality_d["quality"] * 0.50 +
        quality_w["quality"] * 0.30 +
        quality_m["quality"] * 0.20
    )

    required = [
        "ema20",
        "ema50",
        "rsi",
        "macd",
        "macd_signal",
        "macd_hist",
        "volume_ratio",
        "obv",
        "obv_ma",
        "obv_slope",
        "mfi",
        "stoch_rsi_k",
        "stoch_rsi_d",
        "vwap",
        "previous_support",
        "previous_resistance",
        "atr",
        "adx",
        "ema20_slope",
        "ema50_slope",
        "body_pct"
    ]

    df_d = df_d.dropna(
        subset=required
    )

    df_w = df_w.dropna(
        subset=[
            "ema20",
            "ema50",
            "rsi",
            "macd",
            "macd_signal",
            "ema20_slope"
        ]
    )

    df_m = df_m.dropna(
        subset=[
            "ema20",
            "ema50",
            "rsi",
            "macd",
            "macd_signal",
            "ema20_slope"
        ]
    )

    if (
        df_d.empty or
        df_w.empty or
        df_m.empty
    ):

        raise ValueError(
            "المؤشرات غير متاحة"
        )

    d = df_d.iloc[-1]
    w = df_w.iloc[-1]
    m = df_m.iloc[-1]

    # Alignment
    alignment = (
        timeframe_score(df_d) * 0.40 +
        timeframe_score(df_w) * 0.35 +
        timeframe_score(df_m) * 0.25
    )

    alignment = min(
        100,
        max(
            0,
            alignment
        )
    )

    regime = market_regime(d)

    entry_info = determine_entry(
        df_d,
        alignment
    )

    entry = float(
        entry_info["price"]
    )

    risk = calculate_risk_engine(
        df_d,
        entry,
        capital,
        risk_percent,
        df_w,
        df_m
    )

    # =====================================================
    # SCORE
    # =====================================================

    score = alignment * 0.25

    # Momentum
    momentum = 0

    rsi = float(d["rsi"])

    if 50 <= rsi <= 65:
        momentum += 7
    elif 45 <= rsi < 50:
        momentum += 5
    elif 65 < rsi <= 70:
        momentum += 5
    elif 35 <= rsi < 45:
        momentum += 2

    if d["macd"] > d["macd_signal"]:
        momentum += 5
    elif d["macd_hist"] > 0:
        momentum += 3

    if d["stoch_rsi_k"] > d["stoch_rsi_d"]:
        momentum += 3

    score += min(
        15,
        momentum
    )

    # Money
    money = 0

    volume_ratio = float(
        d["volume_ratio"]
    )

    if volume_ratio >= 2:
        money += 5
    elif volume_ratio >= 1.5:
        money += 4
    elif volume_ratio >= 1.1:
        money += 3
    elif volume_ratio >= 0.8:
        money += 1

    mfi = float(d["mfi"])

    if 50 <= mfi <= 75:
        money += 4
    elif 40 <= mfi < 50:
        money += 2
    elif 75 < mfi <= 85:
        money += 2

    if (
        d["obv"] > d["obv_ma"] and
        d["obv_slope"] > 0
    ):
        money += 6
    elif (
        d["obv"] > d["obv_ma"] or
        d["obv_slope"] > 0
    ):
        money += 4

    score += min(
        10,
        money
    )

    # Trend strength
    adx_val = float(
        d["adx"]
    )

    if adx_val >= 30:
        score += 5
    elif adx_val >= 25:
        score += 4
    elif adx_val >= 20:
        score += 3
    elif adx_val >= 15:
        score += 1

    # Structure
    structure = 0

    if (
        d["ema20_slope"] > 0 and
        d["ema50_slope"] > 0
    ):
        structure += 4
    elif d["ema20_slope"] > 0:
        structure += 2

    if d["Close"] > d["vwap"]:
        structure += 3

    if d["Close"] > d["ema50"]:
        structure += 3

    score += min(
        10,
        structure
    )

    # Entry quality
    if entry_info["type"] == "دخول عند Pullback":
        score += 10
    elif entry_info["type"] == "دخول اختراق":
        score += 9
    elif entry_info["type"] == "دخول فوري":
        score += 7
    else:
        score += 2

    # Target
    score += (
        risk["target_quality"] *
        0.10
    )

    # Risk
    rr1 = risk["rr1"]

    risk_score = 0

    if np.isfinite(rr1):

        if rr1 >= 2:
            risk_score += 3
        elif rr1 >= 1.5:
            risk_score += 2
        elif rr1 >= 1.2:
            risk_score += 1

    if risk["risk_pct"] <= 5:
        risk_score += 2
    elif risk["risk_pct"] <= 8:
        risk_score += 1

    score += min(
        5,
        risk_score
    )

    # EMA200 penalty
    incomplete = sum(
        [
            not bool(
                d["ema200_complete"]
            ),
            not bool(
                w["ema200_complete"]
            ),
            not bool(
                m["ema200_complete"]
            )
        ]
    )

    if incomplete >= 2:
        score -= 4
    elif incomplete == 1:
        score -= 2

    if (
        entry_info["type"] ==
        "انتظار تأكيد"
    ):

        score = min(
            score,
            69
        )

    score = min(
        100,
        max(
            0,
            score
        )
    )

    # Confidence
    base_conf = ai_confidence(
        d,
        w,
        m,
        alignment,
        data_quality
    )

    probs = estimate_probabilities(
        base_conf,
        risk["rr1"],
        risk["rr2"],
        risk["rr3"],
        risk["rr4"],
        alignment,
        adx_val
    )

    # Signal
    if (
        score >= 85 and
        np.isfinite(risk["rr1"]) and
        risk["rr1"] >= 1.5 and
        alignment >= 65 and
        entry_info["type"] != "انتظار تأكيد"
    ):

        signal = "🔥 قوي جداً"

    elif (
        score >= 70 and
        np.isfinite(risk["rr1"]) and
        risk["rr1"] >= 1.3 and
        entry_info["type"] != "انتظار تأكيد"
    ):

        signal = "🟢 قوي"

    elif score >= 55:

        signal = "🟡 متوسط"

    else:

        signal = "⚠️ متابعة"

    volatility = (
        float(d["atr"]) /
        entry
    )

    if volatility > 0.07:
        time_est = "1 - 3 أسابيع"
    elif volatility > 0.04:
        time_est = "3 - 8 أسابيع"
    elif volatility > 0.02:
        time_est = "1 - 3 شهور"
    else:
        time_est = "2 - 4 شهور"

    return {

        "التقييم": round(score, 2),

        "الإشارة": signal,

        "الاتجاه": regime,

        "نوع الدخول": entry_info["type"],

        "سبب الدخول": entry_info["reason"],

        "سعر الدخول": round(entry, 2),

        "وقف الخسارة": round(
            risk["stop"],
            2
        ),

        "الهدف الأول": (
            round(risk["tp1"], 2)
            if np.isfinite(risk["tp1"])
            else np.nan
        ),

        "الهدف الثاني": (
            round(risk["tp2"], 2)
            if np.isfinite(risk["tp2"])
            else np.nan
        ),

        "الهدف الثالث": (
            round(risk["tp3"], 2)
            if np.isfinite(risk["tp3"])
            else np.nan
        ),

        "الهدف الرابع": (
            round(risk["tp4"], 2)
            if np.isfinite(risk["tp4"])
            else np.nan
        ),

        "سبب الهدف الأول": risk["tp1_reason"],
        "سبب الهدف الثاني": risk["tp2_reason"],
        "سبب الهدف الثالث": risk["tp3_reason"],
        "سبب الهدف الرابع": risk["tp4_reason"],

        "نوع الهدف الأول": risk["tp1_category"],
        "نوع الهدف الثاني": risk["tp2_category"],
        "نوع الهدف الثالث": risk["tp3_category"],
        "نوع الهدف الرابع": risk["tp4_category"],

        "ربح الهدف الأول %": round(
            risk["tp1_profit_pct"],
            2
        ) if np.isfinite(
            risk["tp1_profit_pct"]
        ) else np.nan,

        "ربح الهدف الثاني %": round(
            risk["tp2_profit_pct"],
            2
        ) if np.isfinite(
            risk["tp2_profit_pct"]
        ) else np.nan,

        "ربح الهدف الثالث %": round(
            risk["tp3_profit_pct"],
            2
        ) if np.isfinite(
            risk["tp3_profit_pct"]
        ) else np.nan,

        "ربح الهدف الرابع %": round(
            risk["tp4_profit_pct"],
            2
        ) if np.isfinite(
            risk["tp4_profit_pct"]
        ) else np.nan,

        "R/R الهدف الأول": round(
            risk["rr1"],
            2
        ) if np.isfinite(risk["rr1"]) else np.nan,

        "R/R الهدف الثاني": round(
            risk["rr2"],
            2
        ) if np.isfinite(risk["rr2"]) else np.nan,

        "R/R الهدف الثالث": round(
            risk["rr3"],
            2
        ) if np.isfinite(risk["rr3"]) else np.nan,

        "R/R الهدف الرابع": round(
            risk["rr4"],
            2
        ) if np.isfinite(risk["rr4"]) else np.nan,

        "ثقة الهدف الأول %": round(
            probs[0] * 100,
            1
        ),

        "ثقة الهدف الثاني %": round(
            probs[1] * 100,
            1
        ),

        "ثقة الهدف الثالث %": round(
            probs[2] * 100,
            1
        ),

        "ثقة الهدف الرابع %": round(
            probs[3] * 100,
            1
        ),

        "جودة الأهداف": round(
            risk["target_quality"],
            1
        ),

        "EMA200": (
            "✅ مكتمل"
            if incomplete == 0
            else "⚠️ غير مكتمل"
        ),

        "التذبذب ATR %": round(
            volatility * 100,
            2
        ),

        "قوة الاتجاه ADX": round(
            adx_val,
            2
        ),

        "مؤشر RSI": round(
            rsi,
            2
        ),

        "المدة المتوقعة": time_est,

        "السيولة Ratio": round(
            float(
                d.get(
                    "liquidity_ratio",
                    0
                )
            ),
            2
        ),

        "Relative Strength %": np.nan,

        "Trend Alignment": round(
            alignment,
            2
        ),

        "عدد الأهداف الهيكلية": int(
            risk["structural_target_count"]
        ),

        "_position_size": round(
            risk["position_size"],
            2
        ),

        "_position_value": round(
            risk["position_value"],
            2
        ),

        "_data_quality": round(
            data_quality,
            2
        )
    }


# =========================================================
# 🧪 REAL HISTORICAL BACKTEST
# =========================================================

def run_real_backtest(
    df,
    max_bars=300,
    risk_pct=2.0,
    fee_pct=0.15,
    slippage_pct=0.10,
    initial_equity=100000.0
):

    empty = {

        "trades": 0,
        "win_rate": 0.0,
        "profit_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "profit_factor": 0.0,
        "expectancy_r": 0.0,

        "avg_win_pct": 0.0,
        "avg_loss_pct": 0.0,

        "final_equity": initial_equity,

        "sharpe": 0.0,
        "sortino": 0.0,

        "avg_bars": 0.0,

        "tp1_hits": 0,
        "tp2_hits": 0,
        "tp3_hits": 0,
        "tp4_hits": 0,

        "backtest_bars": 0
    }

    if (
        df is None or
        df.empty or
        len(df) <
        BACKTEST_WARMUP + 50
    ):

        return empty

    # =====================================================
    # FULL INDICATOR HISTORY FIRST
    # =====================================================

    context = build_historical_context(
        df
    )

    context = context.dropna(
        subset=[
            "Close",
            "Open",
            "High",
            "Low",
            "ema20",
            "ema50",
            "rsi",
            "macd",
            "macd_signal",
            "atr",
            "adx",
            "historical_alignment"
        ]
    ).copy()

    if len(context) < BACKTEST_WARMUP + 20:
        return empty

    # =====================================================
    # EXACT TEST WINDOW
    #
    # max_bars = number of bars tested
    # =====================================================

    test_start = max(
        BACKTEST_WARMUP,
        len(context) - max_bars
    )

    if test_start >= len(context) - 2:
        return empty

    equity = float(
        initial_equity
    )

    peak = equity

    max_dd = 0.0

    trades = []

    i = test_start

    fee_rate = (
        fee_pct / 100
    )

    slip_rate = (
        slippage_pct / 100
    )

    # =====================================================
    # HELPERS
    # =====================================================

    def finite(value):

        try:

            return np.isfinite(
                float(value)
            )

        except Exception:

            return False

    def get(row, col):

        value = row.get(
            col,
            np.nan
        )

        return (
            float(value)
            if finite(value)
            else np.nan
        )

    # =====================================================
    # LOOP
    # =====================================================

    while i < len(context) - 2:

        row = context.iloc[i]

        required = [
            "Close",
            "Open",
            "High",
            "Low",
            "ema20",
            "ema50",
            "rsi",
            "macd",
            "macd_signal",
            "atr",
            "historical_alignment"
        ]

        if not all(
            finite(row.get(c, np.nan))
            for c in required
        ):

            i += 1
            continue

        close = float(
            row["Close"]
        )

        ema20 = float(
            row["ema20"]
        )

        ema50 = float(
            row["ema50"]
        )

        rsi = float(
            row["rsi"]
        )

        macd = float(
            row["macd"]
        )

        macd_signal = float(
            row["macd_signal"]
        )

        atr_val = float(
            row["atr"]
        )

        alignment = float(
            row["historical_alignment"]
        )

        volume_ratio = get(
            row,
            "volume_ratio"
        )

        body_pct = get(
            row,
            "body_pct"
        )

        previous_resistance = get(
            row,
            "previous_resistance"
        )

        previous_support = get(
            row,
            "previous_support"
        )

        confirmed_swing_low = get(
            row,
            "confirmed_swing_low"
        )

        confirmed_swing_high = get(
            row,
            "confirmed_swing_high"
        )

        # =================================================
        # SIGNAL
        # =================================================

        breakout = (
            finite(previous_resistance) and
            close > previous_resistance and
            finite(volume_ratio) and
            volume_ratio >= 1.5 and
            finite(body_pct) and
            body_pct >= 0.45 and
            close > ema20 > ema50 and
            alignment >= 60
        )

        # Historical pullback approximation
        distance20 = (
            abs(close - ema20) /
            (close + 1e-9)
        )

        distance50 = (
            abs(close - ema50) /
            (close + 1e-9)
        )

        near_ema = (
            distance20 <= 0.025 or
            distance50 <= 0.035
        )

        support_near = (
            finite(previous_support) and
            abs(
                close -
                previous_support
            )
            /
            (close + 1e-9)
            <= 0.04
        )

        trend_bullish = (
            close > ema50 and
            ema20 > ema50 and
            get(
                row,
                "ema20_slope"
            ) > 0
        )

        fib_support = (
            (
                finite(
                    get(row, "fib_382")
                ) and
                abs(
                    close -
                    get(row, "fib_382")
                )
                /
                (close + 1e-9)
                <= 0.025
            )
            or
            (
                finite(
                    get(row, "fib_500")
                ) and
                abs(
                    close -
                    get(row, "fib_500")
                )
                /
                (close + 1e-9)
                <= 0.025
            )
            or
            (
                finite(
                    get(row, "fib_618")
                ) and
                abs(
                    close -
                    get(row, "fib_618")
                )
                /
                (close + 1e-9)
                <= 0.025
            )
        )

        close_location = get(
            row,
            "close_location"
        )

        reduced_selling = (
            finite(volume_ratio) and
            volume_ratio <= 1.30 and
            finite(close_location) and
            close_location >= 0.45
        )

        bullish_confirmation = (
            (
                bool(
                    row.get(
                        "bullish_candle",
                        False
                    )
                )
                and
                body_pct >= 0.35
            )
            or
            close > ema20
        )

        pullback_score = (
            int(trend_bullish) * 2 +
            int(near_ema) * 2 +
            int(support_near) +
            int(fib_support) +
            int(reduced_selling) +
            int(bullish_confirmation)
        )

        pullback = (
            pullback_score >= 6 and
            trend_bullish and
            alignment >= 55
        )

        immediate = (
            close > ema20 and
            close > ema50 and
            rsi >= 50 and
            macd > macd_signal and
            finite(
                get(row, "vwap")
            ) and
            close > get(row, "vwap") and
            finite(volume_ratio) and
            volume_ratio >= 1.0 and
            alignment >= 50
        )

        if not (
            breakout or
            pullback or
            immediate
        ):

            i += 1
            continue

        # =================================================
        # ENTRY = NEXT BAR OPEN
        # =================================================

        entry_index = i + 1

        entry_bar = context.iloc[
            entry_index
        ]

        raw_entry = float(
            entry_bar["Open"]
        )

        if (
            not np.isfinite(raw_entry) or
            raw_entry <= 0
        ):

            i += 1
            continue

        entry = (
            raw_entry *
            (1 + slip_rate)
        )

        # =================================================
        # STOP
        # =================================================

        stop_candidates = []

        for value in [
            previous_support,
            confirmed_swing_low
        ]:

            if (
                finite(value) and
                0 < value < entry
            ):

                stop_candidates.append(
                    value -
                    atr_val * 0.20
                )

        if not stop_candidates:

            stop_candidates.append(
                entry -
                atr_val * 1.5
            )

        valid_stops = [
            x for x in stop_candidates
            if 0 < x < entry
        ]

        stop = (
            max(valid_stops)
            if valid_stops
            else entry * 0.95
        )

        risk_per_share = (
            entry - stop
        )

        if (
            risk_per_share <= 0 or
            not np.isfinite(
                risk_per_share
            )
        ):

            i += 1
            continue

        # =================================================
        # TARGETS
        #
        # All calculated from SIGNAL BAR ONLY
        # =================================================

        candidates = []

        def add_candidate(
            value,
            category
        ):

            if (
                finite(value) and
                value > entry
            ):

                candidates.append(
                    (
                        float(value),
                        category
                    )
                )

        add_candidate(
            previous_resistance,
            "Resistance"
        )

        add_candidate(
            get(row, "resistance"),
            "Resistance"
        )

        add_candidate(
            confirmed_swing_high,
            "Swing High"
        )

        add_candidate(
            get(row, "fib_ext_1272"),
            "Fibonacci"
        )

        add_candidate(
            get(row, "fib_ext_1618"),
            "Fibonacci"
        )

        add_candidate(
            get(row, "fib_ext_2000"),
            "Fibonacci"
        )

        # Historical weekly/monthly levels
        weekly_high = get(
            row,
            "weekly_previous_high"
        )

        monthly_high = get(
            row,
            "monthly_previous_high"
        )

        add_candidate(
            weekly_high,
            "Weekly"
        )

        add_candidate(
            monthly_high,
            "Monthly"
        )

        candidates.sort(
            key=lambda x: x[0]
        )

        targets = []

        min_gap = max(
            atr_val * 0.40,
            entry * 0.012
        )

        for value, category in candidates:

            if (
                not targets or
                value >=
                targets[-1][0] +
                min_gap
            ):

                targets.append(
                    (
                        value,
                        category
                    )
                )

            if len(targets) >= 4:
                break

        if not targets:

            i += 1
            continue

        # =================================================
        # POSITION SIZE
        # =================================================

        risk_cash = (
            equity *
            risk_pct /
            100
        )

        qty = (
            risk_cash /
            risk_per_share
        )

        if (
            not np.isfinite(qty) or
            qty <= 0
        ):

            i += 1
            continue

        entry_fee = (
            qty *
            entry *
            fee_rate
        )

        if entry_fee >= risk_cash:

            i += 1
            continue

        qty_remaining = qty

        realized_pnl = (
            -entry_fee
        )

        tp_hits = [
            False,
            False,
            False,
            False
        ]

        exit_index = entry_index

        exit_reason = "EOD"

        # =================================================
        # TRADE MANAGEMENT
        # =================================================

        for j in range(
            entry_index + 1,
            len(context)
        ):

            bar = context.iloc[j]

            bar_open = float(
                bar["Open"]
            )

            bar_high = float(
                bar["High"]
            )

            bar_low = float(
                bar["Low"]
            )

            # ---------------------------------------------
            # STOP FIRST
            # ---------------------------------------------

            if bar_low <= stop:

                if bar_open < stop:

                    exit_price = (
                        bar_open *
                        (1 - slip_rate)
                    )

                else:

                    exit_price = (
                        stop *
                        (1 - slip_rate)
                    )

                realized_pnl += (
                    qty_remaining *
                    (
                        exit_price -
                        entry
                    )
                )

                realized_pnl -= (
                    qty_remaining *
                    exit_price *
                    fee_rate
                )

                qty_remaining = 0

                exit_index = j

                exit_reason = "SL"

                break

            # ---------------------------------------------
            # TARGETS
            # ---------------------------------------------

            for k in range(
                len(targets)
            ):

                if tp_hits[k]:
                    continue

                target_price = (
                    targets[k][0]
                )

                if bar_high >= target_price:

                    if k < len(targets) - 1:

                        sell_qty = (
                            qty / 4
                        )

                    else:

                        sell_qty = (
                            qty_remaining
                        )

                    sell_qty = min(
                        sell_qty,
                        qty_remaining
                    )

                    if sell_qty <= 0:
                        continue

                    exit_price = (
                        target_price *
                        (1 - slip_rate)
                    )

                    realized_pnl += (
                        sell_qty *
                        (
                            exit_price -
                            entry
                        )
                    )

                    realized_pnl -= (
                        sell_qty *
                        exit_price *
                        fee_rate
                    )

                    qty_remaining -= (
                        sell_qty
                    )

                    tp_hits[k] = True

                    if qty_remaining <= (
                        qty * 1e-8
                    ):

                        qty_remaining = 0

                        exit_index = j

                        exit_reason = (
                            f"TP{k + 1}"
                        )

                        break

            if qty_remaining <= 0:
                break

        # =================================================
        # FINAL CLOSE
        # =================================================

        if qty_remaining > 0:

            final_close = float(
                context.iloc[-1]["Close"]
            )

            exit_price = (
                final_close *
                (1 - slip_rate)
            )

            realized_pnl += (
                qty_remaining *
                (
                    exit_price -
                    entry
                )
            )

            realized_pnl -= (
                qty_remaining *
                exit_price *
                fee_rate
            )

            qty_remaining = 0

            exit_index = (
                len(context) - 1
            )

            exit_reason = "EOD"

        # =================================================
        # RESULT
        # =================================================

        entry_cost = (
            qty *
            entry
        ) + entry_fee

        return_pct = (
            realized_pnl /
            max(
                entry_cost,
                1e-9
            )
            * 100
        )

        r_multiple = (
            realized_pnl /
            max(
                risk_cash,
                1e-9
            )
        )

        equity += (
            realized_pnl
        )

        peak = max(
            peak,
            equity
        )

        drawdown = (
            peak - equity
        ) / max(
            peak,
            1e-9
        )

        max_dd = max(
            max_dd,
            drawdown
        )

        trades.append(
            {
                "return_pct": return_pct,
                "r": r_multiple,
                "bars": (
                    exit_index -
                    entry_index
                ),
                "reason": exit_reason,
                "tp1": tp_hits[0],
                "tp2": tp_hits[1],
                "tp3": tp_hits[2],
                "tp4": tp_hits[3]
            }
        )

        # =================================================
        # IMPORTANT:
        # NO OVERLAPPING TRADES
        # =================================================

        i = max(
            exit_index + 1,
            i + 1
        )

    # =====================================================
    # STATS
    # =====================================================

    if not trades:

        empty["backtest_bars"] = (
            len(context) - test_start
        )

        return empty

    returns = np.array(
        [
            x["return_pct"]
            for x in trades
        ],
        dtype=float
    )

    r_values = np.array(
        [
            x["r"]
            for x in trades
        ],
        dtype=float
    )

    wins = returns[
        returns > 0
    ]

    losses = returns[
        returns < 0
    ]

    gross_profit = (
        wins.sum()
        if len(wins)
        else 0
    )

    gross_loss = abs(
        losses.sum()
    ) if len(losses) else 0

    profit_factor = (
        gross_profit /
        gross_loss
        if gross_loss > 0
        else (
            999.0
            if gross_profit > 0
            else 0.0
        )
    )

    # Sharpe
    if (
        len(returns) > 1 and
        np.std(
            returns,
            ddof=1
        ) > 0
    ):

        sharpe = (
            np.mean(returns) /
            np.std(
                returns,
                ddof=1
            )
            *
            np.sqrt(
                len(returns)
            )
        )

    else:

        sharpe = 0.0

    # Sortino
    downside = returns[
        returns < 0
    ]

    if (
        len(downside) > 1 and
        np.std(
            downside,
            ddof=1
        ) > 0
    ):

        sortino = (
            np.mean(returns) /
            np.std(
                downside,
                ddof=1
            )
            *
            np.sqrt(
                len(returns)
            )
        )

    else:

        sortino = 0.0

    return {

        "trades": len(trades),

        "win_rate": (
            len(wins) /
            len(trades) *
            100
        ),

        "profit_pct": (
            equity /
            initial_equity -
            1
        ) * 100,

        "max_drawdown_pct": (
            max_dd * 100
        ),

        "profit_factor": profit_factor,

        "expectancy_r": (
            np.mean(r_values)
        ),

        "avg_win_pct": (
            np.mean(wins)
            if len(wins)
            else 0
        ),

        "avg_loss_pct": (
            np.mean(losses)
            if len(losses)
            else 0
        ),

        "final_equity": equity,

        "sharpe": float(
            sharpe
        ),

        "sortino": float(
            sortino
        ),

        "avg_bars": float(
            np.mean(
                [
                    x["bars"]
                    for x in trades
                ]
            )
        ),

        "tp1_hits": sum(
            x["tp1"]
            for x in trades
        ),

        "tp2_hits": sum(
            x["tp2"]
            for x in trades
        ),

        "tp3_hits": sum(
            x["tp3"]
            for x in trades
        ),

        "tp4_hits": sum(
            x["tp4"]
            for x in trades
        ),

        "backtest_bars": (
            len(context) -
            test_start
        )
    }


# =========================================================
# 📊 MARKET RETURN PROXY
# =========================================================

def build_market_return_proxy(
    data,
    symbols
):

    returns = []

    for symbol in symbols:

        try:

            d = extract_symbol_data(
                data,
                symbol
            )

            if (
                not d.empty and
                len(d) >=
                RS_LOOKBACK + 1
            ):

                r = (
                    d["Close"]
                    .pct_change(
                        RS_LOOKBACK
                    )
                    .iloc[-1]
                )

                if np.isfinite(r):

                    returns.append(
                        float(r)
                    )

        except Exception:
            pass

    if not returns:
        return 0.0

    return float(
        np.median(
            returns
        )
    )


# =========================================================
# ⚡ PROCESS STOCK
# =========================================================

def process(
    symbol,
    daily,
    weekly,
    monthly,
    capital,
    risk_percent,
    market_return_20,
    run_backtest,
    backtest_bars,
    backtest_risk_pct,
    backtest_fee_pct,
    backtest_slippage_pct
):

    clean_symbol = (
        symbol.replace(
            ".CA",
            ""
        )
    )

    try:

        df_d = extract_symbol_data(
            daily,
            symbol
        )

        df_w = extract_symbol_data(
            weekly,
            symbol
        )

        df_m = extract_symbol_data(
            monthly,
            symbol
        )

        if df_d.empty:
            return {
                "السهم": clean_symbol,
                "الحالة": "❌ لا توجد Daily"
            }

        if df_w.empty:
            return {
                "السهم": clean_symbol,
                "الحالة": "❌ لا توجد Weekly"
            }

        if df_m.empty:
            return {
                "السهم": clean_symbol,
                "الحالة": "❌ لا توجد Monthly"
            }

        if len(df_d) < MIN_DAILY_ROWS:
            return {
                "السهم": clean_symbol,
                "الحالة": "❌ Daily غير كافية"
            }

        if len(df_w) < MIN_WEEKLY_ROWS:
            return {
                "السهم": clean_symbol,
                "الحالة": "❌ Weekly غير كافية"
            }

        if len(df_m) < MIN_MONTHLY_ROWS:
            return {
                "السهم": clean_symbol,
                "الحالة": "❌ Monthly غير كافية"
            }

        # =================================================
        # CURRENT ANALYSIS
        # =================================================

        result = analyze(
            df_d,
            df_w,
            df_m,
            capital,
            risk_percent
        )

        # Relative Strength
        current_return = (
            df_d["Close"]
            .pct_change(
                RS_LOOKBACK
            )
            .iloc[-1]
        )

        if np.isfinite(
            current_return
        ):

            rs = (
                current_return -
                market_return_20
            ) * 100

        else:

            rs = np.nan

        result["Relative Strength %"] = (
            round(
                rs,
                2
            )
            if np.isfinite(rs)
            else np.nan
        )

        # =================================================
        # BACKTEST
        # =================================================

        if run_backtest:

            bt = run_real_backtest(
                df_d,
                max_bars=backtest_bars,
                risk_pct=backtest_risk_pct,
                fee_pct=backtest_fee_pct,
                slippage_pct=backtest_slippage_pct,
                initial_equity=capital
            )

            result["Backtest Bars"] = (
                bt["backtest_bars"]
            )

            result["Backtest Trades"] = (
                bt["trades"]
            )

            result["Backtest Win Rate %"] = round(
                bt["win_rate"],
                1
            )

            result["Backtest Return %"] = round(
                bt["profit_pct"],
                2
            )

            result["Backtest Max DD %"] = round(
                bt["max_drawdown_pct"],
                2
            )

            result["Backtest Profit Factor"] = round(
                bt["profit_factor"],
                2
            )

            result["Backtest Expectancy R"] = round(
                bt["expectancy_r"],
                3
            )

            result["Backtest Sharpe"] = round(
                bt["sharpe"],
                2
            )

            result["Backtest Sortino"] = round(
                bt["sortino"],
                2
            )

            result["Backtest Avg Bars"] = round(
                bt["avg_bars"],
                1
            )

            result["Backtest TP1 Hits"] = (
                bt["tp1_hits"]
            )

            result["Backtest TP2 Hits"] = (
                bt["tp2_hits"]
            )

            result["Backtest TP3 Hits"] = (
                bt["tp3_hits"]
            )

            result["Backtest TP4 Hits"] = (
                bt["tp4_hits"]
            )

        else:

            result["Backtest Bars"] = np.nan
            result["Backtest Trades"] = 0
            result["Backtest Win Rate %"] = np.nan
            result["Backtest Return %"] = np.nan
            result["Backtest Max DD %"] = np.nan
            result["Backtest Profit Factor"] = np.nan
            result["Backtest Expectancy R"] = np.nan
            result["Backtest Sharpe"] = np.nan
            result["Backtest Sortino"] = np.nan
            result["Backtest Avg Bars"] = np.nan
            result["Backtest TP1 Hits"] = 0
            result["Backtest TP2 Hits"] = 0
            result["Backtest TP3 Hits"] = 0
            result["Backtest TP4 Hits"] = 0

        result["السهم"] = clean_symbol

        result["الحالة"] = (
            "✅ تم التحليل"
        )

        return result

    except Exception as e:

        return {
            "السهم": clean_symbol,
            "الحالة": (
                f"❌ {str(e)[:180]}"
            )
        }


# =========================================================
# 🚀 RUN
# =========================================================

if st.button(
    "🚀 بدء فحص الأسهم",
    use_container_width=True
):

    st.info(
        f"📡 جاري فحص {TOTAL_STOCKS} سهم..."
    )

    progress = st.progress(0)

    status_text = st.empty()

    # =====================================================
    # DAILY
    # =====================================================

    with st.spinner(
        "📥 تحميل Daily MAX..."
    ):

        daily = load_data(
            EGX100,
            period_daily,
            "1d"
        )

    progress.progress(20)

    # =====================================================
    # WEEKLY
    # =====================================================

    status_text.info(
        "📥 تحميل Weekly MAX..."
    )

    weekly = load_data(
        EGX100,
        period_weekly,
        "1wk"
    )

    progress.progress(35)

    # =====================================================
    # MONTHLY
    # =====================================================

    status_text.info(
        "📥 تحميل Monthly MAX..."
    )

    monthly = load_data(
        EGX100,
        period_monthly,
        "1mo"
    )

    progress.progress(50)

    # =====================================================
    # DATA QUALITY
    # =====================================================

    status_text.info(
        "🔍 فحص جودة البيانات..."
    )

    data_engine_stats = []

    for symbol in EGX100:

        d = extract_symbol_data(
            daily,
            symbol
        )

        w = extract_symbol_data(
            weekly,
            symbol
        )

        m = extract_symbol_data(
            monthly,
            symbol
        )

        qd = calculate_data_quality(d)
        qw = calculate_data_quality(w)
        qm = calculate_data_quality(m)

        quality = (
            qd["quality"] * 0.50 +
            qw["quality"] * 0.30 +
            qm["quality"] * 0.20
        )

        data_engine_stats.append(
            {
                "symbol": symbol,
                "daily_rows": qd["rows"],
                "weekly_rows": qw["rows"],
                "monthly_rows": qm["rows"],
                "daily_quality": qd["quality"],
                "weekly_quality": qw["quality"],
                "monthly_quality": qm["quality"],
                "data_quality": round(
                    quality,
                    2
                ),
                "daily_ema200": (
                    "✅"
                    if qd["rows"] >= 200
                    else "⚠️"
                ),
                "weekly_ema200": (
                    "✅"
                    if qw["rows"] >= 200
                    else "⚠️"
                ),
                "monthly_ema200": (
                    "✅"
                    if qm["rows"] >= 200
                    else "⚠️"
                )
            }
        )

    # =====================================================
    # MARKET PROXY
    # =====================================================

    market_return_20 = (
        build_market_return_proxy(
            daily,
            EGX100
        )
    )

    # =====================================================
    # PROCESS
    # =====================================================

    results = []

    status_text.info(
        f"🧠 تحليل {TOTAL_STOCKS} سهم..."
    )

    with ThreadPoolExecutor(
        max_workers=max_workers
    ) as executor:

        futures = {

            executor.submit(
                process,
                symbol,
                daily,
                weekly,
                monthly,
                capital,
                risk_percent,
                market_return_20,
                run_backtest,
                backtest_bars,
                backtest_risk_pct,
                backtest_fee_pct,
                backtest_slippage_pct
            ): symbol

            for symbol in EGX100
        }

        completed = 0

        for future in as_completed(
            futures
        ):

            symbol = futures[
                future
            ]

            try:

                result = (
                    future.result()
                )

                results.append(
                    result
                )

            except Exception as e:

                results.append(
                    {
                        "السهم": symbol.replace(
                            ".CA",
                            ""
                        ),
                        "الحالة": (
                            f"❌ {str(e)[:180]}"
                        )
                    }
                )

            completed += 1

            progress.progress(
                50 +
                int(
                    completed /
                    TOTAL_STOCKS *
                    50
                )
            )

    progress.progress(100)

    status_text.success(
        "✅ انتهى الفحص"
    )

    # =====================================================
    # DATAFRAME
    # =====================================================

    if not results:

        st.error(
            "❌ لم يتم الحصول على نتائج"
        )

        st.stop()

    df_all = pd.DataFrame(
        results
    )

    df_ok = df_all[
        df_all["الحالة"] ==
        "✅ تم التحليل"
    ].copy()

    # =====================================================
    # SUMMARY
    # =====================================================

    total = TOTAL_STOCKS

    analyzed = len(df_ok)

    failed = (
        total -
        analyzed
    )

    coverage = (
        analyzed /
        total *
        100
    )

    stats_df = pd.DataFrame(
        data_engine_stats
    )

    avg_quality = float(
        stats_df[
            "data_quality"
        ].mean()
    )

    daily_coverage = (
        (
            stats_df[
                "daily_rows"
            ] >= MIN_DAILY_ROWS
        ).mean()
        * 100
    )

    weekly_coverage = (
        (
            stats_df[
                "weekly_rows"
            ] >= MIN_WEEKLY_ROWS
        ).mean()
        * 100
    )

    monthly_coverage = (
        (
            stats_df[
                "monthly_rows"
            ] >= MIN_MONTHLY_ROWS
        ).mean()
        * 100
    )

    daily_ema200_coverage = (
        (
            stats_df[
                "daily_rows"
            ] >= 200
        ).mean()
        * 100
    )

    weekly_ema200_coverage = (
        (
            stats_df[
                "weekly_rows"
            ] >= 200
        ).mean()
        * 100
    )

    monthly_ema200_coverage = (
        (
            stats_df[
                "monthly_rows"
            ] >= 200
        ).mean()
        * 100
    )

    # =====================================================
    # SUMMARY UI
    # =====================================================

    st.subheader(
        "📊 ملخص الفحص"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "📊 الأسهم",
        total
    )

    c2.metric(
        "✅ تم التحليل",
        analyzed
    )

    c3.metric(
        "❌ فشل",
        failed
    )

    c4.metric(
        "📡 التغطية",
        f"{coverage:.1f}%"
    )

    # =====================================================
    # DATA QUALITY
    # =====================================================

    st.subheader(
        "📡 جودة البيانات"
    )

    q1, q2, q3, q4 = st.columns(4)

    q1.metric(
        "⭐ الجودة",
        f"{avg_quality:.1f}%"
    )

    q2.metric(
        "📅 Daily",
        f"{daily_coverage:.1f}%"
    )

    q3.metric(
        "📆 Weekly",
        f"{weekly_coverage:.1f}%"
    )

    q4.metric(
        "🗓️ Monthly",
        f"{monthly_coverage:.1f}%"
    )

    st.subheader(
        "📐 EMA200 الحقيقي"
    )

    e1, e2, e3 = st.columns(3)

    e1.metric(
        "Daily EMA200",
        f"{daily_ema200_coverage:.1f}%"
    )

    e2.metric(
        "Weekly EMA200",
        f"{weekly_ema200_coverage:.1f}%"
    )

    e3.metric(
        "Monthly EMA200",
        f"{monthly_ema200_coverage:.1f}%"
    )

    # =====================================================
    # RESULTS
    # =====================================================

    if not df_ok.empty:

        df_ok = df_ok.sort_values(
            "التقييم",
            ascending=False
        )

        # =================================================
        # TARGET WARNING
        # =================================================

        if (
            "عدد الأهداف الهيكلية"
            in df_ok.columns
        ):

            no_targets = int(
                (
                    df_ok[
                        "عدد الأهداف الهيكلية"
                    ] < 1
                ).sum()
            )

            if no_targets:

                st.warning(
                    f"⚠️ {no_targets} سهم بدون Target هيكلي موثوق."
                )

        # =================================================
        # TOP STOCKS
        # =================================================

        st.subheader(
            f"🏆 أفضل {min(top_n, len(df_ok))} سهم"
        )

        preferred_cols = [

            "السهم",
            "التقييم",
            "الإشارة",
            "الاتجاه",
            "نوع الدخول",
            "سعر الدخول",
            "وقف الخسارة",

            "الهدف الأول",
            "ربح الهدف الأول %",
            "R/R الهدف الأول",

            "الهدف الثاني",
            "ربح الهدف الثاني %",
            "R/R الهدف الثاني",

            "الهدف الثالث",
            "ربح الهدف الثالث %",
            "R/R الهدف الثالث",

            "الهدف الرابع",
            "ربح الهدف الرابع %",
            "R/R الهدف الرابع",

            "جودة الأهداف",

            "EMA200",

            "مؤشر RSI",
            "قوة الاتجاه ADX",
            "التذبذب ATR %",

            "السيولة Ratio",
            "Relative Strength %",
            "Trend Alignment",

            "عدد الأهداف الهيكلية",

            "Backtest Bars",
            "Backtest Trades",
            "Backtest Win Rate %",
            "Backtest Return %",
            "Backtest Max DD %",
            "Backtest Profit Factor",
            "Backtest Expectancy R",
            "Backtest Sharpe",
            "Backtest Sortino",
            "Backtest Avg Bars",
            "Backtest TP1 Hits",
            "Backtest TP2 Hits",
            "Backtest TP3 Hits",
            "Backtest TP4 Hits",

            "المدة المتوقعة"
        ]

        existing_cols = [
            c for c in preferred_cols
            if c in df_ok.columns
        ]

        top_df = df_ok.head(
            top_n
        )

        st.dataframe(
            top_df[
                existing_cols
            ],
            use_container_width=True,
            hide_index=True
        )

        # =================================================
        # STRONG
        # =================================================

        strong = df_ok[
            df_ok["التقييم"] >= 70
        ].copy()

        st.subheader(
            f"🔥 الأسهم القوية: {len(strong)}"
        )

        if not strong.empty:

            st.dataframe(
                strong[
                    existing_cols
                ],
                use_container_width=True,
                hide_index=True
            )

        else:

            st.warning(
                "⚠️ لا توجد أسهم قوية حاليًا."
            )

        # =================================================
        # ALL
        # =================================================

        st.subheader(
            "📋 جميع الأسهم"
        )

        st.dataframe(
            df_ok[
                existing_cols
            ],
            use_container_width=True,
            hide_index=True
        )

        # =================================================
        # CSV
        # =================================================

        csv = (
            df_ok[
                existing_cols
            ]
            .to_csv(
                index=False
            )
            .encode(
                "utf-8-sig"
            )
        )

        st.download_button(
            "⬇️ تحميل النتائج CSV",
            csv,
            "EGX_AI_PRO_MAX_V8_1_RESULTS_AR.csv",
            "text/csv",
            use_container_width=True
        )

        # =================================================
        # TARGET DETAILS
        # =================================================

        with st.expander(
            "🎯 تفاصيل Target Engine"
        ):

            target_cols = [

                "السهم",
                "سعر الدخول",
                "وقف الخسارة",

                "الهدف الأول",
                "نوع الهدف الأول",
                "سبب الهدف الأول",
                "ربح الهدف الأول %",
                "R/R الهدف الأول",

                "الهدف الثاني",
                "نوع الهدف الثاني",
                "سبب الهدف الثاني",
                "ربح الهدف الثاني %",
                "R/R الهدف الثاني",

                "الهدف الثالث",
                "نوع الهدف الثالث",
                "سبب الهدف الثالث",
                "ربح الهدف الثالث %",
                "R/R الهدف الثالث",

                "الهدف الرابع",
                "نوع الهدف الرابع",
                "سبب الهدف الرابع",
                "ربح الهدف الرابع %",
                "R/R الهدف الرابع",

                "جودة الأهداف"
            ]

            available = [
                c for c in target_cols
                if c in df_ok.columns
            ]

            st.dataframe(
                df_ok[
                    available
                ],
                use_container_width=True,
                hide_index=True
            )

        # =================================================
        # ENTRY
        # =================================================

        with st.expander(
            "🎯 تفاصيل Entry Engine"
        ):

            entry_cols = [

                "السهم",
                "التقييم",
                "الإشارة",
                "الاتجاه",
                "نوع الدخول",
                "سبب الدخول",
                "سعر الدخول",
                "وقف الخسارة",
                "Trend Alignment",
                "جودة الأهداف",
                "R/R الهدف الأول",
                "مؤشر RSI",
                "قوة الاتجاه ADX",
                "التذبذب ATR %",
                "EMA200"
            ]

            available = [
                c for c in entry_cols
                if c in df_ok.columns
            ]

            st.dataframe(
                df_ok[
                    available
                ],
                use_container_width=True,
                hide_index=True
            )

        # =================================================
        # BACKTEST DETAILS
        # =================================================

        with st.expander(
            "🧪 تفاصيل Backtest"
        ):

            bt_cols = [

                "السهم",

                "التقييم",

                "Backtest Bars",
                "Backtest Trades",
                "Backtest Win Rate %",
                "Backtest Return %",
                "Backtest Max DD %",
                "Backtest Profit Factor",
                "Backtest Expectancy R",
                "Backtest Sharpe",
                "Backtest Sortino",
                "Backtest Avg Bars",

                "Backtest TP1 Hits",
                "Backtest TP2 Hits",
                "Backtest TP3 Hits",
                "Backtest TP4 Hits"
            ]

            available = [
                c for c in bt_cols
                if c in df_ok.columns
            ]

            bt_df = df_ok[
                available
            ].copy()

            if (
                "Backtest Trades"
                in bt_df.columns
            ):

                bt_df = bt_df.sort_values(
                    "Backtest Return %",
                    ascending=False
                )

            st.dataframe(
                bt_df,
                use_container_width=True,
                hide_index=True
            )

        # =================================================
        # DATA DETAILS
        # =================================================

        with st.expander(
            "📡 تفاصيل جودة البيانات"
        ):

            quality_display = (
                stats_df
                .rename(
                    columns={
                        "symbol": "السهم",
                        "daily_rows": "شموع Daily",
                        "weekly_rows": "شموع Weekly",
                        "monthly_rows": "شموع Monthly",
                        "daily_quality": "جودة Daily %",
                        "weekly_quality": "جودة Weekly %",
                        "monthly_quality": "جودة Monthly %",
                        "data_quality": "جودة البيانات %",
                        "daily_ema200": "Daily EMA200",
                        "weekly_ema200": "Weekly EMA200",
                        "monthly_ema200": "Monthly EMA200"
                    }
                )
            )

            st.dataframe(
                quality_display,
                use_container_width=True,
                hide_index=True
            )

    # =====================================================
    # FAILED
    # =====================================================

    df_failed = df_all[
        df_all["الحالة"] !=
        "✅ تم التحليل"
    ].copy()

    if not df_failed.empty:

        st.subheader(
            f"⚠️ الأسهم الفاشلة: {len(df_failed)}"
        )

        st.dataframe(
            df_failed[
                [
                    "السهم",
                    "الحالة"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        failed_csv = (
            df_failed[
                [
                    "السهم",
                    "الحالة"
                ]
            ]
            .to_csv(
                index=False
            )
            .encode(
                "utf-8-sig"
            )
        )

        st.download_button(
            "⬇️ تحميل الأخطاء",
            failed_csv,
            "EGX_AI_PRO_MAX_V8_1_ERRORS_AR.csv",
            "text/csv",
            use_container_width=True
        )

    # =====================================================
    # FINAL STATUS
    # =====================================================

    st.success(
        f"""
🔥 الفحص اكتمل

📊 إجمالي الأسهم: {total}

✅ تم تحليل: {analyzed}

❌ فشل: {failed}

📡 التغطية: {coverage:.1f}%

⭐ جودة البيانات: {avg_quality:.1f}%

📅 Daily Coverage: {daily_coverage:.1f}%

📆 Weekly Coverage: {weekly_coverage:.1f}%

🗓️ Monthly Coverage: {monthly_coverage:.1f}%

📐 Daily EMA200: {daily_ema200_coverage:.1f}%

📐 Weekly EMA200: {weekly_ema200_coverage:.1f}%

📐 Monthly EMA200: {monthly_ema200_coverage:.1f}%

🧪 Backtest:
{backtest_bars} شمعة اختبار فعلية + Warmup قبلها

💰 العمولة: {backtest_fee_pct:.2f}% لكل جانب

📉 Slippage: {backtest_slippage_pct:.2f}% لكل تنفيذ

⚠️ نتائج الباك تست تاريخية وليست ضمانًا للنتائج المستقبلية.
"""
    )
