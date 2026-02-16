import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import date

# =====================
# PARAMETRY STRATEGII
# =====================

EMA_LEN = 200
LOOKBACK = 252
SKIP = 21

# Wagi portfela
W1 = 0.8
W2 = 0.2

# Cash rate (informacyjnie)
CASH_RATE = 0.02

# =====================
# UNIWERSUM AKTYWÓW (PRODUCTION ETF)
# =====================

ASSETS = {
    "SP500":  "SPY",
    "NASDAQ": "QQQ",
    "EAFE":   "EFA",
    "EEM":    "EEM"
}

WORLD = "SPY"   # filtr trendu rynku

# =====================
# FUNKCJE
# =====================

@st.cache_data(ttl=1800)
def load_prices(tickers):
    df = yf.download(list(tickers.values()), period="6y", progress=False)["Close"]
    return df.dropna()

def calculate_momentum(prices):
    # momentum 12M z pominięciem ostatnich 21 dni (jak w backteście)
    return prices.iloc[-1 - SKIP] / prices.iloc[-1 - LOOKBACK - SKIP] - 1

# =====================
# APP
# =====================

st.set_page_config(page_title="Global Momentum Portfolio", layout="centered")

st.title("🌍 Global Momentum Portfolio")
st.caption("Production signal – zgodny z backtestem")

prices = load_prices({**ASSETS, "WORLD": WORLD})

l = len(prices)
if l < (LOOKBACK + SKIP + 10):
    st.error(f"❌ Za mało danych z Yahoo Finance ({l} sesji). Spróbuj później.")
    st.stop()

# =====================
# FILTR TRENDU (SP500 EMA200)
# =====================

ema200 = prices[WORLD].ewm(span=EMA_LEN).mean().iloc[-1]
price_now = prices[WORLD].iloc[-1]

risk_on = price_now > ema200

st.subheader("🌍 Reżim rynkowy (Trend Filter)")
st.write("**RISK-ON** ✅" if risk_on else "**RISK-OFF** ❌")
st.caption(f"SPY: {price_now:.2f} | EMA200: {ema200:.2f}")

# =====================
# MOMENTUM 12M
# =====================

momentum = calculate_momentum(prices[list(ASSETS.values())])
momentum.index = ASSETS.keys()
momentum = momentum.sort_values(ascending=False)

st.subheader("📈 Momentum 12M (skip 21 dni)")
st.dataframe((momentum * 100).round(2).rename("Return %"))

# =====================
# WYBÓR PORTFELA
# =====================

st.subheader("💼 Aktualna alokacja portfela")

allocation = {}

if not risk_on:
    # risk-off → cash
    st.write("**CASH – 100%**")
    st.caption(f"Oprocentowanie cash: ~{CASH_RATE*100:.1f}% rocznie")

else:
    # tylko aktywa z dodatnim momentum
    valid = momentum[momentum > 0]

    if len(valid) == 0:
        st.write("**CASH – 100%**")
        st.caption("Brak aktywów z dodatnim momentum")

    elif len(valid) == 1:
        top1 = valid.index[0]
        st.write(f"**{top1}** – 100%")

    else:
        top1, top2 = valid.index[:2]
        allocation[top1] = W1
        allocation[top2] = W2

        st.write(f"**{top1}** – {int(W1*100)}%")
        st.write(f"**{top2}** – {int(W2*100)}%")

# =====================
# PODSUMOWANIE SYGNAŁU
# =====================

st.divider()
st.subheader("🧭 Sygnał produkcyjny")

if not risk_on or len(momentum[momentum > 0]) == 0:
    st.success("➡️ Portfel defensywny: **CASH 100%**")
else:
    st.success("➡️ Portfel risk-on aktywny")

    for k, v in allocation.items():
        st.write(f"- {k}: {int(v*100)}%")


if st.sidebar.button("🔄 Wyczyść cache"):
    st.cache_data.clear()
    st.experimental_rerun()

st.divider()
st.caption(f"Dane: Yahoo Finance | Aktualizacja: {date.today()} | Model: Global Momentum Core")
