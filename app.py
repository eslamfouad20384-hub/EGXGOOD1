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
    page_title="EGX AI PRO MAX v6 - عربي",
    page_icon="📈",
    layout="wide"
)

st.title("🚀 EGX AI PRO MAX v6")
st.caption(
    "📊 فحص الأسهم المصرية • تحليل متعدد الفترات • تقييم ذكي • محرك بيانات سريع"
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
    "MPCO.CA", "ELSH.CA", "NCCW.CA", "MEPA.CA", "ODIN.CA",
    "EGAS.CA", "MENA.CA", "RACC.CA", "PRCL.CA", "BINV.CA",
    "EDBM.CA", "MCQE.CA", "MOIL.CA", "NIPH.CA", "ISPH.CA",
    "DICE.CA", "BINV.CA", "IDHC.CA", "UNIT.CA", "PHAR.CA",
    "TRTO.CA", "ALRA.CA", "FARE.CA", "ICFC.CA", "MISr.CA",
    "MOBI.CA", "RACC.CA", "ELKA.CA", "NILE.CA", "ATLC.CA",
    "COSG.CA", "MEDA.CA", "ELSH.CA", "AMPI.CA", "COPR.CA"
]

# إزالة التكرارات مع الحفاظ على الترتيب
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

# =========================================================
# تعديل: فترة Weekly أطول لدعم EMA200 بشكل أفضل
# =========================================================

period_weekly = st.sidebar.selectbox(
    "📅 فترة البيانات الأسبوعية",
    ["3y", "5y", "10y", "max"],
    index=1
)

# =========================================================
# تعديل: فترة Monthly أطول لدعم EMA200 بشكل أفضل
# =========================================================

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
# 💰 إعدادات إدارة رأس المال
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

    • الاتجاه اليومي
    • الاتجاه الأسبوعي
    • الاتجاه الشهري
    • EMA20
    • EMA50
    • EMA200
    • RSI
    • MACD
    • Volume
    • OBV
    • MFI
    • Stochastic RSI
    • VWAP
    • Volume Ratio
    • ATR
    • ADX
    • الدعم والمقاومة
    • Fibonacci
    • Fibonacci Extensions
    • Breakout
    • Pullback
    • Trend Slope
    • Trend Alignment
    • Entry Engine
    • Risk Engine
    • Professional Target Engine
    • التقييم النهائي
    • الدخول
    • وقف الخسارة
    • 4 أهداف
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

        # -------------------------------------------------
        # MultiIndex
        # -------------------------------------------------

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

        # -------------------------------------------------
        # تنظيف أسماء الأعمدة
        # -------------------------------------------------

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

        # -------------------------------------------------
        # تحويل البيانات لأرقام
        # -------------------------------------------------

        for col in required:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

        # -------------------------------------------------
        # إزالة القيم غير الصحيحة
        # -------------------------------------------------

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

        # Volume ممكن يكون صفر
        df["Volume"] = df["Volume"].fillna(0)

        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        df = df[
            (df["High"] >= df["Low"]) &
            (df["Close"] > 0) &
            (df["Open"] > 0)
        ]

        df = df.sort_index()

        # إزالة التواريخ المكررة
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

    total_cells = (
        len(df) *
        len(required)
    )

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

    # خصم بسيط لو عدد الشموع قليل
    if len(df) < 50:

        quality *= (
            len(df) / 50
        )

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
    # EMA
    # =====================================================

    df["ema20"] = close.ewm(
        span=20,
        adjust=False
    ).mean()

    df["ema50"] = close.ewm(
        span=50,
        adjust=False
    ).mean()

    # =====================================================
    # EMA200
    # تحسين: عدم اعتبار EMA200 صالحة من أول شمعة
    # مع السماح بالعمل على الأسهم ذات التاريخ الأقصر
    # =====================================================

    ema200_min_periods = min(
        200,
        max(
            50,
            len(df) // 2
        )
    )

    df["ema200"] = close.ewm(
        span=200,
        adjust=False,
        min_periods=ema200_min_periods
    ).mean()

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

    except Exception:

        df["obv"] = np.nan
        df["obv_ma"] = np.nan

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

    except Exception:

        df["stoch_rsi"] = np.nan
        df["stoch_rsi_k"] = np.nan
        df["stoch_rsi_d"] = np.nan

    # =====================================================
    # VWAP
    # =====================================================

    try:

        typical_price = (
            high +
            low +
            close
        ) / 3

        cumulative_volume = (
            vol.cumsum()
        )

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

    except Exception:

        df["vwap"] = np.nan

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
    # Fibonacci Extensions - أهداف ممتدة
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
    # Previous Support / Resistance
    # مهم: لا نعتمد على الشمعة الحالية
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
    # Breakout
    # مهم:
    # الاعتماد على المقاومة السابقة فقط
    # وعدم استخدام الشمعة الحالية
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

    df["breakout"] = (
        (
            close >
            previous_resistance
        ) &
        (
            df["volume_ratio"] >= 1.2
        )
    )

    # =====================================================
    # Pullback
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

    df["pullback"] = (
        (
            distance_ema20 <= 0.025
        ) |
        (
            distance_ema50 <= 0.035
        )
    ) & (
        close >=
        df["ema50"] * 0.97
    )

    return df


