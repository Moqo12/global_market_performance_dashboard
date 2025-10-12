import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import seaborn as sns

# --- Dashboard Configuration ---
st.set_page_config(page_title="Global Performance Dashboard (GBP)", layout="wide")
st.title("📈 Global Market Performance Dashboard (in GBP)")
st.markdown("Analyzing the performance of investment factors, regions, and sectors using London-listed ETFs.")

# --- Ticker Definitions ---
FACTOR_TICKERS = {
    "MSCI World (Benchmark)": "SWDA.L",
    "MSCI ACWI (Benchmark)": "SSAC.L",
    "World Momentum": "IWFM.L",
    "World Value": "XDEV.L",
    "World Quality": "IWQU.L",
    "World Size": "IWFS.L",
}

REGION_TICKERS = {
    "MSCI World (Benchmark)": "SWDA.L", # Added for comparison
    "USA": "CSUS.L",
    "Japan": "SJPA.L",
    "UK": "CSUK.L",
    "Europe ex-UK": "CEUG.L",
    "Emerging Markets ex-China": "EMXC.L", 
    "China A-Shares": "CNYA.L",
    "Canada": "CCAU.L",
}

SECTOR_TICKERS = {
    "MSCI World (Benchmark)": "SWDA.L", # Added for comparison
    "Info. Technology": "IUIT.L",
    "Health Care": "IUES.L",
    "Financials": "IUFS.L",
    "Cons. Discretionary": "IUCD.L",
    "Industrials": "IUIS.L",
    "Cons. Staples": "IUCS.L",
    "Energy": "IESE.L",
    "Utilities": "IUUS.L",
    "Materials": "IUMS.L",
    "Real Estate": "EPRA.L",
    "Communication Svcs": "IUCM.L",
}

@st.cache_data(ttl=3600) # Cache data for 1 hour
def get_performance_data(tickers, start_date):
    # ... (function is updated to accept a start_date)
    raw_data = yf.download(list(tickers.values()), start=start_date, progress=False, auto_adjust=False)

    if raw_data.empty or 'Close' not in raw_data:
        st.error(f"Could not download market data for one or more tickers.")
        return pd.DataFrame(), pd.DataFrame()
    
    if isinstance(raw_data.columns, pd.MultiIndex):
        data = raw_data['Close'].dropna(axis=1, how='all')
    else:
        data = raw_data[['Close']].dropna(axis=1, how='all')

    if data.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Rename columns to human-readable names
    ticker_to_name = {v: k for k, v in tickers.items()}
    data.rename(columns=ticker_to_name, inplace=True)
        
    return data

def calculate_performance_metrics(data):
    # ... (New function to separate calculation from data fetching)
    if len(data) < 2:
        return pd.DataFrame()

    latest_price = data.iloc[-1]
    perf_1d = latest_price / data.iloc[-2] - 1

    if len(data) > 21:
        perf_1m = latest_price / data.iloc[-22] - 1
    else:
        perf_1m = latest_price / data.iloc[0] - 1
    
    current_year = datetime.now().year
    last_year_data = data[data.index.year == current_year - 1]
    if not last_year_data.empty:
        ytd_start_price = last_year_data.iloc[-1]
        perf_ytd = latest_price / ytd_start_price - 1
    else:
        perf_ytd = latest_price / data[data.index.year == current_year].iloc[0] - 1

    performance_df = pd.DataFrame({
        "1-Day Change": perf_1d,
        "1-Month Change": perf_1m,
        "YTD Total Return (incl. dividends)": perf_ytd
    })
    
    return performance_df

def style_performance_table(df, benchmark_name="MSCI World (Benchmark)"):
    # ... (function is unchanged)
    if benchmark_name not in df.index:
        return df.style.format("{:.2%}").background_gradient(cmap='RdYlGn', axis=None)

    benchmark_row = df.loc[benchmark_name]
    diffs = df - benchmark_row

    max_pos_per_col = diffs[diffs > 0].max()
    max_neg_per_col = abs(diffs[diffs < 0].min())

    green_cmap = mcolors.LinearSegmentedColormap.from_list("green_grad", ["#E8F5E9", "#1B5E20"])
    red_cmap = mcolors.LinearSegmentedColormap.from_list("red_grad", ["#FFEBEE", "#B71C1C"])
    gray_color = "#F0F2F6"

    def color_rows_gradient(row):
        styles = []
        for col_name, value in row.items():
            if row.name == benchmark_name:
                styles.append(f"background-color: {gray_color}; color: black;")
                continue

            diff = value - benchmark_row[col_name]

            if diff > 0:
                max_pos = max_pos_per_col[col_name]
                if pd.notna(max_pos) and max_pos > 0:
                    norm_intensity = min(diff / max_pos, 1.0)
                    rgba = mcolors.to_rgba(green_cmap(norm_intensity))
                    styles.append(f"background-color: rgba({int(rgba[0]*255)}, {int(rgba[1]*255)}, {int(rgba[2]*255)}, {0.9});")
                else:
                    styles.append("background-color: white; color: black;")
            elif diff < 0:
                max_neg = max_neg_per_col[col_name]
                if pd.notna(max_neg) and max_neg > 0:
                    norm_intensity = min(abs(diff) / max_neg, 1.0)
                    rgba = mcolors.to_rgba(red_cmap(norm_intensity))
                    styles.append(f"background-color: rgba({int(rgba[0]*255)}, {int(rgba[1]*255)}, {int(rgba[2]*255)}, {0.9});")
                else:
                    styles.append("background-color: white; color: black;")
            else:
                 styles.append("background-color: white; color: black;")
        return styles

    return df.style.apply(color_rows_gradient, axis=1).format("{:.2%}")

