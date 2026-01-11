import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import date

# =====================
# PARAMETRY
# =====================
EMA_LEN = 200
LOOKBACK = 252

ASSETS = {
    "SP500": "^GSPC",
    "NASDAQ": "^IXIC",
    "EEM": "EEM"
}

WORLD = "SPY"

W1 = 0.8
W2 = 0.2

# =====================
# FUNKCJE
# =====================
@st.cache_data(ttl=3600)
def load_prices(tickers):
    df = yf.download(list(tickers.values()), period="5y", progress=False)["Close"]
    return df.dropna()

prices = load_prices({**ASSETS, "WORLD": WORLD})

if len(prices) < max(EMA_LEN, LOOKBACK):
    st.error("❌ Za mało danych z Yahoo Finance (spróbuj ponownie później)")
    st.stop()

ema200 = prices[WORLD].ewm(span=EMA_LEN).mean().iloc[-1]
price_now = prices[WORLD].iloc[-1]

def calculate_momentum(prices):
    return prices.iloc[-1] / prices.iloc[-LOOKBACK] - 1

# =====================
# APP
# =====================
st.set_page_config(page_title="Risk-On Momentum Portfolio", layout="centered")

st.title("📊 Risk-On Momentum – TOP 2")
st.caption("Daily signal / Daily trade")

prices = load_prices({**ASSETS, "WORLD": WORLD})

# EMA200
ema200 = prices[WORLD].ewm(span=EMA_LEN).mean().iloc[-1]
price_now = prices[WORLD].iloc[-1]

risk_on = price_now > ema200

st.subheader("🌍 Reżim rynkowy")
st.write("**RISK-ON** ✅" if risk_on else "**RISK-OFF** ❌")

# Momentum
momentum = calculate_momentum(prices[list(ASSETS.values())])
momentum.index = ASSETS.keys()

momentum = momentum.sort_values(ascending=False)

st.subheader("📈 Momentum 12M")
st.dataframe((momentum * 100).round(2).rename("Return %"))

# Alokacja
st.subheader("💼 Skład portfela")

if risk_on:
    top1, top2 = momentum.index[:2]
    st.write(f"**{top1}** – {int(W1*100)}%")
    st.write(f"**{top2}** – {int(W2*100)}%")
else:
    st.write("**CASH – 100%**")

st.divider()
st.caption(f"Dane: Yahoo Finance | Aktualizacja: {date.today()}")
