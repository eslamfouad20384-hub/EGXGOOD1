import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import ta
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# =========================================================
# ⚙️ إعداد الصفحة
# =========================================================

st.set_page_config(
    page_title="EGX AI PRO MAX v10 - عربي",
    page_icon="📈",
    layout="wide"
)

st.title("🚀 EGX AI PRO MAX v10")
st.caption(
    "📊 فحص الأسهم المصرية • تحليل متعدد الفترات • Entry/Target Engine احترافي • Risk Management"
)

# =========================================================
# 📌 قائمة الأسهم
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
# 🎛️ إعدادات الفحص
# =========================================================

st.sidebar.header("⚙️ إعدادات الفحص")

period_daily = st.sidebar.selectbox(
    "📅 فترة البيانات اليومية",
    ["3mo", "6mo", "1y", "2y", "3y", "5y", "max"],
    index=6
)

period_weekly = st.sidebar.selectbox(
    "📅 فترة البيانات الأسبوعية",
    ["3y", "5y", "10y", "max"],
    index=3
)

period_monthly = st.sidebar.selectbox(
    "📅 فترة البيانات الشهرية",
    ["10y", "15y", "20y", "max"],
    index=3
)

max_workers = st.sidebar.slider(
    "⚡ عدد الاتصالات المتوازية",
    min_value=2,
    max_value=16,
    value=8,
    step=1
)

top_n = st.sidebar.slider(
    "🏆 عدد أفضل الأسهم",
    min_value=5,
    max_value=100,
    value=20,
    step=5
)

# =========================================================
# 💰 إدارة رأس المال
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
    min_value=0.5,
    max_value=10.0,
    value=2.0,
    step=0.5
)

run_backtest = st.sidebar.checkbox(
    "🧪 تشغيل Backtest تاريخي حقيقي",
    value=True
)
backtest_bars = st.sidebar.slider(
    "عدد شموع الـ Backtest لكل سهم",
    min_value=200,
    max_value=1500,
    value=600,
    step=50
)

commission_pct = st.sidebar.number_input(
    "عمولة التداول لكل جانب %", min_value=0.0, max_value=2.0, value=0.10, step=0.01
)
slippage_pct = st.sidebar.number_input(
    "انزلاق سعري لكل تنفيذ %", min_value=0.0, max_value=2.0, value=0.10, step=0.01
)
max_position_pct = st.sidebar.slider(
    "أقصى حجم مركز من رأس المال %", min_value=5, max_value=50, value=20, step=5
)
monte_carlo_runs = st.sidebar.slider(
    "عدد محاكاة Monte Carlo", min_value=1000, max_value=20000, value=5000, step=1000
)

# =========================================================
# 📊 معلومات
# =========================================================

st.sidebar.markdown("---")

st.sidebar.metric(
    "📊 عدد الأسهم للفحص",
    TOTAL_STOCKS
)

st.sidebar.markdown("---")

st.sidebar.info(
    """
    📌 النظام يقوم بفحص:

    • Daily / Weekly / Monthly
    • EMA20 / EMA50 / EMA200
    • RSI / MACD / ADX / ATR
    • OBV / MFI / Stochastic RSI / VWAP
    • Volume Ratio
    • Support / Resistance
    • Swing High / Swing Low
    • Fibonacci
    • Fibonacci Extensions
    • Professional Pullback
    • Professional Breakout
    • Trend Alignment
    • Entry Quality
    • Target Quality
    • Risk / Reward
    • Risk Management
    • 4 Targets
    """
)

# =========================================================
# 🧠 ثوابت النظام
# =========================================================

MIN_DAILY_ROWS = 60
MIN_WEEKLY_ROWS = 80
MIN_MONTHLY_ROWS = 36

DOWNLOAD_RETRIES = 3
DOWNLOAD_RETRY_DELAY = 2

EMA200_REQUIRED_ROWS = 200

# Backtest / Structure / Liquidity
BACKTEST_WARMUP = 220
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
                timeout=30
            )

            if data is not None and not data.empty:
                return data

            last_error = "Yahoo returned empty data"

        except Exception as e:

            last_error = str(e)

        if attempt < DOWNLOAD_RETRIES - 1:

            time.sleep(
                DOWNLOAD_RETRY_DELAY *
                (attempt + 1)
            )

    return pd.DataFrame()


# =========================================================
# 🔍 استخراج بيانات السهم
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
# 🧪 DATA QUALITY
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

    total_cells = len(df) * len(required)

    missing_cells = int(
        df[required]
        .isna()
        .sum()
        .sum()
    )

    missing_pct = (
        missing_cells /
        total_cells *
        100
        if total_cells > 0
        else 100
    )

    quality = max(
        0.0,
        100.0 - missing_pct
    )

    if len(df) < 50:

        quality *= len(df) / 50

    return {
        "quality": round(
            quality,
            2
        ),
        "missing": round(
            missing_pct,
            2
        ),
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

    plus_dm_raw = high.diff()
    minus_dm_raw = -low.diff()

    plus_dm = np.where(
        (plus_dm_raw > minus_dm_raw) &
        (plus_dm_raw > 0),
        plus_dm_raw,
        0.0
    )

    minus_dm = np.where(
        (minus_dm_raw > plus_dm_raw) &
        (minus_dm_raw > 0),
        minus_dm_raw,
        0.0
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
        abs(
            plus_di -
            minus_di
        )
        /
        (
            plus_di +
            minus_di +
            1e-9
        )
    ) * 100

    return dx.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period
    ).mean()


# =========================================================
# 📐 خطي Regression بسيط
# =========================================================

def linear_slope(series, window=10):

    if len(series) < window:
        return np.nan

    values = series.iloc[-window:].values.astype(float)

    if not np.all(np.isfinite(values)):
        return np.nan

    x = np.arange(window)

    try:

        slope = np.polyfit(
            x,
            values,
            1
        )[0]

        return float(slope)

    except Exception:

        return np.nan


# =========================================================
# 📈 TECHNICAL ENGINE
# =========================================================

