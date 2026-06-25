from pathlib import Path

import pandas as pd
import streamlit as st


TRADES_PATH = Path("data/trades.csv")
SIGNALS_PATH = Path("data/signals.csv")


st.set_page_config(
    page_title="TradePilot AI Dashboard",
    page_icon="📈",
    layout="wide"
)


st.title("📈 TradePilot AI Dashboard")
st.caption("Crypto scanner + paper-trading analytics using Kraken public market data.")


def load_csv(path):
    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


trades_df = load_csv(TRADES_PATH)
signals_df = load_csv(SIGNALS_PATH)


tab_overview, tab_trades, tab_signals = st.tabs(
    ["Overview", "Paper Trades", "Signals"]
)


with tab_overview:
    st.subheader("Portfolio Overview")

    if trades_df.empty:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Closed Trades", 0)
        col2.metric("Total PnL", "£0")
        col3.metric("Win Rate", "0%")
        col4.metric("Average PnL", "£0")

        st.info("No closed paper trades yet. Leave the scanner running until a paper trade closes.")
    else:
        trades_df["pnl"] = pd.to_numeric(trades_df["pnl"], errors="coerce").fillna(0)

        total_trades = len(trades_df)
        total_pnl = trades_df["pnl"].sum()
        wins = trades_df[trades_df["pnl"] > 0]
        win_rate = (len(wins) / total_trades) * 100 if total_trades else 0
        average_pnl = trades_df["pnl"].mean()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Closed Trades", total_trades)
        col2.metric("Total PnL", f"£{total_pnl:.2f}")
        col3.metric("Win Rate", f"{win_rate:.2f}%")
        col4.metric("Average PnL", f"£{average_pnl:.2f}")

        st.subheader("PnL by Symbol")

        pnl_by_symbol = (
            trades_df.groupby("symbol")["pnl"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )

        st.bar_chart(
            pnl_by_symbol,
            x="symbol",
            y="pnl"
        )

        st.subheader("Recent Closed Trades")
        st.dataframe(trades_df.tail(10), use_container_width=True)


with tab_trades:
    st.subheader("Closed Paper Trades")

    if trades_df.empty:
        st.warning("No closed trades found yet.")
    else:
        trades_df["pnl"] = pd.to_numeric(trades_df["pnl"], errors="coerce").fillna(0)

        symbol_filter = st.multiselect(
            "Filter by symbol",
            sorted(trades_df["symbol"].dropna().unique())
        )

        filtered_trades = trades_df.copy()

        if symbol_filter:
            filtered_trades = filtered_trades[
                filtered_trades["symbol"].isin(symbol_filter)
            ]

        st.dataframe(filtered_trades, use_container_width=True)

        csv = filtered_trades.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download trades CSV",
            data=csv,
            file_name="tradepilot_trades.csv",
            mime="text/csv"
        )


with tab_signals:
    st.subheader("Signal Log")

    if signals_df.empty:
        st.warning("No WATCH or PAPER_LONG signals logged yet.")
    else:
        signal_filter = st.multiselect(
            "Filter by signal",
            sorted(signals_df["signal"].dropna().unique())
        )

        filtered_signals = signals_df.copy()

        if signal_filter:
            filtered_signals = filtered_signals[
                filtered_signals["signal"].isin(signal_filter)
            ]

        st.dataframe(filtered_signals.tail(100), use_container_width=True)

        st.subheader("Signals by Symbol")

        signals_by_symbol = (
            filtered_signals.groupby("symbol")
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )

        if not signals_by_symbol.empty:
            st.bar_chart(
                signals_by_symbol,
                x="symbol",
                y="count"
            )

        csv = filtered_signals.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download signals CSV",
            data=csv,
            file_name="tradepilot_signals.csv",
            mime="text/csv"
        )


st.divider()

st.caption(
    "Paper trading only. Not financial advice. Crypto is high risk. "
    "Results are simulated and may not match real trading."
)
