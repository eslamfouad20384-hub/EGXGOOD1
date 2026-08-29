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
    page_title="EGX AI PRO MAX v9 - عربي",
    page_icon="📈",
    layout="wide"
)

st.title("🚀 EGX AI PRO MAX v9")
st.caption(
    "📊 فحص الأسهم المصرية • تحليل متعدد الفترات • Entry/Target Engine احترافي • Risk Management"
)

# =========================================================
# 📌 قائمة الأسهم
# =========================================================

EGX100 = [
"COMI.CA", "MFPC.CA", "PHDC.CA", "ORAS.CA",
"HRHO.CA", "TMGH.CA", "FWRY.CA", "SWDY.CA", "ETEL.CA",
"AMOC.CA", "HELI.CA", "EAST.CA", "EFID.CA", "JUFO.CA",
"ABUK.CA", "ESRS.CA", "EMFD.CA", "MASR.CA", "CCAP.CA",
"CICH.CA", "OCDI.CA", "ORHD.CA",
"ADIB.CA", "SAUD.CA", "CIEB.CA", "FAIT.CA",
"CANA.CA", "EXPA.CA", "ARCC.CA", "AJWA.CA", "MICH.CA",
"SUGR.CA", "POUL.CA", "DOMT.CA", "ISMA.CA", "UEGC.CA",
"GBCO.CA", "OLFI.CA", "SKPC.CA", "AMER.CA", "TALM.CA",
"ORWE.CA", "SPMD.CA", "ZMID.CA", "MENA.CA", "DAPH.CA",
"RAYA.CA", "EGAL.CA", "ECAP.CA", "MPRC.CA",
"NCCW.CA", "SCEM.CA", "ARAB.CA", "GDWA.CA", "ELEC.CA",
"IRON.CA", "ATQA.CA", "EGCH.CA", "ALCN.CA",
"MPCO.CA", "ELSH.CA", "MEPA.CA", "ODIN.CA", "EGAS.CA",
"RACC.CA", "PRCL.CA", "BINV.CA", "EDBM.CA", "MCQE.CA",
"MOIL.CA", "NIPH.CA", "ISPH.CA", "DSCW.CA",
"UNIT.CA", "PHAR.CA", "TRTO.CA",
"ICFC.CA", "ELKA.CA", "ATLC.CA", "COSG.CA", "AMPI.CA", "COPR.CA",

"QNBE.CA", "HDBK.CA", "EFIH.CA", "BTFH.CA",
"CLHO.CA", "VALU.CA", "MBSC.CA", "CIRA.CA",
"MTIE.CA", "EGTS.CA", "EGSA.CA", "UBEE.CA",
"MHOT.CA", "EGBE.CA", "IFAP.CA", "PRDC.CA",
"MIPH.CA", "MPCI.CA", "MOIN.CA", "ISMQ.CA",
"BONY.CA", "AXPH.CA", "PHTV.CA", "CPCI.CA",
"NINH.CA", "SPIN.CA", "ENGC.CA", "ACAP.CA",
"NAPR.CA", "CNFN.CA", "SVCE.CA", "KABO.CA",
"OFH.CA", "GSSC.CA", "WCDF.CA", "MFSC.CA",
"SAIB.CA", "ACGC.CA", "UEFM.CA", "KZPC.CA",
"ADCI.CA", "INFI.CA", "ACTF.CA", "ASCM.CA",
"ZEOT.CA", "GPIM.CA", "SMFR.CA", "ETRS.CA",
"EDFM.CA", "MILS.CA"
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
    min_value=100,
    max_value=1000,
    value=300,
    step=50
)

# تكاليف التنفيذ والقيود الواقعية
st.sidebar.markdown("---")
st.sidebar.header("🧾 واقعية التنفيذ")
commission_pct = st.sidebar.number_input(
    "عمولة التنفيذ لكل جانب %", min_value=0.0, max_value=2.0, value=0.15, step=0.01
)
slippage_pct = st.sidebar.number_input(
    "Slippage لكل جانب %", min_value=0.0, max_value=2.0, value=0.10, step=0.01
)
max_position_pct = st.sidebar.slider(
    "أقصى حجم مركز من رأس المال %", min_value=5, max_value=100, value=20, step=5
)
monte_carlo_runs = st.sidebar.slider(
    "عدد محاكاة Monte Carlo", min_value=100, max_value=2000, value=500, step=100
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
    • Backtest واقعي بتكاليف التنفيذ وSlippage
    • Strict Structural Targets فقط في Backtest
    • Partial Take Profit + Trailing Stop
    • Historical TP Probability / Expectancy
    • Walk-Forward / Out-of-Sample
    • Monte Carlo / Sharpe / Sortino / Calmar
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
DEFAULT_COMMISSION_PCT = 0.15
DEFAULT_SLIPPAGE_PCT = 0.10
DEFAULT_MAX_POSITION_PCT = 20.0

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
    # V9: position-size cap prevents a mathematically valid but practically
    # oversized position when the stop is tight.
    max_position_value = capital * (DEFAULT_MAX_POSITION_PCT / 100.0)
    position_size = min(position_size, max_position_value / entry)
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
    # Liquidity + Relative Strength
    # =====================================================
    liquidity_ratio = float(last_d.get("liquidity_ratio", np.nan))
    if not np.isfinite(liquidity_ratio)