def display_performance_section(title, tickers):
    # ... (function is updated to use new data fetching and calculation functions)
    st.header(f"{title} Performance Overview (GBP)")
    current_year = datetime.now().year
    start_date = f"{current_year - 1}-12-25"
    
    data = get_performance_data(tickers, start_date)
    performance_table = calculate_performance_metrics(data)
    
    benchmark_name = "MSCI World (Benchmark)"

    if not performance_table.empty:
        # Reorder and Style the table
        if benchmark_name in performance_table.index and title != "Factor":
            sort_col = "YTD Total Return (incl. dividends)"
            benchmark_ytd = performance_table.loc[benchmark_name, sort_col]
            
            above_benchmark = performance_table[performance_table[sort_col] > benchmark_ytd].sort_values(by=sort_col, ascending=False)
            benchmark_row = performance_table.loc[[benchmark_name]]
            below_benchmark = performance_table[performance_table[sort_col] <= benchmark_ytd].drop(index=benchmark_name).sort_values(by=sort_col, ascending=False)
            
            display_table = pd.concat([above_benchmark, benchmark_row, below_benchmark])
            
            st.dataframe(style_performance_table(display_table, benchmark_name), use_container_width=True)
        else:
            st.dataframe(style_performance_table(performance_table.sort_values(by="YTD Total Return (incl. dividends)", ascending=False)), use_container_width=True)

        st.header(f"Visual Comparison - {title}")
        
        metric_to_plot = st.selectbox(
            "Choose a performance metric to visualize:",
            ("YTD Total Return (incl. dividends)", "1-Month Change", "1-Day Change"),
            key=f"select_{title}"
        )

        if metric_to_plot in performance_table.columns:
            chart_data = performance_table[[metric_to_plot]].copy()
            chart_data.columns = ['Performance']
            chart_data = chart_data.sort_values(by='Performance', ascending=False)
            st.bar_chart(chart_data)
            st.caption("Chart shows performance sorted from best to worst.")
        else:
            st.warning(f"Could not find data for '{metric_to_plot}'.")
    else:
        st.warning(f"Could not display performance data for {title}.")

def display_risk_correlation_section(all_tickers):
    """New section for Correlation and Rolling Performance analysis."""
    st.header("Risk & Correlation Analysis")

    # Fetch 3 years of data for meaningful analysis
    start_date = (datetime.now() - pd.DateOffset(years=3)).strftime('%Y-%m-%d')
    data = get_performance_data(all_tickers, start_date)

    if not data.empty:
        # --- 1. Correlation Heatmap ---
        st.subheader("Correlation Heatmap")
        st.write("This grid shows how different assets move in relation to each other. A value of 1 means they move perfectly together; a value of 0 means they have no relationship.")
        
        # Calculate correlations on daily returns
        returns = data.pct_change()
        corr_matrix = returns.corr()

        # Plot heatmap
        fig, ax = plt.subplots(figsize=(12, 9))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=.5, ax=ax)
        st.pyplot(fig)

        # --- 2. Rolling Performance ---
        st.subheader("1-Year Rolling Performance")
        st.write("This chart shows the trailing 1-year performance for each asset over the last 3 years, helping to visualize long-term trends and cyclicality.")
        
        # Calculate 1-year (252 trading days) rolling returns
        rolling_returns = (data.pct_change(252).dropna()) * 100
        st.line_chart(rolling_returns)

# --- Main App Logic ---
# Combine all tickers into one dict for the new tab
ALL_TICKERS = {**FACTOR_TICKERS, **REGION_TICKERS, **SECTOR_TICKERS}

tab1, tab2, tab3, tab4 = st.tabs(["Factor", "Regional", "Sector", "Risk & Correlation"])

with tab1:
    display_performance_section("Factor", FACTOR_TICKERS)

with tab2:
    display_performance_section("Regional", REGION_TICKERS)

with tab3:
    display_performance_section("Sector", SECTOR_TICKERS)

with tab4:
    display_risk_correlation_section(ALL_TICKERS)

st.markdown(f"--- \n_*Data last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*_")

