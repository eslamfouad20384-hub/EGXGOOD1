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
    page_title="EGX AI PRO MAX v7 - عربي",
    page_icon="📈",
    layout="wide"
)

st.title("🚀 EGX AI PRO MAX v7")
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
    ["3mo", "6mo", "1y", "2y", "3y", "5y"],
    index=1
)

period_weekly = st.sidebar.selectbox(
    "📅 فترة البيانات الأسبوعية",
    ["3y", "5y", "10y", "max"],
    index=1
)

period_monthly = st.sidebar.selectbox(
    "📅 فترة البيانات الشهرية",
    ["10y", "15y", "20y", "max"],
    index=1
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
    ema20 = float(last["ema20"])
    ema50 = float(last["ema50"])

    levels = []

    for name, level in [
        (
            "EMA20",
            ema20
        ),
        (
            "EMA50",
            ema50
        ),
        (
            "Support",
            last.get(
                "previous_support",
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
    ]:

        try:

            level = float(level)

            if (
                np.isfinite(level) and
                level > 0 and
                level <= close * 1.02
            ):

                levels.append(
                    (
                        name,
                        level
                    )
                )

        except Exception:
            continue

    if not levels:

        return close, "لا توجد منطقة Pullback واضحة"

    # نختار أقرب مستوى دعم أسفل السعر
    below = [
        item for item in levels
        if item[1] <= close
    ]

    if below:

        name, price = max(
            below,
            key=lambda x: x[1]
        )

    else:

        name, price = min(
            levels,
            key=lambda x: abs(
                x[1] - close
            )
        )

    # لا نسمح بسعر دخول Pullback بعيد جدًا عن السوق
    max_pullback_distance = max(
        float(last["atr"]) * 1.5,
        close * 0.07
    )

    if (
        close - price >
        max_pullback_distance
    ):

        return (
            close,
            "Pullback بعيد؛ الدخول عند تأكيد السعر الحالي"
        )

    return (
        float(price),
        f"منطقة {name}"
    )


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

def calculate_risk_engine(
    df_d,
    entry,
    capital,
    risk_percent,
    df_w=None,
    df_m=None
):

    last = df_d.iloc[-1]

    support = float(
        last.get(
            "previous_support",
            last["support"]
        )
    )

    resistance = float(
        last["resistance"]
    )

    previous_resistance = float(
        last.get(
            "previous_resistance",
            np.nan
        )
    )

    atr_val = float(
        last["atr"]
    )

    if (
        not np.isfinite(atr_val) or
        atr_val <= 0
    ):

        atr_val = entry * 0.03

    # =====================================================
    # اتجاه السهم
    # =====================================================

    bullish = (
        last["ema20"] >
        last["ema50"]
    )

    strong_trend = (
        last["adx"] >= 25
    )

    very_strong_trend = (
        last["adx"] >= 30
    )

    breakout = bool(
        last.get(
            "breakout",
            False
        )
    )

    volume_ratio = float(
        last.get(
            "volume_ratio",
            1.0
        )
    )

    # =====================================================
    # Stop Loss
    # =====================================================

    atr_stop = (
        entry -
        atr_val * (
            1.5 if bullish else 1.2
        )
    )

    support_stop = (
        support -
        atr_val * 0.25
    )

    candidates = [
        x for x in [
            atr_stop,
            support_stop
        ]
        if (
            np.isfinite(x) and
            x > 0 and
            x < entry
        )
    ]

    if candidates:

        stop = max(
            candidates
        )

    else:

        stop = (
            entry -
            atr_val * 1.5
        )

    if stop <= 0:

        stop = entry * 0.95

    # =====================================================
    # Risk %
    # =====================================================

    risk_per_share = (
        entry -
        stop
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

    risk_pct_actual = (
        risk_per_share /
        entry
    )

    # =====================================================
    # Position Size
    # =====================================================

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

    # =====================================================
    # TARGET LEVELS
    #
    # الأولوية:
    # 1 Resistance
    # 2 Swing High
    # 3 Weekly / Monthly
    # 4 Fibonacci
    # 5 ATR
    # =====================================================

    structural_levels = []

    # -----------------------------------------------------
    # 1. Daily Resistance
    # -----------------------------------------------------

    add_target_level(
        structural_levels,
        previous_resistance,
        "المقاومة اليومية السابقة",
        "Resistance"
    )

    add_target_level(
        structural_levels,
        resistance,
        "المقاومة اليومية الحالية",
        "Resistance"
    )

    # -----------------------------------------------------
    # 2. Swing High
    # -----------------------------------------------------

    add_target_level(
        structural_levels,
        last.get(
            "swing_high_20",
            np.nan
        ),
        "آخر Swing High - 20 شمعة",
        "Swing High"
    )

    add_target_level(
        structural_levels,
        last.get(
            "swing_high_60",
            np.nan
        ),
        "آخر Swing High - 60 شمعة",
        "Swing High"
    )

    # -----------------------------------------------------
    # 3. Weekly Levels
    # -----------------------------------------------------

    weekly_levels = []

    if (
        df_w is not None and
        not df_w.empty
    ):

        try:

            w_previous_high = (
                df_w["High"]
                .rolling(
                    20,
                    min_periods=10
                )
                .max()
                .shift(1)
                .iloc[-1]
            )

            if (
                np.isfinite(w_previous_high) and
                w_previous_high > entry
            ):

                weekly_levels.append(
                    float(w_previous_high)
                )

                add_target_level(
                    structural_levels,
                    w_previous_high,
                    "مقاومة Weekly سابقة",
                    "Weekly"
                )

        except Exception:
            pass

    # -----------------------------------------------------
    # 4. Monthly Levels
    # -----------------------------------------------------

    monthly_levels = []

    if (
        df_m is not None and
        not df_m.empty
    ):

        try:

            m_previous_high = (
                df_m["High"]
                .rolling(
                    12,
                    min_periods=6
                )
                .max()
                .shift(1)
                .iloc[-1]
            )

            if (
                np.isfinite(m_previous_high) and
                m_previous_high > entry
            ):

                monthly_levels.append(
                    float(m_previous_high)
                )

                add_target_level(
                    structural_levels,
                    m_previous_high,
                    "مقاومة Monthly سابقة",
                    "Monthly"
                )

        except Exception:
            pass

    # -----------------------------------------------------
    # 5. Fibonacci
    # -----------------------------------------------------

    fib_levels = [
        (
            last.get(
                "fib_ext_1272",
                np.nan
            ),
            "Fibonacci Extension 127.2%"
        ),
        (
            last.get(
                "fib_ext_1618",
                np.nan
            ),
            "Fibonacci Extension 161.8%"
        ),
        (
            last.get(
                "fib_ext_2000",
                np.nan
            ),
            "Fibonacci Extension 200%"
        )
    ]

    for level, reason in fib_levels:

        if (
            np.isfinite(level) and
            level > entry
        ):

            add_target_level(
                structural_levels,
                level,
                reason,
                "Fibonacci"
            )

    # =====================================================
    # تنظيف المستويات الهيكلية
    # =====================================================

    structural_levels = [
        x for x in structural_levels
        if (
            np.isfinite(x["price"]) and
            x["price"] > entry
        )
    ]

    structural_levels = deduplicate_levels(
        structural_levels,
        tolerance=0.008
    )

    # =====================================================
    # ATR Targets
    # =====================================================

    atr_targets = [
        (
            entry + atr_val * 1.5,
            "ATR 1.5"
        ),
        (
            entry + atr_val * 2.8,
            "ATR 2.8"
        ),
        (
            entry + atr_val * 4.5,
            "ATR 4.5"
        ),
        (
            entry + atr_val * 6.5,
            "ATR 6.5"
        )
    ]

    # =====================================================
    # دمج المستويات
    # =====================================================

    all_levels = []

    all_levels.extend(
        structural_levels
    )

    for price, reason in atr_targets:

        add_target_level(
            all_levels,
            price,
            reason,
            "ATR"
        )

    all_levels = [
        x for x in all_levels
        if x["price"] > entry
    ]

    all_levels = deduplicate_levels(
        all_levels,
        tolerance=0.01
    )

    all_levels = sorted(
        all_levels,
        key=lambda x: x["price"]
    )

    # =====================================================
    # Minimum Gap
    # =====================================================

    min_gap = max(
        atr_val * 0.55,
        entry * 0.015
    )

    # =====================================================
    # أقصى مسافة منطقية
    # =====================================================

    max_reasonable = (
        entry +
        atr_val * 10
    )

    # =====================================================
    # اختيار الأهداف
    #
    # الهدف الأقرب المنطقي أولاً،
    # ثم المستوى الهيكلي التالي،
    # ثم ATR كحل احتياطي.
    # =====================================================

    selected = []

    def choose_next(
        minimum_price,
        preferred_categories=None
    ):

        candidates = [
            x for x in all_levels
            if (
                x["price"] >= minimum_price and
                x["price"] <= max_reasonable
            )
        ]

        if preferred_categories:

            preferred = [
                x for x in candidates
                if x["category"] in preferred_categories
            ]

            if preferred:
                return min(
                    preferred,
                    key=lambda x: x["price"]
                )

        if candidates:

            return min(
                candidates,
                key=lambda x: x["price"]
            )

        return None

    # =====================================================
    # TP1
    #
    # أولوية للمقاومة القريبة / Swing
    # =====================================================

    tp1_level = choose_next(
        entry + atr_val * 1.0,
        [
            "Resistance",
            "Swing High",
            "Weekly"
        ]
    )

    if tp1_level is None:

        tp1_level = {
            "price": entry + atr_val * 1.5,
            "reason": "ATR 1.5 كحل احتياطي",
            "category": "ATR"
        }

    selected.append(
        tp1_level
    )

    # =====================================================
    # TP2
    #
    # يفضل Weekly / Monthly / Fibonacci
    # =====================================================

    tp2_level = choose_next(
        selected[-1]["price"] + min_gap,
        [
            "Weekly",
            "Monthly",
            "Swing High",
            "Fibonacci"
        ]
    )

    if tp2_level is None:

        tp2_level = {
            "price": max(
                selected[-1]["price"] + min_gap,
                entry + atr_val * 2.8
            ),
            "reason": "ATR 2.8 كحل احتياطي",
            "category": "ATR"
        }

    selected.append(
        tp2_level
    )

    # =====================================================
    # TP3
    # =====================================================

    tp3_level = choose_next(
        selected[-1]["price"] + min_gap,
        [
            "Monthly",
            "Fibonacci",
            "Swing High"
        ]
    )

    if tp3_level is None:

        tp3_level = {
            "price": max(
                selected[-1]["price"] + min_gap,
                entry + atr_val * 4.5
            ),
            "reason": "ATR 4.5 كحل احتياطي",
            "category": "ATR"
        }

    selected.append(
        tp3_level
    )

    # =====================================================
    # TP4
    # =====================================================

    tp4_level = choose_next(
        selected[-1]["price"] + min_gap,
        [
            "Monthly",
            "Fibonacci"
        ]
    )

    if tp4_level is None:

        tp4_level = {
            "price": max(
                selected[-1]["price"] + min_gap,
                entry + atr_val * 6.5
            ),
            "reason": "ATR 6.5 كحل احتياطي",
            "category": "ATR"
        }

    selected.append(
        tp4_level
    )

    # =====================================================
    # اتجاه قوي + Breakout
    # =====================================================

    if (
        strong_trend and
        breakout and
        volume_ratio >= 1.5
    ):

        selected[2]["price"] = max(
            selected[2]["price"],
            entry + atr_val * 4.5
        )

        selected[2]["reason"] += (
            " + تعزيز بسبب Breakout قوي"
        )

        selected[3]["price"] = max(
            selected[3]["price"],
            entry + atr_val * 7.0
        )

        selected[3]["reason"] += (
            " + تعزيز بسبب الاتجاه القوي"
        )

    # =====================================================
    # اتجاه قوي جدًا
    # =====================================================

    if (
        very_strong_trend and
        volume_ratio >= 1.5
    ):

        selected[3]["price"] = max(
            selected[3]["price"],
            entry + atr_val * 8.0
        )

        selected[3]["reason"] += (
            " + اتجاه قوي جدًا"
        )

    # =====================================================
    # فلتر الاتجاه
    # =====================================================

    if not strong_trend:

        selected[3]["price"] = min(
            selected[3]["price"],
            entry + atr_val * 6.0
        )

        selected[3]["reason"] += (
            " + تم تحديده بسبب قوة الاتجاه المحدودة"
        )

    # =====================================================
    # FINAL ORDER VALIDATION
    # =====================================================

    prices = [
        float(x["price"])
        for x in selected
    ]

    # إجبار الترتيب
    prices[0] = max(
        prices[0],
        entry + atr_val * 1.0
    )

    prices[1] = max(
        prices[1],
        prices[0] + min_gap
    )

    prices[2] = max(
        prices[2],
        prices[1] + min_gap
    )

    prices[3] = max(
        prices[3],
        prices[2] + min_gap
    )

    # =====================================================
    # منع TP4 من تجاوز الحد المعقول
    # =====================================================

    prices[3] = min(
        prices[3],
        max_reasonable
    )

    # إعادة ضبط عكسي
    prices[2] = min(
        prices[2],
        prices[3] - min_gap
    )

    prices[1] = min(
        prices[1],
        prices[2] - min_gap
    )

    prices[0] = min(
        prices[0],
        prices[1] - min_gap
    )

    # ضمان الحد الأدنى مرة أخرى
    prices[0] = max(
        prices[0],
        entry + atr_val
    )

    prices[1] = max(
        prices[1],
        prices[0] + min_gap
    )

    prices[2] = max(
        prices[2],
        prices[1] + min_gap
    )

    prices[3] = max(
        prices[3],
        prices[2] + min_gap
    )

    # =====================================================
    # أسباب الأهداف
    # =====================================================

    target_reasons = [
        selected[0]["reason"],
        selected[1]["reason"],
        selected[2]["reason"],
        selected[3]["reason"]
    ]

    target_categories = [
        selected[0]["category"],
        selected[1]["category"],
        selected[2]["category"],
        selected[3]["category"]
    ]

    # =====================================================
    # الأرباح %
    # =====================================================

    profits = [
        (
            price -
            entry
        ) /
        entry *
        100
        for price in prices
    ]

    # =====================================================
    # Risk / Reward
    # =====================================================

    rr = [
        (
            price -
            entry
        ) /
        (
            risk_per_share +
            1e-9
        )
        for price in prices
    ]

    # =====================================================
    # Target Quality Score
    # =====================================================

    category_points = {
        "Resistance": 1.00,
        "Swing High": 0.95,
        "Weekly": 0.90,
        "Monthly": 0.90,
        "Fibonacci": 0.80,
        "ATR": 0.65
    }

    quality_values = [
        category_points.get(
            category,
            0.60
        )
        for category in target_categories
    ]

    target_quality = (
        np.mean(
            quality_values
        ) * 100
    )

    # تعزيز إذا كانت الأهداف الأولى هيكلية
    if target_categories[0] != "ATR":
        target_quality += 5

    target_quality = min(
        100,
        target_quality
    )

    return {

        "entry": float(entry),

        "stop": float(stop),

        "tp1": float(prices[0]),
        "tp2": float(prices[1]),
        "tp3": float(prices[2]),
        "tp4": float(prices[3]),

        "tp1_profit_pct": float(profits[0]),
        "tp2_profit_pct": float(profits[1]),
        "tp3_profit_pct": float(profits[2]),
        "tp4_profit_pct": float(profits[3]),

        "tp1_reason": target_reasons[0],
        "tp2_reason": target_reasons[1],
        "tp3_reason": target_reasons[2],
        "tp4_reason": target_reasons[3],

        "tp1_category": target_categories[0],
        "tp2_category": target_categories[1],
        "tp3_category": target_categories[2],
        "tp4_category": target_categories[3],

        "rr1": float(rr[0]),
        "rr2": float(rr[1]),
        "rr3": float(rr[2]),
        "rr4": float(rr[3]),

        "target_quality": float(
            target_quality
        ),

        "risk_pct": float(
            risk_pct_actual * 100
        ),

        "position_size": float(
            position_size
        ),

        "position_value": float(
            position_value
        )
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

def estimate_probabilities(
    base_conf,
    rr1,
    rr2,
    rr3,
    rr4,
    alignment,
    adx_val
):

    trend_factor = (
        alignment /
        100
    )

    momentum_factor = min(
        1.0,
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

    tp1 = base

    if rr1 >= 2:
        tp1 += 0.05

    elif rr1 < 1.2:
        tp1 -= 0.10

    tp1 = min(
        0.90,
        max(
            0.20,
            tp1
        )
    )

    tp2 = tp1 * 0.82

    if rr2 >= 2:
        tp2 += 0.03

    elif rr2 < 1.5:
        tp2 -= 0.05

    tp2 = min(
        0.82,
        max(
            0.15,
            tp2
        )
    )

    tp3 = tp2 * 0.78

    if rr3 >= 2.5:
        tp3 += 0.03

    elif rr3 < 2:
        tp3 -= 0.05

    tp3 = min(
        0.75,
        max(
            0.10,
            tp3
        )
    )

    tp4 = tp3 * 0.72

    if rr4 >= 3:
        tp4 += 0.03

    elif rr4 < 2.5:
        tp4 -= 0.05

    tp4 = min(
        0.68,
        max(
            0.08,
            tp4
        )
    )

    return (
        tp1,
        tp2,
        tp3,
        tp4
    )


# =========================================================
# 🧠 التحليل الرئيسي
# =========================================================

def analyze(
    df_d,
    df_w,
    df_m,
    capital,
    risk_percent
):

    df_d = add_indicators(
        df_d
    )

    df_w = add_indicators(
        df_w
    )

    df_m = add_indicators(
        df_m
    )

    # =====================================================
    # التأكد من البيانات
    # =====================================================

    if len(df_d) < MIN_DAILY_ROWS:
        raise ValueError(
            "بيانات يومية غير كافية"
        )

    if len(df_w) < MIN_WEEKLY_ROWS:
        raise ValueError(
            "بيانات أسبوعية غير كافية"
        )

    if len(df_m) < MIN_MONTHLY_ROWS:
        raise ValueError(
            "بيانات شهرية غير كافية"
        )

    # =====================================================
    # Data Quality
    # =====================================================

    quality_d = calculate_data_quality(
        df_d
    )

    quality_w = calculate_data_quality(
        df_w
    )

    quality_m = calculate_data_quality(
        df_m
    )

    data_quality = (
        quality_d["quality"] * 0.50 +
        quality_w["quality"] * 0.30 +
        quality_m["quality"] * 0.20
    )

    # =====================================================
    # تنظيف المؤشرات
    # =====================================================

    required_daily = [
        "ema20",
        "ema50",
        "rsi",
        "macd",
        "macd_signal",
        "macd_hist",
        "vol_ma",
        "volume_ratio",
        "obv",
        "obv_ma",
        "obv_slope",
        "mfi",
        "stoch_rsi",
        "stoch_rsi_k",
        "stoch_rsi_d",
        "stoch_rsi_k_slope",
        "vwap",
        "support",
        "resistance",
        "previous_support",
        "previous_resistance",
        "atr",
        "adx",
        "ema20_slope",
        "ema50_slope",
        "body_pct"
    ]

    required_tf = [
        "ema20",
        "ema50",
        "macd",
        "macd_signal",
        "rsi",
        "ema20_slope"
    ]

    # EMA200 لا يدخل في required_tf
    # لأننا نريد معرفة هل هو مكتمل أم لا
    df_d = df_d.dropna(
        subset=required_daily
    )

    df_w = df_w.dropna(
        subset=required_tf
    )

    df_m = df_m.dropna(
        subset=required_tf
    )

    if (
        df_d.empty or
        df_w.empty or
        df_m.empty
    ):

        raise ValueError(
            "المؤشرات غير متاحة"
        )

    # =====================================================
    # آخر قراءة
    # =====================================================

    last_d = df_d.iloc[-1]
    last_w = df_w.iloc[-1]
    last_m = df_m.iloc[-1]

    market_price = float(
        last_d["Close"]
    )

    if market_price <= 0:
        raise ValueError(
            "سعر غير صحيح"
        )

    # =====================================================
    # EMA200 Quality
    # =====================================================

    daily_ema200_complete = (
        len(df_d) >= EMA200_REQUIRED_ROWS
    )

    weekly_ema200_complete = (
        len(df_w) >= EMA200_REQUIRED_ROWS
    )

    monthly_ema200_complete = (
        len(df_m) >= EMA200_REQUIRED_ROWS
    )

    ema200_status = (
        "✅ مكتمل"
        if (
            daily_ema200_complete and
            weekly_ema200_complete and
            monthly_ema200_complete
        )
        else "⚠️ غير مكتمل"
    )

    # =====================================================
    # Trend Alignment
    # =====================================================

    alignment = trend_alignment_score(
        df_d,
        df_w,
        df_m
    )

    # =====================================================
    # Market Regime
    # =====================================================

    regime = market_regime(
        last_d
    )

    # =====================================================
    # Entry Engine
    # =====================================================

    entry_info = determine_entry(
        df_d,
        alignment
    )

    entry = float(
        entry_info["price"]
    )

    entry_type = entry_info["type"]
    entry_reason = entry_info["reason"]

    # =====================================================
    # Risk / Target Engine
    # =====================================================

    risk = calculate_risk_engine(
        df_d,
        entry,
        capital,
        risk_percent,
        df_w,
        df_m
    )

    stop = risk["stop"]

    tp1 = risk["tp1"]
    tp2 = risk["tp2"]
    tp3 = risk["tp3"]
    tp4 = risk["tp4"]

    # =====================================================
    # Score جديد من 100
    #
    # 25 Trend
    # 15 Momentum
    # 15 Volume / Money Flow
    # 10 Trend Strength
    # 10 Price Structure
    # 10 Entry Quality
    # 10 Target Quality
    # 5 Risk
    #
    # TOTAL = 100
    # =====================================================

    score = 0.0

    # =====================================================
    # 1. Trend Quality = 25
    #
    # لا نكرر EMA20/50/200 بشكل زائد
    # =====================================================

    trend_component = (
        alignment * 0.25
    )

    score += trend_component

    # =====================================================
    # 2. Momentum = 15
    # =====================================================

    rsi = float(
        last_d["rsi"]
    )

    momentum_score = 0

    if 50 <= rsi <= 65:
        momentum_score += 7

    elif 45 <= rsi < 50:
        momentum_score += 5

    elif 65 < rsi <= 70:
        momentum_score += 5

    elif 35 <= rsi < 45:
        momentum_score += 2

    if (
        last_d["macd"] >
        last_d["macd_signal"]
    ):
        momentum_score += 5

    elif last_d["macd_hist"] > 0:
        momentum_score += 3

    stoch_k = float(
        last_d["stoch_rsi_k"]
    )

    stoch_d = float(
        last_d["stoch_rsi_d"]
    )

    if stoch_k > stoch_d:
        momentum_score += 3

    score += min(
        15,
        momentum_score
    )

    # =====================================================
    # 3. Volume / Money Flow = 15
    # =====================================================

    volume_ratio = float(
        last_d["volume_ratio"]
    )

    money_score = 0

    if volume_ratio >= 2:
        money_score += 5

    elif volume_ratio >= 1.5:
        money_score += 4

    elif volume_ratio >= 1.1:
        money_score += 3

    elif volume_ratio >= 0.8:
        money_score += 1

    mfi = float(
        last_d["mfi"]
    )

    if 50 <= mfi <= 75:
        money_score += 4

    elif 40 <= mfi < 50:
        money_score += 2

    elif 75 < mfi <= 85:
        money_score += 2

    obv = float(
        last_d["obv"]
    )

    obv_ma = float(
        last_d["obv_ma"]
    )

    obv_slope = float(
        last_d["obv_slope"]
    )

    if (
        obv > obv_ma and
        obv_slope > 0
    ):
        money_score += 6

    elif (
        obv > obv_ma or
        obv_slope > 0
    ):
        money_score += 4

    elif obv_slope > 0:
        money_score += 2

    score += min(
        15,
        money_score
    )

    # =====================================================
    # 4. Trend Strength = 10
    # =====================================================

    adx_val = float(
        last_d["adx"]
    )

    strength_score = 0

    if adx_val >= 30:
        strength_score = 10

    elif adx_val >= 25:
        strength_score = 8

    elif adx_val >= 20:
        strength_score = 6

    elif adx_val >= 15:
        strength_score = 3

    score += strength_score

    # =====================================================
    # 5. Price Structure = 10
    # =====================================================

    structure_score = 0

    if (
        last_d["ema20_slope"] > 0 and
        last_d["ema50_slope"] > 0
    ):
        structure_score += 4

    elif last_d["ema20_slope"] > 0:
        structure_score += 2

    if (
        last_d["Close"] >
        last_d["vwap"]
    ):
        structure_score += 3

    if (
        last_d["Close"] >
        last_d["ema50"]
    ):
        structure_score += 3

    score += min(
        10,
        structure_score
    )

    # =====================================================
    # 6. Entry Quality = 10
    # =====================================================

    entry_score = 0

    if entry_type == "دخول عند Pullback":
        entry_score = 10

    elif entry_type == "دخول اختراق":
        entry_score = 9

    elif entry_type == "دخول فوري":
        entry_score = 7

    else:
        entry_score = 2

    score += entry_score

    # =====================================================
    # 7. Target Quality = 10
    # =====================================================

    target_quality = float(
        risk["target_quality"]
    )

    target_component = (
        target_quality *
        0.10
    )

    score += target_component

    # =====================================================
    # 8. Risk Quality = 5
    # =====================================================

    rr1 = float(
        risk["rr1"]
    )

    risk_pct_actual = float(
        risk["risk_pct"]
    )

    risk_score = 0

    if rr1 >= 2:
        risk_score += 3

    elif rr1 >= 1.5:
        risk_score += 2

    elif rr1 >= 1.2:
        risk_score += 1

    if risk_pct_actual <= 5:
        risk_score += 2

    elif risk_pct_actual <= 8:
        risk_score += 1

    score += min(
        5,
        risk_score
    )

    # =====================================================
    # EMA200 incomplete penalty
    # =====================================================

    incomplete_count = sum([
        not daily_ema200_complete,
        not weekly_ema200_complete,
        not monthly_ema200_complete
    ])

    if incomplete_count >= 2:
        score -= 4

    elif incomplete_count == 1:
        score -= 2

    # =====================================================
    # لا نعطي 85+ إذا كان Entry مجرد انتظار
    # =====================================================

    if entry_type == "انتظار تأكيد":

        score = min(
            score,
            69
        )

    # =====================================================
    # Final Score
    # =====================================================

    score = min(
        100,
        max(
            0,
            score
        )
    )

    # =====================================================
    # Confidence
    # =====================================================

    base_conf = ai_confidence(
        last_d,
        last_w,
        last_m,
        alignment,
        data_quality
    )

    (
        tp1_prob,
        tp2_prob,
        tp3_prob,
        tp4_prob
    ) = estimate_probabilities(
        base_conf,
        risk["rr1"],
        risk["rr2"],
        risk["rr3"],
        risk["rr4"],
        alignment,
        adx_val
    )

    # =====================================================
    # Signal
    # =====================================================

    if (
        score >= 85 and
        rr1 >= 1.5 and
        alignment >= 65 and
        entry_type != "انتظار تأكيد"
    ):

        signal = "🔥 قوي جداً"

    elif (
        score >= 70 and
        rr1 >= 1.3 and
        entry_type != "انتظار تأكيد"
    ):

        signal = "🟢 قوي"

    elif score >= 55:

        signal = "🟡 متوسط"

    else:

        signal = "⚠️ متابعة"

    # =====================================================
    # المدة المتوقعة
    # =====================================================

    volatility = (
        float(last_d["atr"]) /
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

    # =====================================================
    # النتيجة
    # =====================================================

    return {

        "التقييم": round(
            score,
            2
        ),

        "الإشارة": signal,

        "الاتجاه": regime,

        "نوع الدخول": entry_type,

        "سبب الدخول": entry_reason,

        "سعر الدخول": round(
            entry,
            2
        ),

        "وقف الخسارة": round(
            stop,
            2
        ),

        "الهدف الأول": round(
            tp1,
            2
        ),

        "الهدف الثاني": round(
            tp2,
            2
        ),

        "الهدف الثالث": round(
            tp3,
            2
        ),

        "الهدف الرابع": round(
            tp4,
            2
        ),

        "سبب الهدف الأول": risk[
            "tp1_reason"
        ],

        "سبب الهدف الثاني": risk[
            "tp2_reason"
        ],

        "سبب الهدف الثالث": risk[
            "tp3_reason"
        ],

        "سبب الهدف الرابع": risk[
            "tp4_reason"
        ],

        "نوع الهدف الأول": risk[
            "tp1_category"
        ],

        "نوع الهدف الثاني": risk[
            "tp2_category"
        ],

        "نوع الهدف الثالث": risk[
            "tp3_category"
        ],

        "نوع الهدف الرابع": risk[
            "tp4_category"
        ],

        "ربح الهدف الأول %": round(
            risk["tp1_profit_pct"],
            2
        ),

        "ربح الهدف الثاني %": round(
            risk["tp2_profit_pct"],
            2
        ),

        "ربح الهدف الثالث %": round(
            risk["tp3_profit_pct"],
            2
        ),

        "ربح الهدف الرابع %": round(
            risk["tp4_profit_pct"],
            2
        ),

        "R/R الهدف الأول": round(
            risk["rr1"],
            2
        ),

        "R/R الهدف الثاني": round(
            risk["rr2"],
            2
        ),

        "R/R الهدف الثالث": round(
            risk["rr3"],
            2
        ),

        "R/R الهدف الرابع": round(
            risk["rr4"],
            2
        ),

        "ثقة الهدف الأول %": round(
            tp1_prob * 100,
            1
        ),

        "ثقة الهدف الثاني %": round(
            tp2_prob * 100,
            1
        ),

        "ثقة الهدف الثالث %": round(
            tp3_prob * 100,
            1
        ),

        "ثقة الهدف الرابع %": round(
            tp4_prob * 100,
            1
        ),

        "جودة الأهداف": round(
            target_quality,
            1
        ),

        "EMA200": ema200_status,

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

        # =================================================
        # معلومات داخلية
        # =================================================

        "_entry_type": entry_type,

        "_trend_alignment": round(
            alignment,
            2
        ),

        "_data_quality": round(
            data_quality,
            2
        ),

        "_ema200_daily": (
            "مكتمل"
            if daily_ema200_complete
            else "غير مكتمل"
        ),

        "_ema200_weekly": (
            "مكتمل"
            if weekly_ema200_complete
            else "غير مكتمل"
        ),

        "_ema200_monthly": (
            "مكتمل"
            if monthly_ema200_complete
            else "غير مكتمل"
        ),

        "_risk_pct": round(
            risk["risk_pct"],
            2
        ),

        "_rr1": round(
            risk["rr1"],
            2
        ),

        "_rr2": round(
            risk["rr2"],
            2
        ),

        "_rr3": round(
            risk["rr3"],
            2
        ),

        "_rr4": round(
            risk["rr4"],
            2
        ),

        "_target_quality": round(
            target_quality,
            2
        ),

        "_position_size": round(
            risk["position_size"],
            2
        ),

        "_position_value": round(
            risk["position_value"],
            2
        ),

        "_obv": round(
            obv,
            2
        ),

        "_obv_ma": round(
            obv_ma,
            2
        ),

        "_stoch_rsi_k": round(
            stoch_k,
            4
        ),

        "_stoch_rsi_d": round(
            stoch_d,
            4
        ),

        "_vwap": round(
            float(last_d["vwap"]),
            4
        ),

        "_pullback_quality": round(
            float(
                last_d.get(
                    "pullback_quality_score",
                    0
                )
            ),
            2
        ),

        "_volume_ratio": round(
            volume_ratio,
            2
        )
    }


# =========================================================
# ⚡ معالجة سهم واحد
# =========================================================

def process(
    symbol,
    daily,
    weekly,
    monthly,
    capital,
    risk_percent
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

        result = analyze(
            df_d,
            df_w,
            df_m,
            capital,
            risk_percent
        )

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
                risk_percent
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

        df_ok = df_ok.sort_values(
            "التقييم",
            ascending=False
        )

        # =================================================
        # أفضل الأسهم
        # =================================================

        st.subheader(
            f"🏆 أفضل {min(top_n, len(df_ok))} سهم"
        )

        top_df = df_ok.head(
            top_n
        ).copy()

        preferred_cols = [

            "السهم",
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

            "ثقة الهدف الأول %",
            "ثقة الهدف الثاني %",
            "ثقة الهدف الثالث %",
            "ثقة الهدف الرابع %",

            "مؤشر RSI",
            "قوة الاتجاه ADX",
            "التذبذب ATR %",
            "المدة المتوقعة"
        ]

        existing_cols = [
            c for c in preferred_cols
            if c in top_df.columns
        ]

        top_df = top_df[
            existing_cols
        ]

        st.dataframe(
            top_df,
            use_container_width=True,
            hide_index=True
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
            "EGX_AI_PRO_MAX_V7_RESULTS_AR.csv",
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
            "EGX_AI_PRO_MAX_V7_ERRORS_AR.csv",
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