# =========================================================
# 🧠 MARKET REGIME
# =========================================================

def market_regime(last):

    score = 0

    if last["Close"] > last["ema200"]:
        score += 1

    if last["ema20"] > last["ema50"]:
        score += 1

    if last["ema50"] > last["ema200"]:
        score += 1

    if last["macd"] > last["macd_signal"]:
        score += 1

    if last["rsi"] > 50:
        score += 1

    if last["adx"] > 20:
        score += 1

    if score >= 6:

        return "🚀 قوي جداً"

    elif score >= 4:

        return "🟢 صعود"

    elif score >= 3:

        return "🟡 محايد"

    else:

        return "🔴 هبوط"


# =========================================================
# 📊 TREND ALIGNMENT SCORE
# =========================================================

def timeframe_score(df):

    if df is None or df.empty:

        return 0

    last = df.iloc[-1]

    score = 0

    # السعر مقابل EMA200
    if last["Close"] > last["ema200"]:
        score += 25

    # EMA20 / EMA50
    if last["ema20"] > last["ema50"]:
        score += 20

    # EMA50 / EMA200
    if last["ema50"] > last["ema200"]:
        score += 20

    # MACD
    if last["macd"] > last["macd_signal"]:
        score += 15

    # RSI
    if last["rsi"] > 50:
        score += 10

    # Trend Slope
    if last["ema20_slope"] > 0:
        score += 10

    return score


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
# 🎯 ENTRY ENGINE
# =========================================================

