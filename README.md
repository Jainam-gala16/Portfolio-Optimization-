# Gradient — Portfolio Terminal

A dark, multi-pane trading-terminal layout (inspired by real trading platforms)
instead of a sidebar-and-tabs app or a marketing-style dashboard. A slim
toolbar strip up top, a scrolling ticker marquee, then a 2x2 grid of docked
panels:

- **Setup** — your ticker "holdings" as removable chips, an add-a-ticker box,
  time window, a plain-English Risk Appetite slider, max-bet-per-stock, an
  Advanced expander for GD hyperparameters, and the Run button. This used to be
  a tall sticky sidebar; now it's just one panel among equals, sized like the
  others.
- **Chart** — a live-ish candlestick + volume view (with a 20-period moving
  average) for whichever ticker you pick, independent of whether you've run
  the optimizers yet.
- **Ticks** — a convergence tick-list for whichever gradient method you
  select (Full-batch / Mini-batch / Sharpe), styled like a time-and-sales
  ticker tape: iteration #, utility value, and a green/red delta each step.
- **Chain** — a dense weights grid (ticker x method), shaded like an options
  chain, using a heatmap gradient that's been kept dark-mode-safe (see below).

Below the grid: a **Top Pick** banner (the stock all four optimizers agree on
most) and a **Backtest** panel with the out-of-sample performance table,
cumulative-wealth chart, and expanders for per-method detail and correlations.

## Code review — bug found & fixed

Your gradient ascent implementations check out: verified against SLSQP across
dozens of random synthetic portfolios, both full-batch and Sharpe-ratio GD land
within a fraction of a percent of the true optimum. The one real bug was in the
SLSQP *benchmark* itself (`slsqp_mvo` was missing an analytic gradient, so scipy's
numerical fallback could falsely report convergence at the untouched equal-weight
starting guess) — that's fixed now with an analytic jacobian and tighter
tolerances, and the two now agree closely.

## Contrast check

Since this got explicitly called out: every text/background color pair actually
used in the app was run through a WCAG contrast-ratio calculation. All of them
clear 5.5:1, most clear 9-16:1 (WCAG AA for normal text only requires 4.5:1), so
nothing should wash out — including the Chain panel's heatmap, whose gradient is
deliberately capped to stay within dark shades (so the light text on top never
loses contrast the way a default light-to-dark colormap would).

## Run locally

```bash
pip install -r requirements.txt
streamlit run stocks.py
```

Then open the local URL Streamlit prints (usually http://localhost:8501).

Everything (UI + optimizer math) lives in the one `stocks.py` file. The
**`.streamlit/config.toml`** file sets the dark base theme that the custom CSS
builds on — keep it in a `.streamlit/` subfolder right next to `stocks.py`, or
the app falls back to Streamlit's default theme.

Implementation notes, since parts of this lean on Streamlit internals that
aren't official public API:
- Each panel's card styling (background/border/radius) targets the CSS class
  Streamlit generates for `st.container(key=...)` (e.g. `.st-key-panel_setup`).
  This is a widely-used community pattern, but Streamlit could rename that
  class in a future release — the app still works either way, it'd just look
  less polished until the selector is updated.
- The Chain panel's heatmap uses `pandas.Styler.background_gradient`, which
  needs `matplotlib` installed (added to requirements.txt) even though nothing
  else in the app plots with it directly.
- Running the optimizers triggers `st.rerun()` once results are saved, so the
  Ticks/Chain/Backtest panels reflect the new run immediately rather than
  needing a second interaction.

## Deploy to Streamlit Community Cloud (free)

1. Push this folder to a GitHub repo — needs `stocks.py`, `requirements.txt`,
   and the `.streamlit/config.toml` file (with that exact folder name/path).
2. Go to https://share.streamlit.io, sign in with GitHub.
3. "New app" -> pick the repo/branch -> set main file to `stocks.py` -> Deploy.
4. It rebuilds automatically on every push to the branch.

No secrets or API keys needed — `yfinance` pulls public price data directly.
