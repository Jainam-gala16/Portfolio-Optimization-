import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

import time
from scipy.optimize import minimize

# =======================================================================
# THEME — "Gradient": a dark quant-dashboard palette.
# Ink (canvas) / Paper (cards) / Mint (gains) / Coral (losses) / Violet
# (interactive accent) / Fog (muted text). Space Grotesk for display
# numbers & headlines, Inter for UI, JetBrains Mono for tickers/data.
# =======================================================================
INK = "#0B0F1A"
PAPER = "#141B2E"
MINT = "#4CE0B3"
CORAL = "#FF6B6B"
VIOLET = "#8B7CF6"
FOG = "#8A93A6"
WHITE = "#EDEFF5"
COLORWAY = [MINT, VIOLET, CORAL, "#F5C065", "#5AC8FA", WHITE]

st.set_page_config(page_title="Gradient — Portfolio Optimizer", layout="wide", page_icon="◆")


def inject_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

    .stApp::before {{
        content: ""; position: fixed; top: 0; left: 0; right: 0; height: 4px;
        background: linear-gradient(90deg, {MINT}, {VIOLET}, {CORAL}); z-index: 9999;
    }}
    footer {{ visibility: hidden; }}

    /* Hero */
    .hero {{ padding: 10px 0 2px 0; }}
    .hero-eyebrow {{
        font-family: 'JetBrains Mono', monospace; letter-spacing: .15em;
        font-size: .72rem; color: {VIOLET}; margin-bottom: 8px; font-weight: 600;
    }}
    .hero-title {{
        font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 3rem;
        margin: 0; color: {WHITE}; letter-spacing: -0.02em; line-height: 1;
    }}
    .hero-title .accent {{ color: {MINT}; }}
    .hero-sub {{ color: {FOG}; font-size: 1rem; margin-top: 8px; max-width: 640px; }}

    /* Ticker marquee */
    .marquee-wrap {{
        overflow: hidden; white-space: nowrap;
        border-top: 1px solid rgba(255,255,255,0.08);
        border-bottom: 1px solid rgba(255,255,255,0.08);
        padding: 10px 0; margin: 18px 0 26px 0;
    }}
    .marquee-track {{ display: inline-block; animation: marquee 45s linear infinite; }}
    .marquee-track:hover {{ animation-play-state: paused; }}
    @keyframes marquee {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-50%); }} }}
    .marquee-item {{
        display: inline-flex; align-items: center; margin-right: 2.6rem;
        font-family: 'JetBrains Mono', monospace; font-size: .85rem;
    }}
    .marquee-ticker {{ color: {WHITE}; font-weight: 600; margin-right: 8px; }}
    .marquee-up {{ color: {MINT}; }}
    .marquee-down {{ color: {CORAL}; }}

    /* Section titles */
    .section-title {{
        font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.25rem;
        color: {WHITE}; margin: 4px 0 16px 0; padding-left: 12px; border-left: 4px solid {MINT};
    }}
    .section-caption {{ color: {FOG}; font-size: .88rem; margin-top: -10px; margin-bottom: 16px; }}

    /* Metric cards */
    .metric-card {{
        background: linear-gradient(160deg, {PAPER} 0%, #10141F 100%);
        border: 1px solid rgba(255,255,255,0.06); border-radius: 16px;
        padding: 16px 18px; box-shadow: 0 4px 20px rgba(0,0,0,0.25);
        transition: transform .15s ease, box-shadow .15s ease; margin-bottom: 12px;
    }}
    .metric-card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 28px rgba(0,0,0,0.35); }}
    .card-label {{
        font-family: 'JetBrains Mono', monospace; text-transform: uppercase;
        letter-spacing: .08em; font-size: .68rem; color: {FOG}; margin-bottom: 8px;
    }}
    .card-value {{ font-family: 'Space Grotesk', sans-serif; font-size: 1.6rem; font-weight: 700; color: {WHITE}; line-height: 1.1; }}
    .card-delta {{ font-family: 'JetBrains Mono', monospace; font-size: .8rem; margin-top: 6px; font-weight: 600; }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{ gap: 6px; border-bottom: none; }}
    .stTabs [data-baseweb="tab"] {{
        height: 42px; padding: 0 18px; background-color: rgba(255,255,255,0.03);
        border-radius: 999px; border: 1px solid rgba(255,255,255,0.07);
        color: {FOG}; font-family: 'Inter', sans-serif; font-weight: 500; font-size: .88rem;
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, {MINT} 0%, {VIOLET} 100%) !important;
        color: {INK} !important; font-weight: 700 !important; border: none !important;
    }}

    /* Buttons */
    .stButton>button {{
        border-radius: 999px; background: linear-gradient(135deg, {MINT}, {VIOLET});
        color: {INK}; font-weight: 700; border: none; padding: .6rem 1.4rem;
        transition: transform .15s ease, box-shadow .15s ease;
    }}
    .stButton>button:hover {{ transform: translateY(-1px); box-shadow: 0 6px 20px rgba(76,224,179,.25); }}

    [data-testid="stSidebar"] {{ border-right: 1px solid rgba(255,255,255,0.06); }}
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{ font-family: 'Space Grotesk', sans-serif; }}
    </style>
    """, unsafe_allow_html=True)


def themed(fig, height=None):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=WHITE, size=13),
        colorway=COLORWAY,
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor=PAPER, font_family="JetBrains Mono, monospace"),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.08)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.08)")
    if height:
        fig.update_layout(height=height)
    return fig


def section_title(text, accent=MINT, caption=None):
    st.markdown(f'<div class="section-title" style="border-left-color:{accent}">{text}</div>', unsafe_allow_html=True)
    if caption:
        st.markdown(f'<div class="section-caption">{caption}</div>', unsafe_allow_html=True)


def metric_card(label, value, delta=None, positive=True, icon=""):
    color = MINT if positive else CORAL
    arrow = "▲" if positive else "▼"
    delta_html = f'<div class="card-delta" style="color:{color}">{arrow} {delta}</div>' if delta else ""
    st.markdown(
        f'<div class="metric-card"><div class="card-label">{icon} {label}</div>'
        f'<div class="card-value">{value}</div>{delta_html}</div>',
        unsafe_allow_html=True,
    )


def render_marquee(tickers):
    items = []
    for t in tickers[:14]:
        try:
            q = load_ticker_quote(t)
            last = q.get("last_price")
            prev = q.get("previous_close")
            if last is None or prev in (None, 0):
                continue
            pct = (last - prev) / prev
            css_class = "marquee-up" if pct >= 0 else "marquee-down"
            arrow = "▲" if pct >= 0 else "▼"
            items.append(
                f'<span class="marquee-item"><span class="marquee-ticker">{t}</span>'
                f'<span>{last:,.2f}</span>&nbsp;'
                f'<span class="{css_class}">{arrow} {pct:+.2%}</span></span>'
            )
        except Exception:
            continue
    if not items:
        return
    track = "".join(items) * 2  # duplicated once so the 0%->-50% loop is seamless
    st.markdown(
        f'<div class="marquee-wrap"><div class="marquee-track">{track}</div></div>',
        unsafe_allow_html=True,
    )


# =======================================================================
# Optimizer functions — daily returns throughout; annualize at display time.
# =======================================================================
TRADING_DAYS = 252


def compute_mu_sigma(returns_df: pd.DataFrame):
    mu = returns_df.mean().values
    Sigma = returns_df.cov().values
    return mu, Sigma


def project(v, w_max):
    lo, hi = v.min() - 1.0, v.max()
    for _ in range(100):
        tau = 0.5 * (lo + hi)
        if np.clip(v - tau, 0.0, w_max).sum() > 1.0:
            lo = tau
        else:
            hi = tau
    return np.clip(v - 0.5 * (lo + hi), 0.0, w_max)


def utility_value(w, mu, Sigma, risk_aversion):
    return w @ mu - 0.5 * risk_aversion * (w @ Sigma @ w)


def utility_grad(w, mu, Sigma, risk_aversion):
    return mu - risk_aversion * (Sigma @ w)


def batch_gradient_ascent(mu, Sigma, risk_aversion=2.0, w_max=0.25,
                           learning_rate=20.0, iterations=10000, tol=1e-10):
    n = len(mu)
    w = np.ones(n) / n
    return_prog = np.zeros(iterations)
    variance_prog = np.zeros(iterations)
    utility_prog = np.zeros(iterations)
    start = time.perf_counter()
    total_iters = 0
    new_utility = -np.inf

    for i in range(iterations):
        total_iters += 1
        grad = mu - risk_aversion * (Sigma @ w)
        w_new = project(w + learning_rate * grad, w_max)
        step = np.linalg.norm(w_new - w)

        new_return = w_new @ mu
        new_variance = risk_aversion / 2 * (w_new @ Sigma @ w_new)
        new_utility = new_return - new_variance

        return_prog[i] = new_return
        variance_prog[i] = new_variance
        utility_prog[i] = new_utility

        w = w_new
        if abs(step) < tol:
            return_prog[i:] = new_return
            variance_prog[i:] = new_variance
            utility_prog[i:] = new_utility
            break

    w = np.maximum(w, 0)
    w = w / w.sum()

    return {
        "weights": w,
        "return_prog": return_prog[:total_iters],
        "variance_prog": variance_prog[:total_iters],
        "utility_prog": utility_prog[:total_iters],
        "iterations_run": total_iters,
        "runtime_seconds": time.perf_counter() - start,
        "final_utility": new_utility,
    }


def minibatch_gradient_descent(returns, risk_aversion=5.0, w_max=0.25,
                                learning_rate=10.0, batch_size=40,
                                iterations=10000, tol=1e-9, seed=None):
    start = time.perf_counter()
    rng = np.random.default_rng(seed)
    T, n_assets = returns.shape
    w = np.full(n_assets, 1.0 / n_assets)
    utility_history = np.zeros(iterations)
    full_mu, full_Sigma = compute_mu_sigma(pd.DataFrame(returns))

    last_i = iterations - 1
    for i in range(iterations):
        idx = rng.integers(0, T, size=min(batch_size, T))
        batch = returns[idx]
        mu_b, Sigma_b = batch.mean(axis=0), np.cov(batch, rowvar=False)

        grad = utility_grad(w, mu_b, Sigma_b, risk_aversion)
        w_new = project(w + learning_rate * grad, w_max)
        step = np.linalg.norm(w_new - w)
        w = w_new

        utility_history[i] = utility_value(w, full_mu, full_Sigma, risk_aversion)
        if step < tol:
            utility_history[i:] = utility_history[i]
            last_i = i
            break

    return {
        "weights": w,
        "utility_history": utility_history,
        "final_utility": utility_history[last_i],
        "iterations_run": last_i + 1,
        "runtime_seconds": time.perf_counter() - start,
    }


def sharpe_ratio(w, mu, Sigma, rf_daily):
    return (mu @ w - rf_daily) / np.sqrt(w @ Sigma @ w)


def sharpe_grad(w, mu, Sigma, rf_daily):
    Sw = Sigma @ w
    sig = np.sqrt(w @ Sw)
    return mu / sig - (mu @ w - rf_daily) * Sw / sig ** 3


def sharpe_gradient_ascent(mu, Sigma, rf_daily, w_max=0.25,
                            learning_rate=0.05, iterations=10000, tol=1e-10):
    start = time.perf_counter()
    n = len(mu)
    w = np.full(n, 1.0 / n)
    history = [sharpe_ratio(w, mu, Sigma, rf_daily)]

    total_iters = 0
    for _ in range(iterations):
        total_iters += 1
        w_new = project(w + learning_rate * sharpe_grad(w, mu, Sigma, rf_daily), w_max)
        step = np.linalg.norm(w_new - w)
        w = w_new
        history.append(sharpe_ratio(w, mu, Sigma, rf_daily))
        if step < tol:
            break

    return {
        "weights": w,
        "history": np.array(history),
        "iterations_run": total_iters,
        "runtime_seconds": time.perf_counter() - start,
    }


def slsqp_mvo(mu, Sigma, risk_aversion=2.0, w_max=0.25):
    start = time.perf_counter()
    n = len(mu)

    def neg_utility(w):
        return -(w @ mu) + 0.5 * risk_aversion * (w @ Sigma @ w)

    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
    bounds = [(0, w_max)] * n
    w0 = np.ones(n) / n
    res = minimize(neg_utility, w0, method="SLSQP", bounds=bounds, constraints=constraints)
    return {"weights": res.x, "runtime_seconds": time.perf_counter() - start}


def slsqp_sharpe(mu, Sigma, rf_daily, w_max=0.25):
    start = time.perf_counter()
    n = len(mu)
    w0 = np.full(n, 1.0 / n)
    res = minimize(
        lambda w: -sharpe_ratio(w, mu, Sigma, rf_daily),
        w0, method="SLSQP",
        jac=lambda w: -sharpe_grad(w, mu, Sigma, rf_daily),
        bounds=[(0, w_max)] * n,
        constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}],
    )
    return {"weights": res.x, "runtime_seconds": time.perf_counter() - start}


def risk_report(weights, returns_df, rf_annual, label=""):
    port = returns_df.values @ weights
    ann_ret = port.mean() * TRADING_DAYS
    ann_vol = port.std(ddof=1) * np.sqrt(TRADING_DAYS)
    var95 = -np.percentile(port, 5)
    cvar95 = -port[port <= np.percentile(port, 5)].mean()
    cum = np.cumprod(1 + port)
    max_dd = (1 - cum / np.maximum.accumulate(cum)).max()
    sharpe = (ann_ret - rf_annual) / ann_vol if ann_vol > 0 else np.nan
    return pd.Series({
        "Annualized Return": ann_ret,
        "Annualized Volatility": ann_vol,
        "Sharpe (realized)": sharpe,
        "VaR 95% (daily)": var95,
        "CVaR 95% (daily)": cvar95,
        "Max Drawdown": max_dd,
    }, name=label)


def random_portfolios(mu, Sigma, rf_daily, w_max, n_assets, m=8000, seed=0):
    rng = np.random.default_rng(seed)
    W = rng.dirichlet(np.ones(n_assets), size=m)
    W = W[(W <= w_max).all(axis=1)]
    rets = W @ mu
    vols = np.sqrt(np.einsum("ij,jk,ik->i", W, Sigma, W))
    sharpes = (rets - rf_daily) / vols
    return rets, vols, sharpes


# =======================================================================
# App
# =======================================================================
inject_css()

DEFAULT_TICKERS = ["AAPL", "MSFT", "NVDA", "JNJ", "UNH", "JPM",
                    "V", "PG", "KO", "MCD", "XOM", "CAT"]

st.sidebar.markdown("### 🎯 Universe")
tickers_input = st.sidebar.text_input(
    "Tickers (comma-separated, 8+ recommended)",
    value=", ".join(DEFAULT_TICKERS),
)
years = st.sidebar.slider("Years of history", 1, 10, 5)

st.sidebar.markdown("### ⚙️ Objective")
w_max = st.sidebar.slider("Max weight per stock", 0.05, 1.0, 0.25, 0.05)
rf_annual = st.sidebar.number_input("Risk-free rate (annual)", value=0.04, step=0.005, format="%.3f")
risk_aversion = st.sidebar.slider("Risk aversion (λ)", 0.5, 10.0, 2.0, 0.5)

with st.sidebar.expander("🧪 Advanced: gradient descent settings"):
    batch_lr = st.number_input("Full-batch learning rate", value=20.0)
    batch_iters = st.number_input("Full-batch iterations", value=10000, step=1000)
    mb_lr = st.number_input("Mini-batch learning rate", value=10.0)
    mb_batch_size = st.number_input("Mini-batch size (days)", value=40, step=10)
    mb_iters = st.number_input("Mini-batch iterations", value=10000, step=1000)
    sharpe_lr = st.number_input("Sharpe-ascent learning rate", value=0.05, format="%.3f")
    sharpe_iters = st.number_input("Sharpe-ascent iterations", value=10000, step=1000)
    tol = st.number_input("Convergence tolerance", value=1e-9, format="%.1e")

run_button = st.sidebar.button("Run optimization", type="primary")

st.markdown(
    '<div class="hero">'
    '<div class="hero-eyebrow">GRADIENT DESCENT · MEAN-VARIANCE · SHARPE RATIO</div>'
    '<h1 class="hero-title">Gradient<span class="accent">.</span></h1>'
    '<p class="hero-sub">Pick your stocks, then watch four optimizers — full-batch, '
    'mini-batch, Sharpe ascent, and SLSQP — fight it out for the best weights.</p>'
    '</div>',
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def load_prices(tickers, years):
    raw = yf.download(tickers, period=f"{years}y", auto_adjust=True, progress=False)
    prices = raw["Close"].dropna(how="any")
    return prices


def parse_tickers(raw_text):
    seen, out = set(), []
    for t in raw_text.split(","):
        t = t.strip().upper()
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


EXPLORER_RANGES = {
    "1D": ("1d", "5m"), "5D": ("5d", "15m"), "1M": ("1mo", "1d"),
    "6M": ("6mo", "1d"), "YTD": ("ytd", "1d"), "1Y": ("1y", "1d"),
    "5Y": ("5y", "1wk"), "Max": ("max", "1mo"),
}


@st.cache_data(ttl=60, show_spinner=False)
def load_ticker_history(ticker, period, interval):
    return yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=True)


@st.cache_data(ttl=60, show_spinner=False)
def load_ticker_quote(ticker):
    fi = yf.Ticker(ticker).fast_info

    def get(key):
        try:
            return fi[key]
        except Exception:
            return getattr(fi, key, None)

    return {
        "last_price": get("lastPrice"),
        "previous_close": get("previousClose") or get("regularMarketPreviousClose"),
        "day_high": get("dayHigh"), "day_low": get("dayLow"),
        "year_high": get("yearHigh"), "year_low": get("yearLow"),
        "volume": get("lastVolume"), "market_cap": get("marketCap"),
        "currency": get("currency") or "USD",
    }


def weights_bar(weights, tickers, title):
    s = pd.Series(weights, index=tickers).sort_values(ascending=False)
    fig = px.bar(s, title=title, labels={"index": "Ticker", "value": "Weight"},
                 color=s.values, color_continuous_scale=[[0, FOG], [1, MINT]])
    fig.update_layout(showlegend=False, coloraxis_showscale=False)
    return themed(fig), s


render_marquee(parse_tickers(tickers_input) or DEFAULT_TICKERS)

# ---------------------------------------------------------------------
# Run pipeline -> stash everything in session_state
# ---------------------------------------------------------------------
if run_button:
    tickers = parse_tickers(tickers_input)
    if len(tickers) < 2:
        st.error("Enter at least 2 tickers.")
        st.stop()

    with st.spinner(f"Downloading {years}y of price history for {len(tickers)} tickers..."):
        prices = load_prices(tickers, years)

    if prices.empty or prices.shape[1] < 2:
        st.error("Couldn't get usable price data for those tickers. Check the symbols and try again.")
        st.stop()

    valid_tickers = list(prices.columns)
    if len(valid_tickers) < len(tickers):
        st.warning(f"Dropped tickers with missing data: {set(tickers) - set(valid_tickers)}")

    split = int(len(prices) * 0.8)
    prices_train, prices_test = prices.iloc[:split], prices.iloc[split:]
    returns_train = prices_train.pct_change().dropna()
    returns_test = prices_test.pct_change().dropna()

    mu, Sigma = compute_mu_sigma(returns_train)
    rf_daily = rf_annual / TRADING_DAYS
    n = len(valid_tickers)

    with st.spinner("Running full-batch gradient ascent..."):
        batch_out = batch_gradient_ascent(
            mu, Sigma, risk_aversion=risk_aversion, w_max=w_max,
            learning_rate=batch_lr, iterations=int(batch_iters), tol=tol,
        )
    with st.spinner("Running mini-batch gradient ascent..."):
        mb_out = minibatch_gradient_descent(
            returns_train.to_numpy(), risk_aversion=risk_aversion, w_max=w_max,
            learning_rate=mb_lr, batch_size=int(mb_batch_size),
            iterations=int(mb_iters), tol=tol, seed=1,
        )
    with st.spinner("Running Sharpe-ratio gradient ascent..."):
        sharpe_out = sharpe_gradient_ascent(
            mu, Sigma, rf_daily, w_max=w_max,
            learning_rate=sharpe_lr, iterations=int(sharpe_iters), tol=tol,
        )
    with st.spinner("Running SLSQP benchmarks..."):
        slsqp_mvo_out = slsqp_mvo(mu, Sigma, risk_aversion=risk_aversion, w_max=w_max)
        slsqp_sharpe_out = slsqp_sharpe(mu, Sigma, rf_daily, w_max=w_max)

    st.session_state["results"] = dict(
        tickers=valid_tickers, n=n, prices=prices,
        returns_train=returns_train, returns_test=returns_test,
        mu=mu, Sigma=Sigma, rf_daily=rf_daily, rf_annual=rf_annual,
        risk_aversion=risk_aversion, w_max=w_max,
        batch_out=batch_out, mb_out=mb_out, sharpe_out=sharpe_out,
        slsqp_mvo_out=slsqp_mvo_out, slsqp_sharpe_out=slsqp_sharpe_out,
    )

# ---------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------
has_results = "results" in st.session_state
if has_results:
    R = st.session_state["results"]
    tickers, n = R["tickers"], R["n"]

tab_explorer, tab_data, tab_batch, tab_mb, tab_sharpe, tab_slsqp, tab_backtest = st.tabs(
    ["📊 Explorer", "🗂 Data", "🟢 Full-Batch", "🟡 Mini-Batch",
     "🔵 Sharpe", "⚖️ SLSQP", "📈 Backtest"]
)

# --- Stock Explorer tab: works standalone, no need to run the optimizer ---
with tab_explorer:
    section_title("Stock Explorer", VIOLET,
                   "Quotes and charts come from Yahoo Finance and are typically delayed "
                   "~15–20 minutes — not a true real-time streaming feed.")

    explorer_tickers = parse_tickers(tickers_input) or DEFAULT_TICKERS
    ec1, ec2, ec3 = st.columns([2, 2, 1])
    picked = ec1.selectbox("Stock", explorer_tickers, key="explorer_ticker")
    custom_ticker = ec2.text_input("...or look up any other ticker", value="", key="explorer_custom")
    if custom_ticker.strip():
        picked = custom_ticker.strip().upper()
    range_choice = ec3.selectbox("Range", list(EXPLORER_RANGES.keys()), index=3, key="explorer_range")
    period, interval = EXPLORER_RANGES[range_choice]

    with st.spinner(f"Loading {picked}..."):
        hist = load_ticker_history(picked, period, interval)
        quote = load_ticker_quote(picked)

    if hist.empty:
        st.warning(f"No chart data found for '{picked}'. Check the ticker symbol.")
    else:
        last_price = quote.get("last_price") or hist["Close"].iloc[-1]
        prev_close = quote.get("previous_close") or hist["Close"].iloc[0]
        change = (last_price - prev_close) if prev_close else None
        pct_change = (change / prev_close) if (change is not None and prev_close) else None
        currency = quote.get("currency", "USD")

        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            metric_card(f"{picked} price", f"{last_price:,.2f} {currency}",
                        f"{pct_change:+.2%}" if pct_change is not None else None,
                        positive=(pct_change or 0) >= 0)
        with m2:
            dl, dh = quote.get("day_low"), quote.get("day_high")
            metric_card("Day range", f"{dl:,.2f} – {dh:,.2f}" if dl and dh else "—")
        with m3:
            yl, yh = quote.get("year_low"), quote.get("year_high")
            metric_card("52-week range", f"{yl:,.2f} – {yh:,.2f}" if yl and yh else "—")
        with m4:
            vol = quote.get("volume")
            metric_card("Volume", f"{vol:,.0f}" if vol else "—")
        with m5:
            mcap = quote.get("market_cap")
            metric_card("Market cap", f"{mcap / 1e9:,.1f}B" if mcap else "—")

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                             row_heights=[0.75, 0.25], vertical_spacing=0.03)
        fig.add_trace(go.Candlestick(
            x=hist.index, open=hist["Open"], high=hist["High"], low=hist["Low"], close=hist["Close"],
            name=picked, increasing_line_color=MINT, decreasing_line_color=CORAL,
            increasing_fillcolor=MINT, decreasing_fillcolor=CORAL,
        ), row=1, col=1)
        fig.add_trace(go.Bar(x=hist.index, y=hist["Volume"], name="Volume",
                              marker_color="rgba(139,124,246,0.35)"), row=2, col=1)
        fig.update_layout(title=f"{picked} — {range_choice}", xaxis_rangeslider_visible=False, showlegend=False)
        st.plotly_chart(themed(fig, height=550), use_container_width=True)

        with st.expander("Recent data"):
            st.dataframe(hist.tail(30).sort_index(ascending=False), use_container_width=True)

if not has_results:
    st.info("Set your tickers and settings in the sidebar, then click **Run optimization** "
            "to unlock the Data, GD, SLSQP, and Backtest tabs.")
else:
    with tab_data:
        section_title("Price history & stock stats", VIOLET)
        norm = R["prices"] / R["prices"].iloc[0]
        fig = px.line(norm, title="Normalized price (training + test period)",
                       color_discrete_sequence=COLORWAY)
        st.plotly_chart(themed(fig), use_container_width=True)

        stats = pd.DataFrame({
            "Annualized Return": R["mu"] * TRADING_DAYS,
            "Annualized Volatility": np.sqrt(np.diag(R["Sigma"])) * np.sqrt(TRADING_DAYS),
        }, index=tickers)
        st.dataframe(stats.style.format("{:.2%}"), use_container_width=True)

        corr = R["returns_train"].corr()
        fig_corr = px.imshow(corr, color_continuous_scale=[[0, CORAL], [0.5, PAPER], [1, MINT]],
                              zmin=-1, zmax=1, title="Correlation matrix (training period)")
        st.plotly_chart(themed(fig_corr), use_container_width=True)

    with tab_batch:
        out = R["batch_out"]
        section_title("Full-batch projected gradient ascent", MINT)
        c1, c2, c3, c4 = st.columns(4)
        with c1: metric_card("Iterations to converge", out["iterations_run"], icon="🔁")
        with c2: metric_card("Runtime (s)", f"{out['runtime_seconds']:.3f}", icon="⏱")
        with c3: metric_card("Final utility", f"{out['final_utility']:.6f}", icon="Σ")
        with c4:
            ann_ret = out["weights"] @ R["mu"] * TRADING_DAYS
            metric_card("Ann. return", f"{ann_ret:.2%}", positive=ann_ret >= 0, icon="📈")

        fig_conv = go.Figure(go.Scatter(y=out["utility_prog"], name="Utility", line=dict(color=MINT, width=2.5)))
        fig_conv.update_layout(title="Convergence", xaxis_title="Iteration", yaxis_title="Utility")
        st.plotly_chart(themed(fig_conv), use_container_width=True)

        fig_w, s_batch = weights_bar(out["weights"], tickers, "Suggested weights — Full-batch GD")
        st.plotly_chart(fig_w, use_container_width=True)

    with tab_mb:
        out = R["mb_out"]
        section_title("Mini-batch projected gradient ascent", "#F5C065",
                       f"Each iteration resamples a random {int(mb_batch_size)}-day subset to estimate "
                       "μ/Σ, so the utility path is noisier than full-batch.")
        c1, c2, c3 = st.columns(3)
        with c1: metric_card("Iterations to converge", out["iterations_run"], icon="🔁")
        with c2: metric_card("Runtime (s)", f"{out['runtime_seconds']:.3f}", icon="⏱")
        with c3: metric_card("Final utility", f"{out['final_utility']:.6f}", icon="Σ")

        fig_conv = go.Figure(go.Scatter(y=out["utility_history"], name="Utility", line=dict(color="#F5C065", width=1.5)))
        fig_conv.update_layout(title="Convergence (noisy)", xaxis_title="Iteration", yaxis_title="Utility")
        st.plotly_chart(themed(fig_conv), use_container_width=True)

        fig_w, s_mb = weights_bar(out["weights"], tickers, "Suggested weights — Mini-batch GD")
        st.plotly_chart(fig_w, use_container_width=True)

    with tab_sharpe:
        out = R["sharpe_out"]
        section_title("Sharpe-ratio projected gradient ascent", VIOLET)
        c1, c2, c3 = st.columns(3)
        with c1: metric_card("Iterations to converge", out["iterations_run"], icon="🔁")
        with c2: metric_card("Runtime (s)", f"{out['runtime_seconds']:.3f}", icon="⏱")
        with c3: metric_card("Sharpe ratio", f"{out['history'][-1]:.3f}", icon="⚡")

        fig_conv = go.Figure(go.Scatter(y=out["history"], name="Sharpe", line=dict(color=VIOLET, width=2.5)))
        fig_conv.update_layout(title="Convergence", xaxis_title="Iteration", yaxis_title="Sharpe ratio")
        st.plotly_chart(themed(fig_conv), use_container_width=True)

        fig_w, s_sharpe = weights_bar(out["weights"], tickers, "Suggested weights — Sharpe-ratio GD")
        st.plotly_chart(fig_w, use_container_width=True)

        rets, vols, sharpes = random_portfolios(R["mu"], R["Sigma"], R["rf_daily"], R["w_max"], n)
        sig_opt = np.sqrt(out["weights"] @ R["Sigma"] @ out["weights"])
        ret_opt = R["mu"] @ out["weights"]
        fig_scatter = go.Figure()
        fig_scatter.add_trace(go.Scatter(
            x=vols * np.sqrt(TRADING_DAYS), y=rets * TRADING_DAYS, mode="markers",
            marker=dict(size=4, color=sharpes, colorscale=[[0, FOG], [1, MINT]],
                        showscale=True, colorbar=dict(title="Sharpe")),
            name="Random portfolios",
        ))
        fig_scatter.add_trace(go.Scatter(
            x=[sig_opt * np.sqrt(TRADING_DAYS)], y=[ret_opt * TRADING_DAYS], mode="markers",
            marker=dict(size=16, color=CORAL, symbol="star"), name="Optimum",
        ))
        fig_scatter.update_layout(title="Risk/return of random admissible portfolios",
                                   xaxis_title="Annualized volatility", yaxis_title="Annualized return")
        st.plotly_chart(themed(fig_scatter), use_container_width=True)

    with tab_slsqp:
        section_title("SLSQP (scipy) benchmark vs. gradient-based methods", VIOLET)
        comp = pd.DataFrame({
            "Full-batch GD": R["batch_out"]["weights"],
            "Mini-batch GD": R["mb_out"]["weights"],
            "SLSQP (MVO)": R["slsqp_mvo_out"]["weights"],
        }, index=tickers)
        fig = px.bar(comp, barmode="group", title="Weights: gradient methods vs SLSQP",
                     color_discrete_sequence=COLORWAY)
        st.plotly_chart(themed(fig), use_container_width=True)

        runtime_tbl = pd.DataFrame({
            "Runtime (s)": [
                R["batch_out"]["runtime_seconds"], R["mb_out"]["runtime_seconds"],
                R["slsqp_mvo_out"]["runtime_seconds"],
            ],
            "Max weight diff vs SLSQP": [
                np.abs(R["batch_out"]["weights"] - R["slsqp_mvo_out"]["weights"]).max(),
                np.abs(R["mb_out"]["weights"] - R["slsqp_mvo_out"]["weights"]).max(),
                0.0,
            ],
        }, index=["Full-batch GD", "Mini-batch GD", "SLSQP (MVO)"])
        st.dataframe(runtime_tbl, use_container_width=True)

        st.markdown("**Sharpe-objective comparison**")
        comp_sharpe = pd.DataFrame({
            "Sharpe-ratio GD": R["sharpe_out"]["weights"],
            "SLSQP (Sharpe)": R["slsqp_sharpe_out"]["weights"],
        }, index=tickers)
        st.plotly_chart(themed(px.bar(comp_sharpe, barmode="group", title="Weights: Sharpe GD vs SLSQP",
                                       color_discrete_sequence=COLORWAY)),
                         use_container_width=True)

    with tab_backtest:
        section_title("Out-of-sample backtest (test period)", MINT)
        w_eq = np.full(n, 1.0 / n)
        methods = {
            "Full-batch GD": R["batch_out"]["weights"],
            "Mini-batch GD": R["mb_out"]["weights"],
            "Sharpe-ratio GD": R["sharpe_out"]["weights"],
            "SLSQP (MVO)": R["slsqp_mvo_out"]["weights"],
            "Equal-weight": w_eq,
        }

        reports = [risk_report(w, R["returns_test"], R["rf_annual"], label=name)
                   for name, w in methods.items()]
        st.dataframe(pd.concat(reports, axis=1).style.format("{:.4f}"), use_container_width=True)

        fig_wealth = go.Figure()
        for name, w in methods.items():
            cum = (1 + R["returns_test"].values @ w).cumprod()
            fig_wealth.add_trace(go.Scatter(y=cum, name=name))
        fig_wealth.update_layout(title="Cumulative value of $1 invested (test period)",
                                  xaxis_title="Trading day", yaxis_title="Portfolio value")
        st.plotly_chart(themed(fig_wealth), use_container_width=True)