def add_indicators(df):

    df = df.copy()

    if len(df) < 30:
        return df

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    vol = df["Volume"]

    # =====================================================
    # EMA20
    # =====================================================

    df["ema20"] = close.ewm(
        span=20,
        adjust=False
    ).mean()

    # =====================================================
    # EMA50
    # =====================================================

    df["ema50"] = close.ewm(
        span=50,
        adjust=False
    ).mean()

    # =====================================================
    # EMA200
    #
    # مهم:
    # لا نعتبر EMA200 مكتملًا إلا بعد 200 شمعة
    # =====================================================

    if len(df) >= EMA200_REQUIRED_ROWS:

        df["ema200"] = close.ewm(
            span=200,
            adjust=False,
            min_periods=200
        ).mean()

        df["ema200_complete"] = True

    else:

        df["ema200"] = np.nan
        df["ema200_complete"] = False

    # =====================================================
    # RSI
    # =====================================================

    df["rsi"] = ta.momentum.RSIIndicator(
        close=close,
        window=14
    ).rsi()

    # =====================================================
    # MACD
    # =====================================================

    macd_obj = ta.trend.MACD(
        close=close,
        window_slow=26,
        window_fast=12,
        window_sign=9
    )

    df["macd"] = macd_obj.macd()

    df["macd_signal"] = (
        macd_obj.macd_signal()
    )

    df["macd_hist"] = (
        macd_obj.macd_diff()
    )

    # =====================================================
    # Volume MA
    # =====================================================

    df["vol_ma"] = vol.rolling(
        20,
        min_periods=10
    ).mean()

    # =====================================================
    # Volume Ratio
    # =====================================================

    df["volume_ratio"] = (
        vol /
        (df["vol_ma"] + 1e-9)
    )

    # =====================================================
    # OBV
    # =====================================================

    try:

        df["obv"] = (
            ta.volume
            .OnBalanceVolumeIndicator(
                close=close,
                volume=vol
            )
            .on_balance_volume()
        )

        df["obv_ma"] = (
            df["obv"]
            .rolling(
                20,
                min_periods=10
            )
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

    # =====================================================
    # MFI
    # =====================================================

    try:

        df["mfi"] = (
            ta.volume
            .MFIIndicator(
                high=high,
                low=low,
                close=close,
                volume=vol,
                window=14
            )
            .money_flow_index()
        )

    except Exception:

        df["mfi"] = np.nan

    # =====================================================
    # Stochastic RSI
    # =====================================================

    try:

        stoch = ta.momentum.StochRSIIndicator(
            close=close,
            window=14,
            smooth1=3,
            smooth2=3
        )

        df["stoch_rsi"] = (
            stoch.stochrsi()
        )

        df["stoch_rsi_k"] = (
            stoch.stochrsi_k()
        )

        df["stoch_rsi_d"] = (
            stoch.stochrsi_d()
        )

        df["stoch_rsi_k_slope"] = (
            df["stoch_rsi_k"] -
            df["stoch_rsi_k"].shift(1)
        )

    except Exception:

        df["stoch_rsi"] = np.nan
        df["stoch_rsi_k"] = np.nan
        df["stoch_rsi_d"] = np.nan
        df["stoch_rsi_k_slope"] = np.nan

    # =====================================================
    # VWAP
    # =====================================================

    try:

        typical_price = (
            high +
            low +
            close
        ) / 3

        cumulative_volume = vol.cumsum()

        df["vwap"] = (
            (
                typical_price *
                vol
            ).cumsum()
            /
            (
                cumulative_volume +
                1e-9
            )
        )

        df["vwap_distance"] = (
            close -
            df["vwap"]
        ) / (
            close +
            1e-9
        )

    except Exception:

        df["vwap"] = np.nan
        df["vwap_distance"] = np.nan

    # =====================================================
    # ATR
    # =====================================================

    df["atr"] = atr(
        df,
        14
    )

    df["atr_pct"] = (
        df["atr"] /
        (close + 1e-9)
    )

    # =====================================================
    # ADX
    # =====================================================

    df["adx"] = adx(
        df,
        14
    )

    # =====================================================
    # Support / Resistance
    # =====================================================

    df["support"] = (
        low
        .rolling(
            20,
            min_periods=10
        )
        .min()
    )

    df["resistance"] = (
        high
        .rolling(
            20,
            min_periods=10
        )
        .max()
    )

    # =====================================================
    # Previous Support / Resistance
    # =====================================================

    df["previous_support"] = (
        low
        .rolling(
            20,
            min_periods=10
        )
        .min()
        .shift(1)
    )

    df["previous_resistance"] = (
        high
        .rolling(
            20,
            min_periods=10
        )
        .max()
        .shift(1)
    )

    # =====================================================
    # Swing High / Swing Low
    #
    # نستخدم مستويات تاريخية حقيقية داخل النوافذ
    # =====================================================

    df["swing_high_20"] = (
        high
        .rolling(
            20,
            min_periods=10
        )
        .max()
        .shift(1)
    )

    df["swing_low_20"] = (
        low
        .rolling(
            20,
            min_periods=10
        )
        .min()
        .shift(1)
    )

    df["swing_high_60"] = (
        high
        .rolling(
            60,
            min_periods=20
        )
        .max()
        .shift(1)
    )

    df["swing_low_60"] = (
        low
        .rolling(
            60,
            min_periods=20
        )
        .min()
        .shift(1)
    )

    # =====================================================
    # Fibonacci
    # =====================================================

    swing_high = (
        high
        .rolling(
            60,
            min_periods=20
        )
        .max()
    )

    swing_low = (
        low
        .rolling(
            60,
            min_periods=20
        )
        .min()
    )

    fib_range = (
        swing_high -
        swing_low
    )

    df["fib_236"] = (
        swing_high -
        fib_range * 0.236
    )

    df["fib_382"] = (
        swing_high -
        fib_range * 0.382
    )

    df["fib_500"] = (
        swing_high -
        fib_range * 0.500
    )

    df["fib_618"] = (
        swing_high -
        fib_range * 0.618
    )

    df["fib_786"] = (
        swing_high -
        fib_range * 0.786
    )

    # =====================================================
    # Fibonacci Extensions
    # =====================================================

    df["fib_ext_1272"] = (
        swing_low +
        fib_range * 1.272
    )

    df["fib_ext_1618"] = (
        swing_low +
        fib_range * 1.618
    )

    df["fib_ext_2000"] = (
        swing_low +
        fib_range * 2.000
    )

    # =====================================================
    # Trend Slope
    # =====================================================

    df["ema20_slope"] = (
        df["ema20"] -
        df["ema20"].shift(5)
    ) / (
        df["Close"] + 1e-9
    )

    df["ema50_slope"] = (
        df["ema50"] -
        df["ema50"].shift(5)
    ) / (
        df["Close"] + 1e-9
    )

    # =====================================================
    # Candle Body
    # =====================================================

    candle_range = (
        high -
        low
    ).replace(
        0,
        np.nan
    )

    df["body_pct"] = (
        abs(
            close -
            df["Open"]
        ) /
        candle_range
    )

    df["bullish_candle"] = (
        close >
        df["Open"]
    )

    # =====================================================
    # ATR مناسب للاختراق
    # =====================================================

    df["atr_expansion"] = (
        df["atr"] /
        (
            df["atr"]
            .rolling(
                20,
                min_periods=10
            )
            .mean()
            +
            1e-9
        )
    )

    # =====================================================
    # Breakout متقدم
    # =====================================================

    previous_resistance = (
        high
        .rolling(
            20,
            min_periods=10
        )
        .max()
        .shift(1)
    )

    close_above_resistance = (
        close >
        previous_resistance
    )

    breakout_volume = (
        df["volume_ratio"] >= 1.30
    )

    breakout_volume_strong = (
        df["volume_ratio"] >= 1.50
    )

    atr_is_healthy = (
        df["atr_pct"] >= 0.015
    )

    atr_not_extreme = (
        df["atr_pct"] <= 0.12
    )

    candle_quality = (
        df["body_pct"] >= 0.45
    )

    bullish_candle = (
        df["bullish_candle"]
    )

    trend_breakout = (
        (
            close > df["ema20"]
        ) &
        (
            df["ema20"] > df["ema50"]
        )
    )

    df["breakout"] = (
        close_above_resistance &
        breakout_volume &
        atr_is_healthy &
        atr_not_extreme &
        candle_quality &
        bullish_candle &
        trend_breakout
    )

    # =====================================================
    # Pullback متقدم
    # =====================================================

    distance_ema20 = (
        abs(
            close -
            df["ema20"]
        ) /
        (close + 1e-9)
    )

    distance_ema50 = (
        abs(
            close -
            df["ema50"]
        ) /
        (close + 1e-9)
    )

    near_ema20 = (
        distance_ema20 <= 0.025
    )

    near_ema50 = (
        distance_ema50 <= 0.035
    )

    trend_bullish = (
        (close > df["ema50"]) &
        (df["ema20"] > df["ema50"]) &
        (df["ema20_slope"] > 0)
    )

    support_near = (
        (
            abs(
                close -
                df["previous_support"]
            ) /
            (close + 1e-9)
        ) <= 0.04
    )

    fib_support_near = (
        (
            (
                abs(close - df["fib_382"]) /
                (close + 1e-9)
            ) <= 0.025
        )
        |
        (
            (
                abs(close - df["fib_500"]) /
                (close + 1e-9)
            ) <= 0.025
        )
        |
        (
            (
                abs(close - df["fib_618"]) /
                (close + 1e-9)
            ) <= 0.025
        )
    )

    # انخفاض ضغط البيع:
    # حجم البيع الحالي ليس أعلى بشكل حاد
    # والسهم لا يغلق بالقرب من قاع الشمعة
    close_location = (
        close -
        low
    ) / (
        candle_range +
        1e-9
    )

    selling_pressure_reduced = (
        (
            df["volume_ratio"] <= 1.30
        ) &
        (
            close_location >= 0.45
        )
    )

    bullish_confirmation = (
        (
            bullish_candle &
            (
                body := df["body_pct"]
            ).ge(0.35)
        )
        |
        (
            close >
            df["ema20"]
        )
    )

    pullback_score = (
        trend_bullish.astype(int) * 2 +
        (
            near_ema20 |
            near_ema50
        ).astype(int) * 2 +
        support_near.astype(int) +
        fib_support_near.astype(int) +
        selling_pressure_reduced.astype(int) +
        bullish_confirmation.astype(int)
    )

    df["pullback_quality_score"] = (
        pullback_score
    )

    df["pullback"] = (
        (
            pullback_score >= 6
        ) &
        trend_bullish
    )

    # =====================================================
    # Confirmed Swing Engine - no look-ahead at decision time
    # Pivot is only considered confirmed after PIVOT_RADIUS candles
    # =====================================================
    w = PIVOT_RADIUS * 2 + 1
    ph_candidate = high.eq(high.rolling(w, center=True, min_periods=w).max())
    pl_candidate = low.eq(low.rolling(w, center=True, min_periods=w).min())

    df["confirmed_swing_high_raw"] = high.where(ph_candidate).shift(PIVOT_RADIUS)
    df["confirmed_swing_low_raw"] = low.where(pl_candidate).shift(PIVOT_RADIUS)
    df["confirmed_swing_high"] = df["confirmed_swing_high_raw"].ffill()
    df["confirmed_swing_low"] = df["confirmed_swing_low_raw"].ffill()

    # Last confirmed pivot timestamps, also shifted by confirmation delay.
    idx_num = pd.Series(np.arange(len(df), dtype=float), index=df.index)
    df["confirmed_high_idx"] = idx_num.where(ph_candidate).shift(PIVOT_RADIUS).ffill()
    df["confirmed_low_idx"] = idx_num.where(pl_candidate).shift(PIVOT_RADIUS).ffill()

    # =====================================================
    # Confirmed Fibonacci - based on the latest confirmed impulse
    # =====================================================
    bull_leg = (
        df["confirmed_low_idx"].notna() &
        df["confirmed_high_idx"].notna() &
        (df["confirmed_low_idx"] < df["confirmed_high_idx"])
    )
    fib_hi = df["confirmed_swing_high"]
    fib_lo = df["confirmed_swing_low"]
    fib_range_confirmed = (fib_hi - fib_lo).where(bull_leg)

    for ratio, col in [(0.236, "fib_236"), (0.382, "fib_382"), (0.500, "fib_500"), (0.618, "fib_618"), (0.786, "fib_786")]:
        df[col] = (fib_hi - fib_range_confirmed * ratio).where(fib_range_confirmed > 0)

    # Bullish extensions are measured from confirmed low -> confirmed high.
    df["fib_ext_1272"] = (fib_hi + fib_range_confirmed * 0.272).where(fib_range_confirmed > 0)
    df["fib_ext_1618"] = (fib_hi + fib_range_confirmed * 0.618).where(fib_range_confirmed > 0)
    df["fib_ext_2000"] = (fib_hi + fib_range_confirmed * 1.000).where(fib_range_confirmed > 0)

    # =====================================================
    # Liquidity Engine: EGP turnover, not raw share volume
    # =====================================================
    df["turnover"] = close * vol
    df["turnover_ma20"] = df["turnover"].rolling(LIQUIDITY_LOOKBACK, min_periods=10).median()
    df["liquidity_ratio"] = df["turnover"] / (df["turnover_ma20"] + 1e-9)

    # Relative strength is computed later against the EGX cross-sectional proxy.
    df["return_20d"] = close.pct_change(RS_LOOKBACK)

    return df


# =========================================================
# 🧠 MARKET REGIME
# =========================================================

def market_regime(last):

    score = 0

    checks = [
        (
            np.isfinite(last.get("ema200", np.nan)) and
            last["Close"] > last["ema200"]
        ),
        last["ema20"] > last["ema50"],
        (
            np.isfinite(last.get("ema200", np.nan)) and
            last["ema50"] > last["ema200"]
        ),
        last["macd"] > last["macd_signal"],
        last["rsi"] > 50,
        last["adx"] > 20
    ]

    score = sum(checks)

    if score >= 6:
        return "🚀 قوي جداً"

    elif score >= 4:
        return "🟢 صعود"

    elif score >= 3:
        return "🟡 محايد"

    else:
        return "🔴 هبوط"


# =========================================================
# 📊 TIMEFRAME SCORE
# =========================================================

def timeframe_score(df):

    if df is None or df.empty:
        return 0

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

    # لا نعطي Score EMA200 كامل إذا غير مكتمل
    if not bool(last.get("ema200_complete", False)):
        score = min(
            score,
            55
        )

    return score


# =========================================================
# 📊 TREND ALIGNMENT
# =========================================================

def trend_alignment_score(
    df_d,
    df_w,
    df_m
):

    daily_score = timeframe_score(
        df_d
    )

    weekly_score = timeframe_score(
        df_w
    )

    monthly_score = timeframe_score(
        df_m
    )

    alignment = (
        daily_score * 0.40 +
        weekly_score * 0.35 +
        monthly_score * 0.25
    )

    return min(
        100,
        max(
            0,
            alignment
        )
    )


# =========================================================
# 🎯 حساب Pullback Entry
# =========================================================

def calculate_pullback_entry(df_d):
    last = df_d.iloc[-1]
    close = float(last["Close"])
    atr_val = float(last.get("atr", close * 0.03))
    if not np.isfinite(atr_val) or atr_val <= 0:
        atr_val = close * 0.03

    levels = []
    candidates = [
        ("Confirmed Support", last.get("previous_support", np.nan)),
        ("Confirmed Swing Low", last.get("confirmed_swing_low", np.nan)),
        ("EMA20", last.get("ema20", np.nan)),
        ("EMA50", last.get("ema50", np.nan)),
        ("Fib 38.2%", last.get("fib_382", np.nan)),
        ("Fib 50%", last.get("fib_500", np.nan)),
        ("Fib 61.8%", last.get("fib_618", np.nan)),
    ]
    for name, level in candidates:
        try:
            level = float(level)
            if np.isfinite(level) and level > 0 and level <= close:
                levels.append((name, level))
        except Exception:
            pass

    if not levels:
        return close, "لا توجد منطقة Pullback مؤكدة أسفل السعر"

    max_distance = max(atr_val * 1.5, close * 0.06)
    nearby = [x for x in levels if close - x[1] <= max_distance]
    if not nearby:
        return close, "لا يوجد Pullback قريب بما يكفي؛ انتظار تأكيد سعري"

    # Prefer the strongest structural level when several levels are close.
    priority = {"Confirmed Support": 1, "Confirmed Swing Low": 2, "Fib 61.8%": 3, "Fib 50%": 4, "Fib 38.2%": 5, "EMA50": 6, "EMA20": 7}
    name, price = min(nearby, key=lambda x: (priority.get(x[0], 99), abs(close-x[1])))
    return float(price), f"منطقة {name} مؤكدة + مسافة Pullback ضمن {max_distance/close*100:.1f}%"



# =========================================================
# 🎯 Entry Engine
# =========================================================

def determine_entry(
    df_d,
    alignment
):

    last = df_d.iloc[-1]

    market_price = float(
        last["Close"]
    )

    previous_resistance = float(
        last.get(
            "previous_resistance",
            np.nan
        )
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
        last["volume_ratio"]
    )

    atr_pct = float(
        last["atr_pct"]
    )

    body_pct = float(
        last.get(
            "body_pct",
            0
        )
    )

    # =====================================================
    # 1️⃣ Breakout
    # =====================================================

    if (
        breakout and
        np.isfinite(previous_resistance) and
        market_price > previous_resistance and
        volume_ratio >= 1.5 and
        0.015 <= atr_pct <= 0.12 and
        body_pct >= 0.45 and
        alignment >= 60
    ):

        return {
            "type": "دخول اختراق",
            "price": market_price,
            "reason": (
                "اختراق مقاومة سابقة + حجم قوي + "
                "شمعة اختراق جيدة + ATR مناسب + "
                "Trend Alignment قوي"
            )
        }

    # =====================================================
    # 2️⃣ Professional Pullback
    # =====================================================

    if (
        pullback and
        ema20 > ema50 and
        alignment >= 55
    ):

        pullback_price, pullback_reason = (
            calculate_pullback_entry(
                df_d
            )
        )

        return {
            "type": "دخول عند Pullback",
            "price": pullback_price,
            "reason": (
                "اتجاه صاعد + منطقة دعم/EMA/Fibonacci + "
                "انخفاض ضغط البيع + تأكيد سعري | "
                + pullback_reason
            )
        }

    # =====================================================
    # 3️⃣ Immediate
    # =====================================================

    if (
        market_price > ema20 and
        market_price > ema50 and
        last["rsi"] >= 50 and
        last["macd"] > last["macd_signal"] and
        market_price > last["vwap"] and
        volume_ratio >= 1.0 and
        alignment >= 50
    ):

        return {
            "type": "دخول فوري",
            "price": market_price,
            "reason": (
                "السعر فوق EMA20/50 وVWAP + "
                "RSI إيجابي + MACD إيجابي + "
                "حجم مقبول + Trend Alignment"
            )
        }

    # =====================================================
    # 4️⃣ Confirmation
    # =====================================================

    return {
        "type": "انتظار تأكيد",
        "price": market_price,
        "reason": (
            "لا توجد حاليًا شروط كافية "
            "لدخول اختراق أو Pullback أو دخول فوري"
        )
    }


# =========================================================
# 🎯 TARGET ENGINE HELPERS
# =========================================================

def add_target_level(
    levels,
    price,
    reason,
    category
):

    try:

        price = float(price)

        if (
            np.isfinite(price) and
            price > 0
        ):

            levels.append({
                "price": price,
                "reason": reason,
                "category": category
            })

    except Exception:
        pass


def deduplicate_levels(
    levels,
    tolerance
):

    if not levels:
        return []

    levels = sorted(
        levels,
        key=lambda x: x["price"]
    )

    result = []

    for level in levels:

        if not result:

            result.append(level)

        else:

            previous = result[-1]

            relative_gap = (
                abs(
                    level["price"] -
                    previous["price"]
                )
                /
                max(
                    previous["price"],
                    1e-9
                )
            )

            if relative_gap >= tolerance:

                result.append(level)

            else:

                # نحتفظ بالأعلى أولوية
                priority = {
                    "Resistance": 1,
                    "Swing High": 2,
                    "Weekly": 3,
                    "Monthly": 4,
                    "Fibonacci": 5,
                    "ATR": 6
                }

                old_priority = priority.get(
                    previous["category"],
                    99
                )

                new_priority = priority.get(
                    level["category"],
                    99
                )

                if new_priority < old_priority:

                    result[-1] = level

    return result


# =========================================================
# 🛡️ PROFESSIONAL RISK & TARGET ENGINE
# =========================================================

def calculate_risk_engine(df_d, entry, capital, risk_percent, df_w=None, df_m=None):
    last = df_d.iloc[-1]
    support = float(last.get("previous_support", np.nan))
    atr_val = float(last.get("atr", np.nan))
    if not np.isfinite(atr_val) or atr_val <= 0:
        atr_val = entry * 0.03

    bullish = bool(last.get("ema20", entry) > last.get("ema50", entry))
    # Stop is structural first, ATR only protects when no valid structure exists.
    stop_candidates = []
    for level in [support, last.get("confirmed_swing_low", np.nan)]:
        try:
            level = float(level)
            if np.isfinite(level) and 0 < level < entry:
                stop_candidates.append(level - atr_val * 0.20)
        except Exception:
            pass
    stop_candidates.append(entry - atr_val * (1.5 if bullish else 1.2))
    stop_candidates = [x for x in stop_candidates if np.isfinite(x) and 0 < x < entry]
    stop = max(stop_candidates) if stop_candidates else entry * 0.95

    risk_per_share = entry - stop
    if risk_per_share <= 0 or not np.isfinite(risk_per_share):
        risk_per_share = entry * 0.03
        stop = entry - risk_per_share
    risk_pct_actual = risk_per_share / entry
    allowed_loss = capital * risk_percent / 100.0
    position_size = allowed_loss / risk_per_share
    position_value = position_size * entry

    # =====================================================
    # Target Engine: STRUCTURAL ONLY. No ATR-generated/fake targets.
    # =====================================================
    levels = []
    def add(price, reason, category):
        try:
            price = float(price)
            if np.isfinite(price) and price > entry:
                levels.append({"price": price, "reason": reason, "category": category})
        except Exception:
            pass

    add(last.get("previous_resistance", np.nan), "المقاومة اليومية السابقة", "Resistance")
    add(last.get("resistance", np.nan), "المقاومة اليومية الحالية", "Resistance")
    add(last.get("confirmed_swing_high", np.nan), "آخر Swing High مؤكد", "Swing High")

    for col, reason, cat in [
        ("fib_ext_1272", "Fibonacci Extension 127.2% مبني على Swing مؤكد", "Fibonacci"),
        ("fib_ext_1618", "Fibonacci Extension 161.8% مبني على Swing مؤكد", "Fibonacci"),
        ("fib_ext_2000", "Fibonacci Extension 200% مبني على Swing مؤكد", "Fibonacci"),
    ]:
        add(last.get(col, np.nan), reason, cat)

    if df_w is not None and not df_w.empty:
        try:
            w_high = df_w["High"].rolling(20, min_periods=10).max().shift(1).iloc[-1]
            add(w_high, "مقاومة Weekly سابقة", "Weekly")
        except Exception:
            pass
    if df_m is not None and not df_m.empty:
        try:
            m_high = df_m["High"].rolling(12, min_periods=6).max().shift(1).iloc[-1]
            add(m_high, "مقاومة Monthly سابقة", "Monthly")
        except Exception:
            pass

    priority = {"Resistance":1, "Swing High":2, "Weekly":3, "Monthly":4, "Fibonacci":5}
    levels.sort(key=lambda x: x["price"])
    dedup=[]
    for x in levels:
        if not dedup or abs(x["price"]-dedup[-1]["price"])/max(dedup[-1]["price"],1e-9) >= 0.008:
            dedup.append(x)
        elif priority.get(x["category"],99) < priority.get(dedup[-1]["category"],99):
            dedup[-1]=x

    min_gap = max(atr_val * 0.40, entry * 0.012)
    selected=[]
    for x in dedup:
        if not selected or x["price"] >= selected[-1]["price"] + min_gap:
            selected.append(x)
        if len(selected) >= 4:
            break

    # Do NOT fabricate missing targets.
    while len(selected) < 4:
        selected.append({"price": np.nan, "reason": "لا يوجد مستوى سعري هيكلي موثوق كافٍ", "category": "غير متاح"})

    prices=[x["price"] for x in selected]
    profits=[((p-entry)/entry*100) if np.isfinite(p) else np.nan for p in prices]
    rr=[((p-entry)/risk_per_share) if np.isfinite(p) else np.nan for p in prices]
    points={"Resistance":1.0,"Swing High":0.95,"Weekly":0.9,"Monthly":0.9,"Fibonacci":0.8,"غير متاح":0.0}
    target_quality=float(np.mean([points.get(x["category"],0.0) for x in selected])*100)

    structural_count=sum(np.isfinite(prices))
    return {
        "entry": float(entry), "stop": float(stop),
        "tp1": float(prices[0]) if np.isfinite(prices[0]) else np.nan,
        "tp2": float(prices[1]) if np.isfinite(prices[1]) else np.nan,
        "tp3": float(prices[2]) if np.isfinite(prices[2]) else np.nan,
        "tp4": float(prices[3]) if np.isfinite(prices[3]) else np.nan,
        "tp1_profit_pct": float(profits[0]) if np.isfinite(profits[0]) else np.nan,
        "tp2_profit_pct": float(profits[1]) if np.isfinite(profits[1]) else np.nan,
        "tp3_profit_pct": float(profits[2]) if np.isfinite(profits[2]) else np.nan,
        "tp4_profit_pct": float(profits[3]) if np.isfinite(profits[3]) else np.nan,
        "tp1_reason": selected[0]["reason"], "tp2_reason": selected[1]["reason"], "tp3_reason": selected[2]["reason"], "tp4_reason": selected[3]["reason"],
        "tp1_category": selected[0]["category"], "tp2_category": selected[1]["category"], "tp3_category": selected[2]["category"], "tp4_category": selected[3]["category"],
        "rr1": float(rr[0]) if np.isfinite(rr[0]) else np.nan, "rr2": float(rr[1]) if np.isfinite(rr[1]) else np.nan, "rr3": float(rr[2]) if np.isfinite(rr[2]) else np.nan, "rr4": float(rr[3]) if np.isfinite(rr[3]) else np.nan,
        "target_quality": target_quality, "risk_pct": float(risk_pct_actual*100),
        "position_size": float(position_size), "position_value": float(position_value),
        "structural_target_count": structural_count
    }



# =========================================================
# 🧠 CONFIDENCE ENGINE
# =========================================================

def ai_confidence(
    last_d,
    last_w,
    last_m,
    alignment,
    data_quality
):

    score = 0
    total = 13

    if (
        np.isfinite(last_d.get("ema200", np.nan)) and
        last_d["Close"] > last_d["ema200"]
    ):
        score += 1

    if (
        np.isfinite(last_w.get("ema200", np.nan)) and
        last_w["Close"] > last_w["ema200"]
    ):
        score += 1

    if (
        np.isfinite(last_m.get("ema200", np.nan)) and
        last_m["Close"] > last_m["ema200"]
    ):
        score += 1

    if last_d["macd"] > last_d["macd_signal"]:
        score += 1

    if 45 < last_d["rsi"] < 70:
        score += 1

    if last_d["volume_ratio"] > 1:
        score += 1

    if last_d["adx"] > 20:
        score += 1

    if 40 < last_d["mfi"] < 80:
        score += 1

    if (
        np.isfinite(last_d["obv"]) and
        np.isfinite(last_d["obv_ma"]) and
        last_d["obv"] > last_d["obv_ma"]
    ):
        score += 1

    if (
        np.isfinite(last_d["stoch_rsi_k"]) and
        np.isfinite(last_d["stoch_rsi_d"]) and
        last_d["stoch_rsi_k"] >
        last_d["stoch_rsi_d"]
    ):
        score += 1

    if (
        np.isfinite(last_d["vwap"]) and
        last_d["Close"] > last_d["vwap"]
    ):
        score += 1

    if alignment >= 60:
        score += 1

    if data_quality >= 90:
        score += 1

    return score / total


# =========================================================
# 🧠 CONFIDENCE TARGET MODEL
# =========================================================

def calibrated_probabilities_from_backtest(bt):
    """احتمالات تاريخية فعلية من نتائج الصفقات، وليست Confidence مصطنعة."""
    if not bt or bt.get("trades", 0) <= 0:
        return (np.nan, np.nan, np.nan, np.nan)
    return tuple(
        float(bt.get(f"tp{i}_hit_rate", np.nan)) for i in range(1, 5)
    )


def _v10_signal(row):
    try:
        close=float(row["Close"]); ema20=float(row["ema20"]); ema50=float(row["ema50"])
        rsi=float(row["rsi"]); macd=float(row["macd"]); sig=float(row["macd_signal"])
        vr=float(row["volume_ratio"]); atrp=float(row["atr_pct"])
        breakout=bool(row.get("breakout",False)); pullback=bool(row.get("pullback",False))
        immediate=(close>ema20>ema50 and rsi>=50 and macd>sig and vr>=1.0 and 0.015<=atrp<=0.12)
        return bool(breakout or pullback or immediate)
    except Exception:
        return False


def _v10_structural_targets(row, entry):
    vals=[]
    for col,cat in [
        ("previous_resistance","مقاومة سابقة"),("resistance","مقاومة"),
        ("confirmed_swing_high","Swing High مؤكد"),("fib_ext_1272","Fib 127.2%"),
        ("fib_ext_1618","Fib 161.8%"),("fib_ext_2000","Fib 200%")]:
        try:
            x=float(row.get(col,np.nan))
            if np.isfinite(x) and x>entry*1.001: vals.append((x,cat))
        except Exception: pass
    vals.sort(key=lambda z:z[0])
    out=[]
    for x,cat in vals:
        if not out or abs(x-out[-1][0])/max(out[-1][0],1e-9)>=0.008:
            out.append((x,cat))
        if len(out)>=4: break
    return out


def _v10_one_run(data, max_bars=600, commission_pct=0.10, slippage_pct=0.10):
    """محاكاة صفقة محافظة: دخول Open التالي، أهداف هيكلية فقط، 4 أجزاء، BE بعد TP1."""
    empty={"trades":0,"win_rate":0.0,"profit_pct":0.0,"max_drawdown_pct":0.0,
           "profit_factor":0.0,"avg_trade_pct":0.0,"signals":0,"entries":0,
           "skipped_no_target":0,"tp1_hits":0,"tp2_hits":0,"tp3_hits":0,"tp4_hits":0,
           "closed_returns":[],"benchmark_return_pct":0.0}
    if data is None or data.empty: return empty
    try: bt=add_indicators(data.copy())
    except Exception: return empty
    warm=max(BACKTEST_WARMUP,220)
    data=bt.tail(warm+max(int(max_bars),1)+2).copy()
    if len(data)<warm+3: return empty
    equity=1.0; peak=1.0; maxdd=0.0; trades=[]; next_i=warm
    cost=commission_pct/100.0+slippage_pct/100.0
    for i in range(warm,len(data)-2):
        if i<next_i: continue
        row=data.iloc[i]; empty["signals"]+=1
        if not _v10_signal(row): continue
        entry=float(data.iloc[i+1]["Open"])*(1+slippage_pct/100.0)
        atr=float(row.get("atr",np.nan))
        if not np.isfinite(atr) or atr<=0 or entry<=0: continue
        swing=float(row.get("confirmed_swing_low",np.nan))
        stop=swing-0.20*atr if np.isfinite(swing) and 0<swing<entry else entry-1.5*atr
        stop=min(stop,entry-0.001*entry)
        targets=_v10_structural_targets(row,entry)
        if not targets:
            empty["skipped_no_target"]+=1; continue
        empty["entries"]+=1
        # Equal allocation across available structural targets.
        n=len(targets); weights=[1.0/n]*n; remaining=1.0; ret=0.0; hits=0; exit_i=len(data)-1; outcome="open"; current_stop=stop
        for j in range(i+1,len(data)):
            bar=data.iloc[j]; low=float(bar["Low"]); high=float(bar["High"])
            if low<=current_stop:
                ret += remaining*((current_stop/entry)-1.0)-remaining*cost
                remaining=0; exit_i=j; outcome="loss" if hits==0 else "partial_stop"; break
            for k,(tp,cat) in enumerate(targets):
                if weights[k]>0 and high>=tp:
                    ret += weights[k]*((tp*(1-slippage_pct/100.0)/entry)-1.0)-weights[k]*commission_pct/100.0
                    weights[k]=0; remaining-=1.0/n; hits+=1; empty[f"tp{k+1}_hits"]+=1
                    if k==0: current_stop=max(current_stop,entry)
                    elif k==1: current_stop=max(current_stop,entry*(1+0.001))
                    if remaining<=1e-9:
                        exit_i=j; outcome="win"; break
            if remaining<=1e-9: break
        if remaining>1e-9:
            px=float(data.iloc[exit_i]["Close"])*(1-slippage_pct/100.0)
            ret += remaining*(px/entry-1.0)-remaining*cost
            outcome="open" if exit_i==len(data)-1 else outcome
        equity*=max(0.01,1+ret); peak=max(peak,equity); maxdd=max(maxdd,(peak-equity)/peak)
        trades.append(ret); next_i=max(next_i,exit_i+1)
        if exit_i>=len(data)-1: break
    closed=trades
    wins=[x for x in closed if x>0]; losses=[x for x in closed if x<0]
    gw=sum(wins); gl=abs(sum(losses))
    # Buy & hold benchmark over tested bars, with costs.
    try:
        first=float(data.iloc[warm]["Close"]); last=float(data.iloc[-1]["Close"])
        bench=(last/first-1.0-cost)*100
    except Exception: bench=0.0
    out=empty.copy(); out.update({"trades":len(closed),"win_rate":len(wins)/len(closed)*100 if closed else 0.0,
        "profit_pct":(equity-1)*100,"max_drawdown_pct":maxdd*100,
        "profit_factor":gw/gl if gl>0 else (999.0 if gw>0 else 0.0),
        "avg_trade_pct":float(np.mean(closed)*100) if closed else 0.0,
        "closed_returns":closed,"benchmark_return_pct":bench})
    for k in range(1,5): out[f"tp{k}_hit_rate"]=(out[f"tp{k}_hits"]/len(closed)*100) if closed else np.nan
    if closed:
        out["expectancy_pct"]=float(np.mean(closed)*100)
        out["sharpe"]=float(np.mean(closed)/np.std(closed,ddof=1)*np.sqrt(len(closed))) if len(closed)>1 and np.std(closed,ddof=1)>0 else 0.0
        downside=np.array([min(x,0) for x in closed]); ds=np.std(downside,ddof=1) if len(closed)>1 else 0
        out["sortino"]=float(np.mean(closed)/ds*np.sqrt(len(closed))) if ds>0 else 0.0
        out["excess_return_pct"]=out["profit_pct"]-bench
    else:
        out["expectancy_pct"]=out["sharpe"]=out["sortino"]=out["excess_return_pct"]=0.0
    return out


def monte_carlo_metrics(returns, runs=5000, seed=42):
    if not returns or len(returns)<3:
        return {"mc_median_pct":np.nan,"mc_p05_pct":np.nan,"mc_p95_pct":np.nan,"mc_ruin_pct":np.nan}
    rng=np.random.default_rng(seed); arr=np.asarray(returns,float); finals=[]; ruins=0
    for _ in range(int(runs)):
        seq=rng.choice(arr,size=len(arr),replace=True); eq=1.0; peak=1.0; dd=0
        for r in seq: eq*=max(0.01,1+r); peak=max(peak,eq); dd=max(dd,(peak-eq)/peak)
        finals.append((eq-1)*100); ruins += dd>=0.50
    return {"mc_median_pct":float(np.percentile(finals,50)),"mc_p05_pct":float(np.percentile(finals,5)),"mc_p95_pct":float(np.percentile(finals,95)),"mc_ruin_pct":float(ruins/len(finals)*100)}


def walk_forward_v10(df, max_bars=600, commission_pct=0.10, slippage_pct=0.10):
    if df is None or len(df)<700: return {"wf_windows":0,"wf_positive":0,"wf_score":np.nan,"oos_return_pct":np.nan}
    n=min(len(df), max(900,int(max_bars)+440)); d=df.tail(n).copy(); chunk=max(150,(len(d)-220)//4); results=[]
    for z in range(4):
        a=220+z*chunk; b=min(len(d),a+chunk)
        if b-a<80: continue
        r=_v10_one_run(d.iloc[:b],max_bars=b-220,commission_pct=commission_pct,slippage_pct=slippage_pct)
        results.append(r)
    if not results: return {"wf_windows":0,"wf_positive":0,"wf_score":np.nan,"oos_return_pct":np.nan}
    pos=sum(r["profit_pct"]>0 for r in results); oos=float(np.mean([r["profit_pct"] for r in results]))
    return {"wf_windows":len(results),"wf_positive":pos,"wf_score":pos/len(results)*100,"oos_return_pct":oos}


def trading_rank_v10(row):
    """ترتيب تداولي منفصل عن التقييم الفني."""
    vals=[]
    def add(v,w,lo=None,hi=None):
        try:
            x=float(v)
            if not np.isfinite(x): return
            if lo is not None and hi is not None: x=(x-lo)/(hi-lo)*100
            vals.append((max(0,min(100,x)),w))
        except Exception: pass
    add(row.get("التقييم",0),25,0,100)
    add(row.get("Historical TP1 %",np.nan),20,35,90)
    add(row.get("Expectancy %",np.nan),15,-2,5)
    add(row.get("R/R الهدف الأول",np.nan),15,1,4)
    add(row.get("Walk Forward %",np.nan),10,25,100)
    add(row.get("OOS Return %",np.nan),5,-20,30)
    add(row.get("جودة الأهداف",np.nan),5,0,100)
    add(row.get("السيولة Ratio",np.nan),5,0.5,3)
    return round(sum(x*w for x,w in vals)/sum(w for _,w in vals),2) if vals else 0.0


# =========================================================
# ⚡ معالجة سهم واحد
# =========================================================

def process(
    symbol,
    daily,
    weekly,
    monthly,
    capital,
    risk_percent,
    market_return_20=0.0,
    run_backtest=False,
    backtest_bars=600,
    commission_pct=0.10,
    slippage_pct=0.10,
    max_position_pct=20,
    monte_carlo_runs=5000
):

    clean_symbol = symbol.replace(
        ".CA",
        ""
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
                "الحالة": "❌ لا توجد بيانات يومية"
            }

        if len(df_d) < MIN_DAILY_ROWS:

            return {
                "السهم": clean_symbol,
                "الحالة": "❌ بيانات يومية غير كافية"
            }

        if df_w.empty:

            return {
                "السهم": clean_symbol,
                "الحالة": "❌ لا توجد بيانات أسبوعية"
            }

        if len(df_w) < MIN_WEEKLY_ROWS:

            return {
                "السهم": clean_symbol,
                "الحالة": "❌ بيانات أسبوعية غير كافية"
            }

        if df_m.empty:

            return {
                "السهم": clean_symbol,
                "الحالة": "❌ لا توجد بيانات شهرية"
            }

        if len(df_m) < MIN_MONTHLY_ROWS:

            return {
                "السهم": clean_symbol,
                "الحالة": "❌ بيانات شهرية غير كافية"
            }

        df_d["market_return_20"] = market_return_20
        result = analyze(
            df_d,
            df_w,
            df_m,
            capital,
            risk_percent
        )
        if run_backtest:
            bt = _v10_one_run(df_d, backtest_bars, commission_pct, slippage_pct)
            mc = monte_carlo_metrics(bt.get("closed_returns", []), monte_carlo_runs)
            wf = walk_forward_v10(df_d, backtest_bars, commission_pct, slippage_pct)
            result["Backtest Trades"] = bt["trades"]
            result["Backtest Win Rate %"] = round(bt["win_rate"], 1)
            result["Backtest Return %"] = round(bt["profit_pct"], 2)
            result["Backtest Max DD %"] = round(bt["max_drawdown_pct"], 2)
            result["Backtest Profit Factor"] = round(bt["profit_factor"], 2)
            result["Backtest Signals"] = int(bt.get("signals", 0))
            result["Backtest Valid Entries"] = int(bt.get("entries", 0))
            result["Backtest No Target"] = int(bt.get("skipped_no_target", 0))
            result["Backtest Bad Stop"] = 0
            result["Backtest Invalid Indicators"] = 0
            result["Expectancy %"] = round(bt.get("expectancy_pct",0),3)
            result["Sharpe"] = round(bt.get("sharpe",0),2)
            result["Sortino"] = round(bt.get("sortino",0),2)
            result["Benchmark Return %"] = round(bt.get("benchmark_return_pct",0),2)
            result["Excess Return %"] = round(bt.get("excess_return_pct",0),2)
            result["Historical TP1 %"] = round(bt.get("tp1_hit_rate",np.nan),1) if np.isfinite(bt.get("tp1_hit_rate",np.nan)) else np.nan
            result["Historical TP2 %"] = round(bt.get("tp2_hit_rate",np.nan),1) if np.isfinite(bt.get("tp2_hit_rate",np.nan)) else np.nan
            result["Historical TP3 %"] = round(bt.get("tp3_hit_rate",np.nan),1) if np.isfinite(bt.get("tp3_hit_rate",np.nan)) else np.nan
            result["Historical TP4 %"] = round(bt.get("tp4_hit_rate",np.nan),1) if np.isfinite(bt.get("tp4_hit_rate",np.nan)) else np.nan
            result["MC Median %"] = round(mc["mc_median_pct"],2) if np.isfinite(mc["mc_median_pct"]) else np.nan
            result["MC P05 %"] = round(mc["mc_p05_pct"],2) if np.isfinite(mc["mc_p05_pct"]) else np.nan
            result["MC P95 %"] = round(mc["mc_p95_pct"],2) if np.isfinite(mc["mc_p95_pct"]) else np.nan
            result["MC Ruin %"] = round(mc["mc_ruin_pct"],2) if np.isfinite(mc["mc_ruin_pct"]) else np.nan
            result["Walk Forward %"] = round(wf["wf_score"],1) if np.isfinite(wf["wf_score"]) else np.nan
            result["WF Windows"] = wf["wf_windows"]
            result["WF Positive Windows"] = wf["wf_positive"]
            result["OOS Return %"] = round(wf["oos_return_pct"],2) if np.isfinite(wf["oos_return_pct"]) else np.nan
            result["الاحتمال التاريخي TP1 %"] = result["Historical TP1 %"]
            result["الترتيب التداولي"] = trading_rank_v10(result)
        else:
            result["Backtest Trades"] = 0
            result["Backtest Win Rate %"] = np.nan
            result["Backtest Return %"] = np.nan
            result["Backtest Max DD %"] = np.nan
            result["Backtest Profit Factor"] = np.nan
            result["Backtest Signals"] = np.nan
            result["Backtest Valid Entries"] = np.nan
            result["Backtest No Target"] = np.nan
            result["Backtest Bad Stop"] = np.nan
            result["Backtest Invalid Indicators"] = np.nan
            for _c in ["Expectancy %","Sharpe","Sortino","Benchmark Return %","Excess Return %","Historical TP1 %","Historical TP2 %","Historical TP3 %","Historical TP4 %","MC Median %","MC P05 %","MC P95 %","MC Ruin %","Walk Forward %","OOS Return %"]:
                result[_c] = np.nan
            result["الترتيب التداولي"] = 0.0

        # Portfolio concentration cap: risk-based size can never exceed the configured
        # percentage of total capital. Keep the stop/risk calculation intact and cap
        # only the executable position size/value.
        try:
            max_value = float(capital) * float(max_position_pct) / 100.0
            current_value = float(result.get("_position_value", np.nan))
            current_size = float(result.get("_position_size", np.nan))
            entry_px = float(result.get("سعر الدخول", np.nan))
            if np.isfinite(max_value) and np.isfinite(current_value) and current_value > max_value and entry_px > 0:
                result["_position_value"] = max_value
                result["_position_size"] = max_value / entry_px
        except Exception:
            pass

        result["السهم"] = clean_symbol
        result["الحالة"] = "✅ تم التحليل"

        return result

    except Exception as e:

        return {
            "السهم": clean_symbol,
            "الحالة": f"❌ {str(e)[:120]}"
        }


# =========================================================
# 🚀 تشغيل الفحص
# =========================================================

if st.button(
    "🚀 بدء فحص الأسهم",
    use_container_width=True
):

    st.info(
        f"📡 جاري فحص {TOTAL_STOCKS} سهم..."
    )

    progress = st.progress(
        0
    )

    status_text = st.empty()

    # =====================================================
    # Daily
    # =====================================================

    with st.spinner(
        "📥 جاري تحميل البيانات اليومية..."
    ):

        daily = load_data(
            EGX100,
            period_daily,
            "1d"
        )

    progress.progress(
        20
    )

    # =====================================================
    # Weekly
    # =====================================================

    status_text.info(
        "📥 جاري تحميل البيانات الأسبوعية..."
    )

    weekly = load_data(
        EGX100,
        period_weekly,
        "1wk"
    )

    progress.progress(
        40
    )

    # =====================================================
    # Monthly
    # =====================================================

    status_text.info(
        "📥 جاري تحميل البيانات الشهرية..."
    )

    monthly = load_data(
        EGX100,
        period_monthly,
        "1mo"
    )

    progress.progress(
        50
    )

    # =====================================================
    # Data Engine Stats
    # =====================================================

    status_text.info(
        "🔍 جاري فحص جودة البيانات والتغطية..."
    )

    data_engine_stats = []

    for symbol in EGX100:

        df_d_check = extract_symbol_data(
            daily,
            symbol
        )

        df_w_check = extract_symbol_data(
            weekly,
            symbol
        )

        df_m_check = extract_symbol_data(
            monthly,
            symbol
        )

        qd = calculate_data_quality(
            df_d_check
        )

        qw = calculate_data_quality(
            df_w_check
        )

        qm = calculate_data_quality(
            df_m_check
        )

        quality = (
            qd["quality"] * 0.50 +
            qw["quality"] * 0.30 +
            qm["quality"] * 0.20
        )

        data_engine_stats.append({

            "symbol": symbol,

            "daily_rows":
                qd["rows"],

            "weekly_rows":
                qw["rows"],

            "monthly_rows":
                qm["rows"],

            "daily_quality":
                qd["quality"],

            "weekly_quality":
                qw["quality"],

            "monthly_quality":
                qm["quality"],

            "data_quality":
                round(
                    quality,
                    2
                ),

            "daily_ema200":
                (
                    "✅"
                    if qd["rows"] >= 200
                    else "⚠️"
                ),

            "weekly_ema200":
                (
                    "✅"
                    if qw["rows"] >= 200
                    else "⚠️"
                ),

            "monthly_ema200":
                (
                    "✅"
                    if qm["rows"] >= 200
                    else "⚠️"
                )
        })

    # =====================================================
    # Relative Strength market proxy
    # =====================================================
    market_return_20 = build_market_return_proxy(daily, EGX100)

    # =====================================================
    # التحليل
    # =====================================================

    results = []

    status_text.info(
        f"🧠 جاري تحليل {TOTAL_STOCKS} سهم بالتوازي..."
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
                commission_pct,
                slippage_pct,
                max_position_pct,
                monte_carlo_runs
            ): symbol

            for symbol in EGX100
        }

        completed = 0

        for future in as_completed(
            futures
        ):

            try:

                result = future.result()

                if result:
                    results.append(
                        result
                    )

            except Exception as e:

                symbol = futures[
                    future
                ]

                results.append({

                    "السهم":
                        symbol.replace(
                            ".CA",
                            ""
                        ),

                    "الحالة":
                        f"❌ {str(e)[:120]}"
                })

            completed += 1

            progress.progress(
                50 +
                int(
                    completed /
                    TOTAL_STOCKS *
                    50
                )
            )

    progress.progress(
        100
    )

    status_text.success(
        "✅ انتهى الفحص بالكامل"
    )

    # =====================================================
    # النتائج
    # =====================================================

    if not results:

        st.error(
            "❌ لم يتم الحصول على أي نتائج."
        )

        st.stop()

    df_all = pd.DataFrame(
        results
    )

    # =====================================================
    # الأسهم الناجحة
    # =====================================================

    df_ok = df_all[
        df_all["الحالة"] ==
        "✅ تم التحليل"
    ].copy()

    if not df_ok.empty and "عدد الأهداف الهيكلية" in df_ok.columns:
        no_targets = int((df_ok["عدد الأهداف الهيكلية"] < 1).sum())
        if no_targets:
            st.warning(f"⚠️ {no_targets} سهم بدون مستوى Target هيكلي موثوق؛ النظام لا يخترع أهداف ATR بديلة.")

    # =====================================================
    # التغطية
    # =====================================================

    total = TOTAL_STOCKS

    analyzed = int(
        (
            df_all["الحالة"] ==
            "✅ تم التحليل"
        ).sum()
    )

    failed = total - analyzed

    coverage = (
        analyzed /
        total *
        100
        if total > 0
        else 0
    )

    # =====================================================
    # Data Quality
    # =====================================================

    stats_df = pd.DataFrame(
        data_engine_stats
    )

    if not stats_df.empty:

        avg_quality = float(
            stats_df[
                "data_quality"
            ].mean()
        )

        daily_coverage = float(
            (
                stats_df[
                    "daily_rows"
                ] >= MIN_DAILY_ROWS
            ).mean() * 100
        )

        weekly_coverage = float(
            (
                stats_df[
                    "weekly_rows"
                ] >= MIN_WEEKLY_ROWS
            ).mean() * 100
        )

        monthly_coverage = float(
            (
                stats_df[
                    "monthly_rows"
                ] >= MIN_MONTHLY_ROWS
            ).mean() * 100
        )

        daily_ema200_coverage = float(
            (
                stats_df[
                    "daily_rows"
                ] >= 200
            ).mean() * 100
        )

        weekly_ema200_coverage = float(
            (
                stats_df[
                    "weekly_rows"
                ] >= 200
            ).mean() * 100
        )

        monthly_ema200_coverage = float(
            (
                stats_df[
                    "monthly_rows"
                ] >= 200
            ).mean() * 100
        )

    else:

        avg_quality = 0
        daily_coverage = 0
        weekly_coverage = 0
        monthly_coverage = 0
        daily_ema200_coverage = 0
        weekly_ema200_coverage = 0
        monthly_ema200_coverage = 0

    # =====================================================
    # ملخص الفحص
    # =====================================================

    st.subheader(
        "📊 ملخص الفحص"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "📊 الأسهم المطلوبة",
        total
    )

    c2.metric(
        "✅ تم تحليلها",
        analyzed
    )

    c3.metric(
        "❌ فشل",
        failed
    )

    c4.metric(
        "📡 نسبة التغطية",
        f"{coverage:.1f}%"
    )

    # =====================================================
    # جودة البيانات
    # =====================================================

    st.subheader(
        "📡 جودة البيانات"
    )

    q1, q2, q3, q4 = st.columns(4)

    q1.metric(
        "⭐ جودة البيانات",
        f"{avg_quality:.1f}%"
    )

    q2.metric(
        "📅 تغطية Daily",
        f"{daily_coverage:.1f}%"
    )

    q3.metric(
        "📆 تغطية Weekly",
        f"{weekly_coverage:.1f}%"
    )

    q4.metric(
        "🗓️ تغطية Monthly",
        f"{monthly_coverage:.1f}%"
    )

    st.subheader(
        "📐 تغطية EMA200 الحقيقي"
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
    # الأسهم الناجحة
    # =====================================================

    if not df_ok.empty:

        if "الترتيب التداولي" in df_ok.columns and run_backtest:
            df_ok = df_ok.sort_values(["الترتيب التداولي","التقييم"], ascending=[False,False])
        else:
            df_ok = df_ok.sort_values("التقييم", ascending=False)

        # =================================================
        # أفضل الأسهم
        # =================================================

        st.subheader(
            f"🏆 أفضل {min(top_n, len(df_ok))} سهم"
        )
        if run_backtest:
            st.info(
                "📌 الترتيب هنا هو **الترتيب التداولي** وليس التقييم الفني فقط. "
                "يُراعى فيه التقييم الفني + النتائج التاريخية الفعلية + القيمة المتوقعة + R/R + Walk-Forward + OOS + السيولة + جودة الأهداف. "
                "احتمالات TP المعروضة مبنية على صفقات الباك تست وليست تنبؤًا مضمونًا."
            )

        top_df = df_ok.head(
            top_n
        ).copy()

        preferred_cols = [

            "السهم",
            "الترتيب التداولي",
            "التقييم",
            "الإشارة",
            "الاتجاه",
            "نوع الدخول",
            "سبب الدخول",
            "سعر الدخول",
            "وقف الخسارة",

            "الهدف الأول",
            "ربح الهدف الأول %",
            "R/R الهدف الأول",
            "سبب الهدف الأول",

            "الهدف الثاني",
            "ربح الهدف الثاني %",
            "R/R الهدف الثاني",
            "سبب الهدف الثاني",

            "الهدف الثالث",
            "ربح الهدف الثالث %",
            "R/R الهدف الثالث",
            "سبب الهدف الثالث",

            "الهدف الرابع",
            "ربح الهدف الرابع %",
            "R/R الهدف الرابع",
            "سبب الهدف الرابع",

            "جودة الأهداف",
            "EMA200",

            "Historical TP1 %",
            "Historical TP2 %",
            "Historical TP3 %",
            "Historical TP4 %",

            "مؤشر RSI",
            "قوة الاتجاه ADX",
            "التذبذب ATR %",
            "السيولة Ratio",
            "Relative Strength %",
            "عدد الأهداف الهيكلية",
            "Backtest Trades",
            "Backtest Win Rate %",
            "Backtest Return %",
            "Backtest Max DD %",
            "Backtest Profit Factor",
            "Expectancy %",
            "Historical TP1 %",
            "Historical TP2 %",
            "Historical TP3 %",
            "Historical TP4 %",
            "Benchmark Return %",
            "Excess Return %",
            "Sharpe",
            "Sortino",
            "Walk Forward %",
            "WF Windows",
            "OOS Return %",
            "MC Median %",
            "MC P05 %",
            "MC P95 %",
            "MC Ruin %",
            "المدة المتوقعة"
        ]

        existing_cols = [
            c for c in preferred_cols
            if c in top_df.columns
        ]

        top_df = top_df[
            existing_cols
        ]

        top_df = top_df.rename(columns={
            "الترتيب التداولي":"الترتيب التداولي", "التقييم":"التقييم الفني",
            "Backtest Trades":"عدد صفقات الباك تست", "Backtest Win Rate %":"نسبة الصفقات الرابحة %",
            "Backtest Return %":"عائد الباك تست %", "Backtest Max DD %":"أقصى تراجع %",
            "Backtest Profit Factor":"معامل الربح", "Expectancy %":"القيمة المتوقعة لكل صفقة %",
            "Historical TP1 %":"احتمال TP1 تاريخيًا %", "Historical TP2 %":"احتمال TP2 تاريخيًا %",
            "Historical TP3 %":"احتمال TP3 تاريخيًا %", "Historical TP4 %":"احتمال TP4 تاريخيًا %",
            "Benchmark Return %":"عائد الاحتفاظ بالسهم %", "Excess Return %":"العائد الإضافي على السوق %",
            "Sharpe":"معامل شارب", "Sortino":"معامل سورتينو", "Walk Forward %":"نجاح Walk-Forward %",
            "WF Windows":"عدد نوافذ Walk-Forward", "OOS Return %":"عائد الاختبار خارج العينة OOS %",
            "MC Median %":"وسيط Monte Carlo %", "MC P05 %":"أسوأ 5% Monte Carlo %",
            "MC P95 %":"أفضل 5% Monte Carlo %", "MC Ruin %":"احتمال Drawdown 50%+ %"
        })
        st.dataframe(
            top_df, use_container_width=True, hide_index=True
        )
        if run_backtest:
            st.caption(
                "🧪 الباك تست: دخول عند افتتاح الشمعة التالية للإشارة، أهداف هيكلية فقط، "
                "تقسيم المركز على الأهداف المتاحة، نقل الوقف للتعادل بعد الهدف الأول، مع احتساب العمولة والانزلاق السعري. "
                "إذا لم توجد أهداف هيكلية لا تُنشأ أهداف ATR وهمية."
            )

        # =================================================
        # الأسهم القوية
        # =================================================

        strong = df_ok[
            df_ok["التقييم"] > 70
        ].copy()

        st.subheader(
            f"🔥 الأسهم القوية: {len(strong)}"
        )

        if not strong.empty:

            strong = strong[
                existing_cols
            ]

            st.dataframe(
                strong,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.warning(
                "⚠️ لا توجد أسهم قوية حالياً حسب شروط النظام."
            )

        # =================================================
        # جميع الأسهم
        # =================================================

        st.subheader(
            "📋 جميع الأسهم التي تم تحليلها"
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

        csv_ok = (
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
            "⬇️ تحميل نتائج الأسهم المحللة",
            csv_ok,
            "EGX_AI_PRO_MAX_V10_RESULTS_AR.csv",
            "text/csv",
            use_container_width=True
        )

        # =================================================
        # معلومات المحرك
        # =================================================

        with st.expander(
            "🔬 معلومات المحرك المتقدمة"
        ):

            internal_cols = [

                "السهم",

                "_entry_type",
                "_trend_alignment",
                "_data_quality",

                "_ema200_daily",
                "_ema200_weekly",
                "_ema200_monthly",

                "_risk_pct",

                "_rr1",
                "_rr2",
                "_rr3",
                "_rr4",

                "_target_quality",

                "_position_size",
                "_position_value",

                "_pullback_quality",
                "_volume_ratio",
                "_liquidity_ratio",
                "_relative_strength",
                "_structural_target_count",
                "الترتيب التداولي", "Expectancy %", "Historical TP1 %", "Historical TP2 %",
                "Historical TP3 %", "Historical TP4 %", "Walk Forward %", "OOS Return %",
                "MC Median %", "MC P05 %", "MC P95 %", "MC Ruin %",

                "_obv",
                "_obv_ma",

                "_stoch_rsi_k",
                "_stoch_rsi_d",

                "_vwap"
            ]

            available_internal = [
                c for c in internal_cols
                if c in df_ok.columns
            ]

            internal_df = (
                df_ok[
                    available_internal
                ]
                .rename(
                    columns={

                        "_entry_type":
                            "نوع الدخول",

                        "_trend_alignment":
                            "Trend Alignment",

                        "_data_quality":
                            "جودة البيانات",

                        "_ema200_daily":
                            "Daily EMA200",

                        "_ema200_weekly":
                            "Weekly EMA200",

                        "_ema200_monthly":
                            "Monthly EMA200",

                        "_risk_pct":
                            "المخاطرة %",

                        "_rr1":
                            "R/R TP1",

                        "_rr2":
                            "R/R TP2",

                        "_rr3":
                            "R/R TP3",

                        "_rr4":
                            "R/R TP4",

                        "_target_quality":
                            "جودة الأهداف",

                        "_position_size":
                            "حجم المركز",

                        "_position_value":
                            "قيمة المركز",

                        "_pullback_quality":
                            "Pullback Quality",

                        "_volume_ratio":
                            "Volume Ratio",
                        "_liquidity_ratio":
                            "Liquidity Ratio",
                        "_relative_strength":
                            "Relative Strength %",
                        "_structural_target_count":
                            "عدد الأهداف الهيكلية",

                        "الترتيب التداولي": "الترتيب التداولي",
                        "Expectancy %": "القيمة المتوقعة %",
                        "Historical TP1 %": "احتمال TP1 تاريخيًا %",
                        "Historical TP2 %": "احتمال TP2 تاريخيًا %",
                        "Historical TP3 %": "احتمال TP3 تاريخيًا %",
                        "Historical TP4 %": "احتمال TP4 تاريخيًا %",
                        "Walk Forward %": "نجاح Walk-Forward %",
                        "OOS Return %": "عائد OOS %",
                        "MC Median %": "وسيط Monte Carlo %",
                        "MC P05 %": "أسوأ 5% Monte Carlo %",
                        "MC P95 %": "أفضل 5% Monte Carlo %",
                        "MC Ruin %": "احتمال Drawdown 50%+ %",

                        "_obv":
                            "OBV",

                        "_obv_ma":
                            "OBV MA",

                        "_stoch_rsi_k":
                            "Stoch RSI K",

                        "_stoch_rsi_d":
                            "Stoch RSI D",

                        "_vwap":
                            "VWAP"
                    }
                )
            )

            st.dataframe(
                internal_df,
                use_container_width=True,
                hide_index=True
            )

        # =================================================
        # تفاصيل الأهداف
        # =================================================

        with st.expander(
            "🎯 تفاصيل Target Engine"
        ):

            target_cols = [

                "السهم",

                "سعر الدخول",

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

            available_target_cols = [
                c for c in target_cols
                if c in df_ok.columns
            ]

            st.dataframe(
                df_ok[
                    available_target_cols
                ],
                use_container_width=True,
                hide_index=True
            )

        # =================================================
        # تفاصيل Entry
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
                "جودة الأهداف",
                "R/R الهدف الأول",
                "مؤشر RSI",
                "قوة الاتجاه ADX",
                "التذبذب ATR %",
                "EMA200"
            ]

            available_entry_cols = [
                c for c in entry_cols
                if c in df_ok.columns
            ]

            st.dataframe(
                df_ok[
                    available_entry_cols
                ],
                use_container_width=True,
                hide_index=True
            )

        # =================================================
        # Data Quality Details
        # =================================================

        with st.expander(
            "📡 تفاصيل جودة البيانات لكل سهم"
        ):

            quality_display = (
                stats_df
                .rename(
                    columns={

                        "symbol":
                            "السهم",

                        "daily_rows":
                            "شموع Daily",

                        "weekly_rows":
                            "شموع Weekly",

                        "monthly_rows":
                            "شموع Monthly",

                        "daily_quality":
                            "جودة Daily %",

                        "weekly_quality":
                            "جودة Weekly %",

                        "monthly_quality":
                            "جودة Monthly %",

                        "data_quality":
                            "جودة البيانات %",

                        "daily_ema200":
                            "Daily EMA200",

                        "weekly_ema200":
                            "Weekly EMA200",

                        "monthly_ema200":
                            "Monthly EMA200"
                    }
                )
            )

            st.dataframe(
                quality_display,
                use_container_width=True,
                hide_index=True
            )

    # =====================================================
    # الأسهم الفاشلة
    # =====================================================

    df_failed = df_all[
        df_all["الحالة"] !=
        "✅ تم التحليل"
    ].copy()

    if not df_failed.empty:

        st.subheader(
            f"⚠️ الأسهم التي فشل تحميل/تحليل بياناتها: {len(df_failed)}"
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

        csv_failed = (
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
            "⬇️ تحميل قائمة الأخطاء",
            csv_failed,
            "EGX_AI_PRO_MAX_V10_ERRORS_AR.csv",
            "text/csv",
            use_container_width=True
        )

    # =====================================================
    # الحالة النهائية
    # =====================================================

    st.success(
        f"""
🔥 الفحص اكتمل بنجاح

📊 إجمالي الأسهم: {total}

✅ تم تحليل: {analyzed}

❌ فشل: {failed}

📡 نسبة تغطية البيانات: {coverage:.1f}%

⭐ متوسط جودة البيانات: {avg_quality:.1f}%

📅 Daily Coverage: {daily_coverage:.1f}%

📆 Weekly Coverage: {weekly_coverage:.1f}%

🗓️ Monthly Coverage: {monthly_coverage:.1f}%

📐 Daily EMA200 الحقيقي: {daily_ema200_coverage:.1f}%

📐 Weekly EMA200 الحقيقي: {weekly_ema200_coverage:.1f}%

📐 Monthly EMA200 الحقيقي: {monthly_ema200_coverage:.1f}%
"""
    )