def determine_entry(
    df_d,
    entry
):

    last = df_d.iloc[-1]

    support = float(
        last["support"]
    )

    # =====================================================
    # مهم:
    # استخدام المقاومة السابقة فقط
    # وعدم استخدام مقاومة تشمل الشمعة الحالية
    # =====================================================

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
        last["pullback"]
    )

    volume_ratio = float(
        last["volume_ratio"]
    )

    # =====================================================
    # 1. Breakout
    # =====================================================

    if (
        breakout and
        np.isfinite(previous_resistance) and
        entry > previous_resistance and
        volume_ratio >= 1.5
    ):

        return {
            "type": "دخول اختراق",
            "price": entry
        }

    # =====================================================
    # 2. Pullback
    # =====================================================

    if (
        pullback and
        ema20 > ema50
    ):

        pullback_price = max(
            support,
            min(
                ema20,
                ema50
            )
        )

        return {
            "type": "دخول عند Pullback",
            "price": pullback_price
        }

    # =====================================================
    # 3. Immediate
    # =====================================================

    if (
        entry > ema20 and
        entry > ema50 and
        last["rsi"] >= 50 and
        last["macd"] > last["macd_signal"]
    ):

        return {
            "type": "دخول فوري",
            "price": entry
        }

    # =====================================================
    # 4. Confirmation
    # =====================================================

    return {
        "type": "انتظار تأكيد",
        "price": entry
    }


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

    # =====================================================
    # البيانات الأساسية
    # =====================================================

    support = float(
        last["support"]
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
    # Fibonacci Extensions
    # =====================================================

    fib_ext_1272 = float(
        last.get(
            "fib_ext_1272",
            np.nan
        )
    )

    fib_ext_1618 = float(
        last.get(
            "fib_ext_1618",
            np.nan
        )
    )

    fib_ext_2000 = float(
        last.get(
            "fib_ext_2000",
            np.nan
        )
    )

    # =====================================================
    # Daily Resistance
    # =====================================================

    daily_levels = []

    for level in [
        previous_resistance,
        resistance
    ]:

        if (
            np.isfinite(level) and
            level > entry
        ):

            daily_levels.append(
                float(level)
            )

    # =====================================================
    # Weekly Resistance
    # =====================================================

    weekly_levels = []

    if (
        df_w is not None and
        not df_w.empty
    ):

        try:

            w_high = (
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
                np.isfinite(w_high) and
                w_high > entry
            ):

                weekly_levels.append(
                    float(w_high)
                )

        except Exception:
            pass

    # =====================================================
    # Monthly Resistance
    # =====================================================

    monthly_levels = []

    if (
        df_m is not None and
        not df_m.empty
    ):

        try:

            m_high = (
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
                np.isfinite(m_high) and
                m_high > entry
            ):

                monthly_levels.append(
                    float(m_high)
                )

        except Exception:
            pass

    # =====================================================
    # Fibonacci Extension Levels
    # =====================================================

    fib_levels = []

    for level in [
        fib_ext_1272,
        fib_ext_1618,
        fib_ext_2000
    ]:

        if (
            np.isfinite(level) and
            level > entry
        ):

            fib_levels.append(
                float(level)
            )

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

    strong_volume = (
        volume_ratio >= 1.5
    )

    # =====================================================
    # Stop Loss
    # =====================================================

    if bullish:

        atr_stop = (
            entry -
            atr_val * 1.5
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

    else:

        stop = (
            entry -
            atr_val * 1.2
        )

        if stop <= 0:

            stop = (
                entry * 0.95
            )

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
    # Professional Target Engine
    # =====================================================

    atr_distance = atr_val

    # =====================================================
    # بناء المستويات المحتملة
    # =====================================================

    all_levels = []

    all_levels.extend(
        daily_levels
    )

    all_levels.extend(
        weekly_levels
    )

    all_levels.extend(
        monthly_levels
    )

    all_levels.extend(
        fib_levels
    )

    # =====================================================
    # ATR Targets
    # =====================================================

    atr_target_1 = (
        entry +
        atr_distance * 1.5
    )

    atr_target_2 = (
        entry +
        atr_distance * 2.8
    )

    atr_target_3 = (
        entry +
        atr_distance * 4.5
    )

    atr_target_4 = (
        entry +
        atr_distance * 6.5
    )

    all_levels.extend([
        atr_target_1,
        atr_target_2,
        atr_target_3,
        atr_target_4
    ])

    # =====================================================
    # تنظيف المستويات
    # =====================================================

    clean_levels = []

    for level in all_levels:

        try:

            level = float(level)

            if (
                np.isfinite(level) and
                level > entry
            ):

                clean_levels.append(
                    level
                )

        except Exception:
            continue

    clean_levels = sorted(
        set(
            round(
                x,
                6
            )
            for x in clean_levels
        )
    )

    # =====================================================
    # Minimum Gap
    # =====================================================

    min_gap = max(
        atr_val * 0.55,
        entry * 0.015
    )

    # =====================================================
    # TP1
    # =====================================================

    tp1_candidates = [
        x for x in clean_levels
        if x >= (
            entry +
            atr_val * 1.15
        )
    ]

    if tp1_candidates:

        tp1 = min(
            tp1_candidates
        )

    else:

        tp1 = atr_target_1

    # =====================================================
    # TP2
    # =====================================================

    tp2_candidates = [
        x for x in clean_levels
        if x >= (
            tp1 +
            min_gap
        )
    ]

    if tp2_candidates:

        structural_tp2 = [
            x for x in tp2_candidates
            if x in (
                daily_levels +
                weekly_levels +
                monthly_levels +
                fib_levels
            )
        ]

        if structural_tp2:

            tp2 = min(
                structural_tp2
            )

        else:

            tp2 = min(
                tp2_candidates
            )

    else:

        tp2 = max(
            tp1 + min_gap,
            atr_target_2
        )

    # =====================================================
    # TP3
    # =====================================================

    tp3_candidates = [
        x for x in clean_levels
        if x >= (
            tp2 +
            min_gap
        )
    ]

    if tp3_candidates:

        structural_tp3 = [
            x for x in tp3_candidates
            if x in (
                weekly_levels +
                monthly_levels +
                fib_levels
            )
        ]

        if structural_tp3:

            tp3 = min(
                structural_tp3
            )

        else:

            tp3 = min(
                tp3_candidates
            )

    else:

        tp3 = max(
            tp2 + min_gap,
            atr_target_3
        )

    # =====================================================
    # TP4
    # =====================================================

    tp4_candidates = [
        x for x in clean_levels
        if x >= (
            tp3 +
            min_gap
        )
    ]

    if tp4_candidates:

        structural_tp4 = [
            x for x in tp4_candidates
            if x in (
                monthly_levels +
                fib_levels
            )
        ]

        if structural_tp4:

            tp4 = max(
                structural_tp4
            )

        else:

            tp4 = max(
                tp4_candidates
            )

    else:

        tp4 = max(
            tp3 + min_gap,
            atr_target_4
        )

    # =====================================================
    # فلتر قوة الاتجاه
    # =====================================================

    if not strong_trend:

        tp4 = min(
            tp4,
            entry +
            atr_val * 6.0
        )

    # =====================================================
    # اتجاه قوي + Breakout + Volume
    # =====================================================

    if (
        strong_trend and
        breakout and
        strong_volume
    ):

        tp3 = max(
            tp3,
            entry +
            atr_val * 4.5
        )

        tp4 = max(
            tp4,
            entry +
            atr_val * 7.0
        )

    # =====================================================
    # اتجاه قوي جدًا
    # =====================================================

    if (
        very_strong_trend and
        volume_ratio >= 1.5
    ):

        tp4 = max(
            tp4,
            entry +
            atr_val * 8.0
        )

    # =====================================================
    # FINAL TARGET ORDER VALIDATION
    # =====================================================

    tp1 = max(
        tp1,
        entry +
        atr_val * 1.0
    )

    tp2 = max(
        tp2,
        tp1 +
        min_gap
    )

    tp3 = max(
        tp3,
        tp2 +
        min_gap
    )

    tp4 = max(
        tp4,
        tp3 +
        min_gap
    )

    # =====================================================
    # منع الأهداف المبالغ فيها
    # =====================================================

    max_reasonable = (
        entry +
        atr_val * 10
    )

    tp4 = min(
        tp4,
        max_reasonable
    )

    # إعادة ضمان الترتيب
    tp3 = min(
        tp3,
        tp4 - min_gap
    )

    tp2 = min(
        tp2,
        tp3 - min_gap
    )

    tp1 = min(
        tp1,
        tp2 - min_gap
    )

    # =====================================================
    # الأرباح %
    # =====================================================

    tp1_profit_pct = (
        (
            tp1 -
            entry
        ) /
        entry
    ) * 100

    tp2_profit_pct = (
        (
            tp2 -
            entry
        ) /
        entry
    ) * 100

    tp3_profit_pct = (
        (
            tp3 -
            entry
        ) /
        entry
    ) * 100

    tp4_profit_pct = (
        (
            tp4 -
            entry
        ) /
        entry
    ) * 100

    # =====================================================
    # Risk / Reward
    # =====================================================

    rr1 = (
        tp1 -
        entry
    ) / (
        risk_per_share +
        1e-9
    )

    rr2 = (
        tp2 -
        entry
    ) / (
        risk_per_share +
        1e-9
    )

    rr3 = (
        tp3 -
        entry
    ) / (
        risk_per_share +
        1e-9
    )

    rr4 = (
        tp4 -
        entry
    ) / (
        risk_per_share +
        1e-9
    )

    return {

        "entry": float(entry),

        "stop": float(stop),

        "tp1": float(tp1),

        "tp2": float(tp2),

        "tp3": float(tp3),

        "tp4": float(tp4),

        "tp1_profit_pct": float(
            tp1_profit_pct
        ),

        "tp2_profit_pct": float(
            tp2_profit_pct
        ),

        "tp3_profit_pct": float(
            tp3_profit_pct
        ),

        "tp4_profit_pct": float(
            tp4_profit_pct
        ),

        "risk_pct": float(
            risk_pct_actual * 100
        ),

        "rr1": float(rr1),

        "rr2": float(rr2),

        "rr3": float(rr3),

        "rr4": float(rr4),

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
    total = 10

    # Daily trend
    if last_d["Close"] > last_d["ema200"]:
        score += 1

    # Weekly trend
    if last_w["Close"] > last_w["ema200"]:
        score += 1

    # Monthly trend
    if last_m["Close"] > last_m["ema200"]:
        score += 1

    # MACD
    if last_d["macd"] > last_d["macd_signal"]:
        score += 1

    # RSI healthy
    if 45 < last_d["rsi"] < 70:
        score += 1

    # Volume
    if last_d["volume_ratio"] > 1:
        score += 1

    # ADX
    if last_d["adx"] > 20:
        score += 1

    # MFI
    if 40 < last_d["mfi"] < 80:
        score += 1

    # Trend Alignment
    if alignment >= 60:
        score += 1

    # Data Quality
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

    # =====================================================
    # TP1
    # =====================================================

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

    # =====================================================
    # TP2
    # =====================================================

    tp2 = (
        tp1 * 0.82
    )

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

    # =====================================================
    # TP3
    # =====================================================

    tp3 = (
        tp2 * 0.78
    )

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

    # =====================================================
    # TP4
    # =====================================================

    tp4 = (
        tp3 * 0.72
    )

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

    # =====================================================
    # إضافة المؤشرات
    # =====================================================

    df_d = add_indicators(df_d)
    df_w = add_indicators(df_w)
    df_m = add_indicators(df_m)

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
        "ema200",
        "rsi",
        "macd",
        "macd_signal",
        "vol_ma",
        "volume_ratio",
        "support",
        "resistance",
        "atr",
        "adx",
        "mfi",
        "ema20_slope",
        "ema50_slope"
    ]

    required_tf = [
        "ema200",
        "ema20",
        "ema50",
        "macd",
        "macd_signal",
        "rsi",
        "ema20_slope"
    ]

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
        market_price
    )

    entry = float(
        entry_info["price"]
    )

    entry_type = entry_info["type"]

    # =====================================================
    # Risk Engine
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

    tp1_profit_pct = risk[
        "tp1_profit_pct"
    ]

    tp2_profit_pct = risk[
        "tp2_profit_pct"
    ]

    tp3_profit_pct = risk[
        "tp3_profit_pct"
    ]

    tp4_profit_pct = risk[
        "tp4_profit_pct"
    ]

    rr1 = risk["rr1"]
    rr2 = risk["rr2"]
    rr3 = risk["rr3"]
    rr4 = risk["rr4"]

    volatility = (
        float(last_d["atr"]) /
        entry
    )

    # =====================================================
    # ⭐ SCORE من 100
    # =====================================================

    score = 0.0

    # -----------------------------------------------------
    # Trend Alignment 30
    # -----------------------------------------------------

    score += (
        alignment *
        0.30
    )

    # -----------------------------------------------------
    # RSI 10
    # -----------------------------------------------------

    rsi = float(
        last_d["rsi"]
    )

    if 50 <= rsi <= 65:

        score += 10

    elif 45 <= rsi < 50:

        score += 7

    elif 65 < rsi <= 70:

        score += 7

    elif 35 <= rsi < 45:

        score += 4

    # -----------------------------------------------------
    # MACD 10
    # -----------------------------------------------------

    if (
        last_d["macd"] >
        last_d["macd_signal"]
    ):

        score += 10

    elif (
        last_d["macd_hist"] >
        0
    ):

        score += 6

    # -----------------------------------------------------
    # Volume 10
    # -----------------------------------------------------

    volume_ratio = float(
        last_d["volume_ratio"]
    )

    if volume_ratio >= 2:

        score += 10

    elif volume_ratio >= 1.5:

        score += 8

    elif volume_ratio >= 1.1:

        score += 6

    elif volume_ratio >= 0.8:

        score += 3

    # -----------------------------------------------------
    # ADX 10
    # -----------------------------------------------------

    adx_val = float(
        last_d["adx"]
    )

    if adx_val >= 30:

        score += 10

    elif adx_val >= 25:

        score += 8

    elif adx_val >= 20:

        score += 6

    elif adx_val >= 15:

        score += 3

    # -----------------------------------------------------
    # MFI 5
    # -----------------------------------------------------

    mfi = float(
        last_d["mfi"]
    )

    if 50 <= mfi <= 75:

        score += 5

    elif 40 <= mfi < 50:

        score += 3

    elif 75 < mfi <= 85:

        score += 3

    # -----------------------------------------------------
    # Trend Slope 5
    # -----------------------------------------------------

    if (
        last_d["ema20_slope"] > 0 and
        last_d["ema50_slope"] > 0
    ):

        score += 5

    elif (
        last_d["ema20_slope"] > 0
    ):

        score += 3

    # -----------------------------------------------------
    # Entry Quality 10
    # -----------------------------------------------------

    if entry_type == "دخول فوري":

        score += 7

    elif entry_type == "دخول عند Pullback":

        score += 10

    elif entry_type == "دخول اختراق":

        score += 9

    else:

        score += 3

    # -----------------------------------------------------
    # Risk / Reward 10
    # -----------------------------------------------------

    if rr1 >= 2:

        score += 10

    elif rr1 >= 1.5:

        score += 7

    elif rr1 >= 1.2:

        score += 4

    # -----------------------------------------------------
    # Data Quality adjustment
    # -----------------------------------------------------

    if data_quality >= 95:

        score += 5

    elif data_quality >= 90:

        score += 3

    elif data_quality < 75:

        score -= 5

    # -----------------------------------------------------
    # الحد النهائي
    # -----------------------------------------------------

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

    # =====================================================
    # تقدير الثقة المحافظة
    # =====================================================

    (
        tp1_prob,
        tp2_prob,
        tp3_prob,
        tp4_prob
    ) = estimate_probabilities(
        base_conf,
        rr1,
        rr2,
        rr3,
        rr4,
        alignment,
        adx_val
    )

    # =====================================================
    # Signal
    # =====================================================

    if (
        score >= 85 and
        rr1 >= 1.5 and
        alignment >= 65
    ):

        signal = "🔥 قوي جداً"

    elif (
        score >= 70 and
        rr1 >= 1.3
    ):

        signal = "🟢 قوي"

    elif score >= 55:

        signal = "🟡 متوسط"

    else:

        signal = "⚠️ متابعة"

    # =====================================================
    # المدة المتوقعة
    # =====================================================

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

        "ربح الهدف الأول %": round(
            tp1_profit_pct,
            2
        ),

        "ربح الهدف الثاني %": round(
            tp2_profit_pct,
            2
        ),

        "ربح الهدف الثالث %": round(
            tp3_profit_pct,
            2
        ),

        "ربح الهدف الرابع %": round(
            tp4_profit_pct,
            2
        ),

        "احتمال الهدف الأول %": round(
            tp1_prob * 100,
            1
        ),

        "احتمال الهدف الثاني %": round(
            tp2_prob * 100,
            1
        ),

        "احتمال الهدف الثالث %": round(
            tp3_prob * 100,
            1
        ),

        "احتمال الهدف الرابع %": round(
            tp4_prob * 100,
            1
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

        # =================================================
        # معلومات داخلية للمحرك
        # لا يتم عرضها في الجداول للحفاظ على شكلها
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

        "_risk_pct": round(
            risk["risk_pct"],
            2
        ),

        "_rr1": round(
            rr1,
            2
        ),

        "_rr2": round(
            rr2,
            2
        ),

        "_rr3": round(
            rr3,
            2
        ),

        "_rr4": round(
            rr4,
            2
        ),

        "_position_size": round(
            risk["position_size"],
            2
        ),

        "_position_value": round(
            risk["position_value"],
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

        # =================================================
        # استخراج البيانات
        # =================================================

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

        # =================================================
        # Validation
        # =================================================

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

        # =================================================
        # التحليل
        # =================================================

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
            "الحالة": f"❌ {str(e)[:80]}"
        }


# =========================================================
# 🚀 تشغيل الفحص
# =========================================================

if st.button(
    "🚀 بدء فحص الأسهم",
    use_container_width=True
):

    # =====================================================
    # الحالة
    # =====================================================

    st.info(
        f"📡 جاري فحص {TOTAL_STOCKS} سهم..."
    )

    progress = st.progress(
        0
    )

    status_text = st.empty()

    # =====================================================
    # 📥 البيانات اليومية
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
    # 📥 البيانات الأسبوعية
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
    # 📥 البيانات الشهرية
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
    # 📊 فحص Data Engine
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
                )
        })

    # =====================================================
    # 🧠 التحليل
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
                        f"❌ {str(e)[:80]}"
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
    # 📊 النتائج
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
    # 📈 الأسهم التي تم تحليلها بنجاح
    # إصلاح: تعريف df_ok قبل استخدامه
    # =====================================================

    df_ok = df_all[
        df_all["الحالة"] == "✅ تم التحليل"
    ].copy()

    # =====================================================
    # 📊 التغطية
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
    # 📊 Data Engine Quality
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

    else:

        avg_quality = 0
        daily_coverage = 0
        weekly_coverage = 0
        monthly_coverage = 0

    # =====================================================
    # 📊 مؤشرات عامة
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
    # 📡 Data Engine Quality
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

    # =====================================================
    # 📈 الأسهم الناجحة
    # =====================================================

    if not df_ok.empty:

        # =================================================
        # ترتيب حسب التقييم
        # =================================================

        df_ok = df_ok.sort_values(
            "التقييم",
            ascending=False
        )

        # =================================================
        # 🏆 أفضل الأسهم
        # =================================================

        st.subheader(
            f"🏆 أفضل {min(top_n, len(df_ok))} سهم"
        )

        top_df = df_ok.head(
            top_n
        ).copy()

        # =================================================
        # كل الأعمدة القديمة + الأعمدة الجديدة
        # =================================================

        preferred_cols = [

            "السهم",

            "التقييم",

            "الإشارة",

            "الاتجاه",

            "سعر الدخول",

            "وقف الخسارة",

            "الهدف الأول",

            "الهدف الثاني",

            "الهدف الثالث",

            "الهدف الرابع",

            "ربح الهدف الأول %",

            "ربح الهدف الثاني %",

            "ربح الهدف الثالث %",

            "ربح الهدف الرابع %",

            "احتمال الهدف الأول %",

            "احتمال الهدف الثاني %",

            "احتمال الهدف الثالث %",

            "احتمال الهدف الرابع %",

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
        # 🔥 الأسهم القوية
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
        # 📋 جميع الأسهم المحللة
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
        # 💾 تحميل النتائج
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
            "EGX_AI_PRO_MAX_RESULTS_AR.csv",
            "text/csv",
            use_container_width=True
        )

        # =================================================
        # 📊 تفاصيل المحرك الداخلي
        # =================================================

        with st.expander(
            "🔬 معلومات المحرك المتقدمة"
        ):

            internal_cols = [
                "السهم",
                "_entry_type",
                "_trend_alignment",
                "_data_quality",
                "_risk_pct",
                "_rr1",
                "_rr2",
                "_rr3",
                "_rr4",
                "_position_size",
                "_position_value"
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

                        "_position_size":
                            "حجم المركز",

                        "_position_value":
                            "قيمة المركز"
                    }
                )
            )

            st.dataframe(
                internal_df,
                use_container_width=True,
                hide_index=True
            )

        # =================================================
        # 📡 Data Quality Details
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
                            "جودة البيانات %"
                    }
                )
            )

            st.dataframe(
                quality_display,
                use_container_width=True,
                hide_index=True
            )

    # =====================================================
    # ⚠️ الأسهم الفاشلة
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
            "EGX_AI_PRO_MAX_ERRORS_AR.csv",
            "text/csv",
            use_container_width=True
        )

    # =====================================================
    # 🏁 الحالة النهائية
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
"""
    )
