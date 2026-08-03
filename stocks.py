import time
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from scipy.optimize import minimize
from matplotlib.colors import LinearSegmentedColormap

# =======================================================================
# THEME — SOFT LIGHT CHARCOAL PALETTE (Comfortable, not harsh white)
# =======================================================================
BG = "#E8ECEF"            # Soft light grey background (not harsh white)
PANEL = "#F4F6F9"         # Clean, very light panel background
PANEL_ALT = "#FFFFFF"     # Pure white for inputs/hover contrasts
BORDER = "rgba(0,0,0,0.10)" # Subtle, elegant dark border
TEXT = "#1E2229"          # Deep slate grey (almost black) text for high contrast
MUTED = "#5A626C"         # Soft grey for secondary text
GREEN = "#0D9488"         # Teal/Dark green (pops nicely against light grey)
GREEN_DIM = "#CCFBF1"     # Very light teal gradient endpoint
RED = "#DC2626"           # Professional Red
GOLD = "#D97706"
BLUE = "#2563EB"
COLORWAY = [GREEN, BLUE, RED, GOLD]

# CHANGED TITLE TO ALPHA TRADING
st.set_page_config(page_title="Alpha Trading — Portfolio Terminal", layout="wide", page_icon="📈")


def inject_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; color: {TEXT}; }}
    .stApp {{ background-color: {BG}; }}
    footer {{ visibility: hidden; }}
    section[data-testid="stSidebar"] {{ display: none; }}

    /* Make sure Streamlit's own text stays legible */
    p, span, label, .stMarkdown, .stCaption {{ color: {TEXT}; }}
    .stCaption, small {{ color: {MUTED} !important; }}

    /* Top toolbar */
    .toolbar {{
        position: relative; left: 50%; right: 50%;
        margin-left: -50vw; margin-right: -50vw; width: 100vw;
        background: {PANEL_ALT}; border-bottom: 1px solid {BORDER};
        padding: 14px 3vw; margin-bottom: 22px;
        display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;
    }}
    .toolbar-brand {{ font-family:'Space Grotesk',sans-serif; font-weight:700; color:{TEXT}; font-size:1.05rem; letter-spacing:-0.01em; display:flex; align-items:center; gap:9px; white-space:nowrap;}}
    .toolbar-tabs {{ display:flex; gap:24px; flex-wrap: wrap; }}
    .toolbar-tab {{ font-family:'JetBrains Mono',monospace; font-size:.72rem; color:{MUTED}; text-transform:uppercase; letter-spacing:.06em; padding-bottom:4px; }}
    .toolbar-tab.active {{ color:{TEXT}; border-bottom:2px solid {GREEN}; }}
    .toolbar-note {{ font-family:'JetBrains Mono',monospace; font-size:.68rem; color:{MUTED}; }}

    /* Ticker marquee */
    .marquee-wrap {{ overflow:hidden; white-space:nowrap; border-bottom:1px solid {BORDER}; padding:8px 0; margin:0 0 22px 0;}}
    .marquee-track {{ display:inline-block; animation: marquee 45s linear infinite; }}
    .marquee-track:hover {{ animation-play-state: paused; }}
    @keyframes marquee {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-50%); }} }}
    .marquee-item {{ display:inline-flex; align-items:center; margin-right:2.4rem; font-family:'JetBrains Mono',monospace; font-size:.82rem;}}
    .marquee-ticker {{ color:{TEXT}; font-weight:600; margin-right:8px;}}
    .marquee-up {{ color:{GREEN}; }}
    .marquee-down {{ color:{RED}; }}

    /* Panel chrome */
    .panel-header {{ display:flex; align-items:center; justify-content:space-between; padding-bottom:10px; margin-bottom:12px; border-bottom:1px solid {BORDER}; }}
    .panel-title {{ font-family:'Inter',sans-serif; font-weight:600; font-size:.78rem; color:{TEXT}; text-transform:uppercase; letter-spacing:.05em; display:flex; align-items:center; gap:8px;}}
    .panel-pill {{ font-family:'JetBrains Mono',monospace; font-size:.62rem; font-weight:700; background:rgba(13,148,136,0.12); color:{GREEN}; border:1px solid rgba(13,148,136,0.32); border-radius:999px; padding:2px 9px; text-transform:uppercase; }}
    .panel-pill.muted {{ background:rgba(0,0,0,0.05); color:{MUTED}; border-color:{BORDER}; }}

    .st-key-panel_setup, .st-key-panel_chart, .st-key-panel_ticks,
    .st-key-panel_chain, .st-key-panel_backtest, .st-key-panel_toppick {{
        background: {PANEL}; border: 1px solid {BORDER}; border-radius: 12px;
        padding: 16px 18px 18px 18px; margin-bottom: 20px;
    }}

    /* Ticker chip buttons */
    .st-key-chip_zone .stButton>button {{
        background: {PANEL_ALT} !important; color:{TEXT} !important;
        border: 1px solid {BORDER} !important; border-radius: 999px !important;
        font-family:'JetBrains Mono',monospace !important; font-size:.72rem !important;
        font-weight:600 !important; padding: 4px 6px !important; box-shadow:none !important;
    }}
    .st-key-chip_zone .stButton>button:hover {{ border-color:{RED} !important; color:{RED} !important; }}

    /* Primary CTA */
    .stButton>button {{
        border-radius: 999px; background: {GREEN};
        color: #FFFFFF; font-weight:700; border:none; padding:.6rem 1.4rem;
        transition: transform .15s ease, box-shadow .15s ease;
    }}
    .stButton>button:hover {{ transform: translateY(-1px); box-shadow: 0 6px 18px rgba(13,148,136,.28); background:#0F766E; }}

    /* Top pick banner */
    .toppick-label {{ font-family:'JetBrains Mono',monospace; letter-spacing:.06em; font-size:.7rem; color:{GREEN}; margin-bottom:8px; font-weight:700; text-transform:uppercase;}}
    .toppick-ticker {{ font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:2rem; color:{TEXT};}}
    .toppick-weight {{ font-family:'JetBrains Mono',monospace; font-size:1rem; color:{GREEN}; margin-left:10px; font-weight:700;}}
    .toppick-runners {{ margin-top:8px; }}
    </style>
    """, unsafe_allow_html=True)


def themed(fig, height=None):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=TEXT, size=13),
        colorway=COLORWAY, margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor=PANEL_ALT, font_family="JetBrains Mono, monospace", font_color=TEXT),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.07)", zerolinecolor="rgba(0,0,0,0.12)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.07)", zerolinecolor="rgba(0,0,0,0.12)")
    if height:
        fig.update_layout(height=height)
    return fig


def panel_header(title, badge=None, muted_badge=False):
    cls = "panel-pill muted" if muted_badge else "panel-pill"
    badge_html = f'<span class="{cls}">{badge}</span>' if badge else ""
    st.markdown(f'<div class="panel-header"><div class="panel-title">{title}</div>{badge_html}</div>',
                unsafe_allow_html=True)


def render_marquee(tickers):
    items = []
    for t in tickers[:14]:
        try:
            q = load_ticker_quote(t)
            last, prev = q.get("last_price"), q.get("previous_close")
            if last is None or not prev:
                continue
            pct = (last - prev) / prev
            css_class = "marquee-up" if pct >= 0 else "marquee-down"
            arrow = "▲" if pct >= 0 else "▼"
            items.append(
                f'<span class="marquee-item"><span class="marquee-ticker">{t}</span>'
                f'<span>{last:,.2f}</span>&nbsp;<span class="{css_class}">{arrow} {pct:+.2%}</span></span>'
            )
        except Exception:
            continue
    if not items:
        return
    track = "".join(items) * 2
    st.markdown(f'<div class="marquee-wrap"><div class="marquee-track">{track}</div></div>', unsafe_allow_html=True)


def dark_safe_gradient_table(df_pct, index_label="Ticker"):
    """pandas Styler heatmap for the soft-light theme"""
    cmap = LinearSegmentedColormap.from_list("panel_light", ["#FFFFFF", "#CCFBF1", "#0D9488"])
    styler = (
        df_pct.style
        .background_gradient(cmap=cmap, axis=0)
        .set_properties(**{"color": "#111827", "font-family": "JetBrains Mono, monospace", "font-size": "0.82rem"})
        .format("{:.1%}")
    )
    return styler


# =======================================================================
# Optimizer functions — daily returns throughout; annualize at display time.
# =======================================================================
TRADING_DAYS = 252


def compute_mu_sigma(returns_df: pd.DataFrame):
    return returns_df.mean().values, returns_df.cov().values


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
        "weights": w, "return_prog": return_prog[:total_iters],
        "variance_prog": variance_prog[:total_iters], "utility_prog": utility_prog[:total_iters],
        "iterations_run": total_iters, "runtime_seconds": time.perf_counter() - start,
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
        "weights": w, "utility_history": utility_history,
        "final_utility": utility_history[last_i], "iterations_run": last_i + 1,
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
    return {"weights": w, "history": np.array(history), "iterations_run": total_iters,
            "runtime_seconds": time.perf_counter() - start}


def slsqp_mvo(mu, Sigma, risk_aversion=2.0, w_max=0.25):
    start = time.perf_counter()
    n = len(mu)

    def neg_utility(w):
        return -(w @ mu) + 0.5 * risk_aversion * (w @ Sigma @ w)

    def neg_utility_grad(w):
        return -mu + risk_aversion * (Sigma @ w)

    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
    bounds = [(0, w_max)] * n
    w0 = np.ones(n) / n
    res = minimize(neg_utility, w0, jac=neg_utility_grad, method="SLSQP",
                   bounds=bounds, constraints=constraints,
                   options={"maxiter": 1000, "ftol": 1e-12})
    return {"weights": res.x, "runtime_seconds": time.perf_counter() - start}


def slsqp_sharpe(mu, Sigma, rf_daily, w_max=0.25):
    start = time.perf_counter()
    n = len(mu)
    w0 = np.full(n, 1.0 / n)
    res = minimize(
        lambda w: -sharpe_ratio(w, mu, Sigma, rf_daily), w0, method="SLSQP",
        jac=lambda w: -sharpe_grad(w, mu, Sigma, rf_daily),
        bounds=[(0, w_max)] * n,
        constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}],
        options={"maxiter": 1000, "ftol": 1e-12},
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
        "Annualized Return": ann_ret, "Annualized Volatility": ann_vol,
        "Sharpe (realized)": sharpe, "VaR 95% (daily)": var95,
        "CVaR 95% (daily)": cvar95, "Max Drawdown": max_dd,
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
# Data loading (cached)
# =======================================================================
@st.cache_data(ttl=3600, show_spinner=False)
def load_prices(tickers, years):
    raw = yf.download(tickers, period=f"{years}y", auto_adjust=True, progress=False)
    return raw["Close"].dropna(how="any")


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


# =======================================================================
# App
# =======================================================================
inject_css()

DEFAULT_TICKERS = ["AAPL", "MSFT", "NVDA", "JNJ", "UNH", "JPM",
                    "V", "PG", "KO", "MCD", "XOM", "CAT"]
if "tickers" not in st.session_state:
    st.session_state.tickers = DEFAULT_TICKERS.copy()

RISK_LEVELS = {"Cautious": 6.0, "Balanced": 2.5, "Bold": 1.2, "Aggressive": 0.5}
RANGE_OPTS = {"1M": ("1mo", "1d"), "6M": ("6mo", "1d"), "1Y": ("1y", "1d"), "5Y": ("5y", "1wk")}


def _remove_ticker(t):
    st.session_state.tickers = [x for x in st.session_state.tickers if x != t]


has_results_now = "results" in st.session_state
st.markdown(f"""
<div class="toolbar">
  <div class="toolbar-brand">◆ ALPHA TRADING</div>
  <div class="toolbar-tabs">
    <span class="toolbar-tab active">Setup</span>
    <span class="toolbar-tab">Chart</span>
    <span class="toolbar-tab">Ticks</span>
    <span class="toolbar-tab">Chain</span>
    <span class="toolbar-tab">Backtest</span>
  </div>
  <div class="toolbar-note">{len(st.session_state.tickers)} tickers · yfinance, delayed ~15–20min · {'results ready' if has_results_now else 'not yet run'}</div>
</div>
""", unsafe_allow_html=True)

render_marquee(st.session_state.tickers)

# --------------------------- ROW 1: Setup | Chart ---------------------------
row1_left, row1_right = st.columns(2, gap="large")

with row1_left:
    with st.container(key="panel_setup"):
        panel_header("Setup", "Ready" if not has_results_now else "Ran")

        st.markdown('<div class="panel-title" style="margin-bottom:6px;">Holdings</div>', unsafe_allow_html=True)
        with st.container(key="chip_zone"):
            tickers_now = st.session_state.tickers
            for row_start in range(0, len(tickers_now), 4):
                row = tickers_now[row_start:row_start + 4]
                cols = st.columns(len(row))
                for c, t in zip(cols, row):
                    with c:
                        st.button(f"{t}  ✕", key=f"chip_{t}", on_click=_remove_ticker, args=(t,),
                                   use_container_width=True)

        with st.form("add_ticker_form", clear_on_submit=True):
            fc1, fc2 = st.columns([3, 1])
            new_t = fc1.text_input("add", label_visibility="collapsed", placeholder="Add a ticker, e.g. TSLA")
            added = fc2.form_submit_button("＋ Add")
            if added and new_t.strip():
                nt = new_t.strip().upper()
                if nt not in st.session_state.tickers:
                    st.session_state.tickers.append(nt)

        sc1, sc2 = st.columns(2)
        with sc1:
            st.caption("Time window (years)")
            years = st.slider("years", 1, 10, 5, label_visibility="collapsed")
            st.caption("Max bet per stock")
            w_max = st.slider("wmax", 0.05, 1.0, 0.25, 0.05, label_visibility="collapsed")
        with sc2:
            st.caption("Risk appetite")
            risk_label = st.select_slider("risk", options=list(RISK_LEVELS.keys()), value="Balanced",
                                           label_visibility="collapsed")
            risk_aversion = RISK_LEVELS[risk_label]

        with st.expander("Advanced settings"):
            rf_annual = st.number_input("Risk-free rate (annual)", value=0.04, step=0.005, format="%.3f")
            batch_lr = st.number_input("Full-batch learning rate", value=20.0)
            batch_iters = st.number_input("Full-batch iterations", value=10000, step=1000)
            mb_lr = st.number_input("Mini-batch learning rate", value=10.0)
            mb_batch_size = st.number_input("Mini-batch size (days)", value=40, step=10)
            mb_iters = st.number_input("Mini-batch iterations", value=10000, step=1000)
            sharpe_lr = st.number_input("Sharpe-ascent learning rate", value=0.05, format="%.3f")
            sharpe_iters = st.number_input("Sharpe-ascent iterations", value=10000, step=1000)
            tol = st.number_input("Convergence tolerance", value=1e-9, format="%.1e")

        run_button = st.button("▶  Run the algorithms", type="primary", use_container_width=True)

with row1_right:
    with st.container(key="panel_chart"):
        panel_header("Chart", "Live-ish", muted_badge=True)
        if st.session_state.tickers:
            preview_ticker = st.selectbox("Preview", st.session_state.tickers,
                                           label_visibility="collapsed", key="preview_ticker")
            preview_range = st.radio("Range", list(RANGE_OPTS.keys()), horizontal=True,
                                      label_visibility="collapsed", key="preview_range")
            period, interval = RANGE_OPTS[preview_range]
            try:
                hist = load_ticker_history(preview_ticker, period, interval)
                quote = load_ticker_quote(preview_ticker)
            except Exception:
                hist, quote = pd.DataFrame(), {}
            if hist is not None and not hist.empty:
                last = quote.get("last_price") or hist["Close"].iloc[-1]
                prev = quote.get("previous_close") or hist["Close"].iloc[0]
                pct = (last - prev) / prev if prev else None
                positive = (pct or 0) >= 0
                color = GREEN if positive else RED
                arrow = "▲" if positive else "▼"
                st.markdown(
                    f'<div style="font-family:\'JetBrains Mono\',monospace;margin-bottom:8px;">'
                    f'<span style="font-size:1.3rem;font-weight:700;">{preview_ticker}</span>&nbsp;&nbsp;'
                    f'<span style="font-size:1.1rem;">{last:,.2f}</span>&nbsp;'
                    f'<span style="color:{color};font-weight:600;">{arrow} {pct:+.2%}</span></div>',
                    unsafe_allow_html=True,
                )
                ma20 = hist["Close"].rolling(20, min_periods=1).mean()
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.72, 0.28],
                                     vertical_spacing=0.03)
                fig.add_trace(go.Candlestick(
                    x=hist.index, open=hist["Open"], high=hist["High"], low=hist["Low"], close=hist["Close"],
                    increasing_line_color=GREEN, decreasing_line_color=RED,
                    increasing_fillcolor=GREEN, decreasing_fillcolor=RED, name=preview_ticker,
                ), row=1, col=1)
                fig.add_trace(go.Scatter(x=hist.index, y=ma20, mode="lines", name="20-period MA",
                                          line=dict(color=MUTED, width=1, dash="dot")), row=1, col=1)
                fig.add_trace(go.Bar(x=hist.index, y=hist["Volume"], marker_color="rgba(37,99,235,0.35)",
                                      name="Volume"), row=2, col=1)
                fig.update_layout(xaxis_rangeslider_visible=False, showlegend=False, height=360)
                st.plotly_chart(themed(fig), use_container_width=True, config={"displayModeBar": False})
            else:
                st.caption("No data for that ticker yet.")

# --------------------------- ROW 2: Ticks | Chain ---------------------------
row2_left, row2_right = st.columns(2, gap="large")

has_results = "results" in st.session_state
if has_results:
    R = st.session_state["results"]
    tickers, n = R["tickers"], R["n"]
    method_weights = {
        "Full-batch": R["batch_out"]["weights"], "Mini-batch": R["mb_out"]["weights"],
        "Sharpe": R["sharpe_out"]["weights"], "SLSQP": R["slsqp_mvo_out"]["weights"],
    }

with row2_left:
    with st.container(key="panel_ticks"):
        panel_header("Ticks", "Convergence", muted_badge=True)
        if not has_results:
            st.caption("Run the algorithms to see iteration-by-iteration convergence here.")
        else:
            algo = st.radio("algo", ["Full-batch", "Mini-batch", "Sharpe"], horizontal=True,
                             label_visibility="collapsed", key="ticks_algo")
            if algo == "Full-batch":
                y = R["batch_out"]["utility_prog"]
            elif algo == "Mini-batch":
                y = R["mb_out"]["utility_history"]
            else:
                y = R["sharpe_out"]["history"]
            y = np.asarray(y)
            n_show = min(18, len(y))
            idx = np.linspace(0, len(y) - 1, n_show).astype(int)
            vals = y[idx]
            deltas = np.diff(vals, prepend=vals[0])
            tick_df = pd.DataFrame({"Iter": idx, "Value": vals, "Δ": deltas})

            def _delta_color(v):
                return f"color: {GREEN}" if v >= 0 else f"color: {RED}"

            styler = (
                tick_df.style
                .format({"Value": "{:.6f}", "Δ": "{:+.6f}"})
                .map(_delta_color, subset=["Δ"])
                .set_properties(**{"font-family": "JetBrains Mono, monospace", "font-size": "0.78rem"})
            )
            st.dataframe(styler, use_container_width=True, hide_index=True, height=330)

with row2_right:
    with st.container(key="panel_chain"):
        panel_header("Chain", "All methods", muted_badge=True)
        if not has_results:
            st.caption("Run the algorithms to see every method's weights side by side here.")
        else:
            comp = pd.DataFrame(method_weights, index=tickers)
            comp = comp[(comp.abs() > 0.001).any(axis=1)]
            comp = comp.sort_values(comp.columns[0], ascending=False)
            cmap = LinearSegmentedColormap.from_list("panel_light", ["#FFFFFF", "#CCFBF1", "#0D9488"])
            styler = (
                comp.style.background_gradient(cmap=cmap, axis=0)
                .set_properties(**{"color": "#111827", "font-family": "JetBrains Mono, monospace", "font-size": "0.8rem"})
                .format("{:.1%}")
            )
            st.dataframe(styler, use_container_width=True, height=330)

# --------------------------- Top pick + Backtest ---------------------------
if run_button:
    tickers_in = list(dict.fromkeys(st.session_state.tickers))
    if len(tickers_in) < 2:
        st.error("Add at least 2 tickers in the Setup panel.")
        st.stop()

    with st.spinner(f"Downloading {years}y of price history for {len(tickers_in)} tickers..."):
        prices = load_prices(tickers_in, years)

    if prices.empty or prices.shape[1] < 2:
        st.error("Couldn't get usable price data for those tickers. Check the symbols and try again.")
        st.stop()

    valid_tickers = list(prices.columns)
    if len(valid_tickers) < len(tickers_in):
        st.warning(f"Dropped tickers with missing data: {set(tickers_in) - set(valid_tickers)}")

    split = int(len(prices) * 0.8)
    prices_train, prices_test = prices.iloc[:split], prices.iloc[split:]
    returns_train = prices_train.pct_change().dropna()
    returns_test = prices_test.pct_change().dropna()
    mu, Sigma = compute_mu_sigma(returns_train)
    rf_daily = rf_annual / TRADING_DAYS
    n2 = len(valid_tickers)

    with st.spinner("Running full-batch gradient ascent..."):
        batch_out = batch_gradient_ascent(mu, Sigma, risk_aversion=risk_aversion, w_max=w_max,
                                           learning_rate=batch_lr, iterations=int(batch_iters), tol=tol)
    with st.spinner("Running mini-batch gradient ascent..."):
        mb_out = minibatch_gradient_descent(returns_train.to_numpy(), risk_aversion=risk_aversion, w_max=w_max,
                                             learning_rate=mb_lr, batch_size=int(mb_batch_size),
                                             iterations=int(mb_iters), tol=tol, seed=1)
    with st.spinner("Running Sharpe-ratio gradient ascent..."):
        sharpe_out = sharpe_gradient_ascent(mu, Sigma, rf_daily, w_max=w_max,
                                             learning_rate=sharpe_lr, iterations=int(sharpe_iters), tol=tol)
    with st.spinner("Running SLSQP benchmarks..."):
        slsqp_mvo_out = slsqp_mvo(mu, Sigma, risk_aversion=risk_aversion, w_max=w_max)
        slsqp_sharpe_out = slsqp_sharpe(mu, Sigma, rf_daily, w_max=w_max)

    st.session_state["results"] = dict(
        tickers=valid_tickers, n=n2, prices=prices,
        returns_train=returns_train, returns_test=returns_test,
        mu=mu, Sigma=Sigma, rf_daily=rf_daily, rf_annual=rf_annual,
        risk_aversion=risk_aversion, w_max=w_max,
        batch_out=batch_out, mb_out=mb_out, sharpe_out=sharpe_out,
        slsqp_mvo_out=slsqp_mvo_out, slsqp_sharpe_out=slsqp_sharpe_out,
    )
    st.rerun()

has_results = "results" in st.session_state
if not has_results:
    st.info("Set up your universe and hit **▶ Run the algorithms** in the Setup panel to populate "
            "Ticks, Chain, Top Pick, and Backtest.")
else:
    R = st.session_state["results"]
    tickers, n = R["tickers"], R["n"]
    method_weights = {
        "Full-batch": R["batch_out"]["weights"], "Mini-batch": R["mb_out"]["weights"],
        "Sharpe": R["sharpe_out"]["weights"], "SLSQP": R["slsqp_mvo_out"]["weights"],
    }

    with st.container(key="panel_toppick"):
        avg_w = np.mean(list(method_weights.values()), axis=0)
        order = np.argsort(avg_w)[::-1]
        top_ticker, top_weight = tickers[order[0]], avg_w[order[0]]
        runners = [(tickers[i], avg_w[i]) for i in order[1:4] if avg_w[i] > 0.001]
        runner_html = "".join(
            f'<span style="margin-right:18px;color:{MUTED};font-family:\'JetBrains Mono\',monospace;font-size:.85rem;">{t} · {w:.1%}</span>'
            for t, w in runners
        )
        st.markdown(f"""
        <div class="toppick-label">Consensus top pick — average weight across all 4 strategies</div>
        <div class="toppick-ticker">{top_ticker}<span class="toppick-weight">{top_weight:.1%}</span></div>
        <div class="toppick-runners">{runner_html}</div>
        """, unsafe_allow_html=True)

    with st.container(key="panel_backtest"):
        panel_header("Backtest", "Out-of-sample", muted_badge=True)
        w_eq = np.full(n, 1.0 / n)
        methods_bt = {**method_weights, "Equal-weight": w_eq}
        reports_bt = [risk_report(w, R["returns_test"], R["rf_annual"], label=name)
                      for name, w in methods_bt.items()]
        st.dataframe(pd.concat(reports_bt, axis=1).style.format("{:.4f}"), use_container_width=True)

        fig_wealth = go.Figure()
        for name, w in methods_bt.items():
            cum = (1 + R["returns_test"].values @ w).cumprod()
            fig_wealth.add_trace(go.Scatter(y=cum, name=name))
        fig_wealth.update_layout(title="Cumulative value of $1 invested (test period)",
                                  xaxis_title="Trading day", yaxis_title="Portfolio value")
        st.plotly_chart(themed(fig_wealth), use_container_width=True)

        with st.expander("Arena detail: per-method return, Sharpe, iterations"):
            arena_reports = {name: risk_report(w, R["returns_test"], R["rf_annual"], label=name)
                              for name, w in method_weights.items()}
            iters_map = {"Full-batch": R["batch_out"]["iterations_run"], "Mini-batch": R["mb_out"]["iterations_run"],
                         "Sharpe": R["sharpe_out"]["iterations_run"], "SLSQP": "—"}
            detail = pd.concat(arena_reports.values(), axis=1)
            detail.loc["Iterations"] = [iters_map[k] for k in arena_reports]
            st.dataframe(detail, use_container_width=True)

        with st.expander("Data & correlations"):
            norm = R["prices"] / R["prices"].iloc[0]
            fig_p = px.line(norm, title="Normalized price (training + test period)",
                             color_discrete_sequence=COLORWAY)
            st.plotly_chart(themed(fig_p), use_container_width=True)
            corr = R["returns_train"].corr()
            fig_corr = px.imshow(corr, color_continuous_scale=[[0, RED], [0.5, PANEL], [1, GREEN]],
                                  zmin=-1, zmax=1, title="Correlation matrix (training period)")
            st.plotly_chart(themed(fig_corr), use_container_width=True)