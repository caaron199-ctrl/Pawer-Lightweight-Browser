"""
Sample Streamlit Application for Pawer Browser.
Demonstrates interactive metrics, real-time widgets, charts, and local diagnostics.
"""

import datetime
import time
import pandas as pd
import numpy as np
import streamlit as st

# Configure page
st.set_page_config(
    page_title="Pawer Streamlit Showcase",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling for modern look
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #cba6f7 0%, #89b4fa 50%, #a6e3a1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        background-color: rgba(166, 227, 161, 0.15);
        color: #a6e3a1;
        border: 1px solid rgba(166, 227, 161, 0.3);
        font-weight: 600;
        font-size: 0.85rem;
    }
    .card-metric {
        background-color: #1e1e2e;
        border: 1px solid #313244;
        border-radius: 10px;
        padding: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar
with st.sidebar:
    st.image("https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f43e.png", width=64)
    st.markdown("### 🐾 Pawer Control Panel")
    st.markdown("Running inside **Pawer Browser**.")
    st.markdown('<span class="badge">● Local Isolation Active</span>', unsafe_allow_html=True)
    st.divider()

    dataset_size = st.slider("Data Points", min_value=50, max_value=1000, value=250, step=50)
    noise_level = st.slider("Volatility Factor", min_value=0.1, max_value=2.0, value=0.5, step=0.1)
    chart_theme = st.selectbox("Chart Style", ["Area Chart", "Line Chart", "Bar Chart"])

    st.divider()
    st.caption("Pawer: Super Lightweight Browser for Local Apps")

# Main Content Header
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown('<h1 class="main-header">🐾 Pawer Streamlit Showcase</h1>', unsafe_allow_html=True)
    st.write("Lightweight, dedicated browser environment running completely offline on localhost.")

with col_status:
    st.metric(label="Browser Engine", value="WebView2", delta="~35MB RAM vs 1.2GB Chrome")

# Key Metrics Row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Local Port", "8501", delta="Streamlit Native")
with col2:
    st.metric("WebSocket Latency", "< 1 ms", delta="Local Loopback")
with col3:
    st.metric("Internet Access", "Blocked", delta="100% Private", delta_color="inverse")
with col4:
    st.metric("DevTools", "F12 Enabled", delta="Chromium Inspect")

st.divider()

# Tabs
tab_charts, tab_data, tab_bench, tab_about = st.tabs([
    "📈 Interactive Analytics",
    "📊 Data Explorer",
    "⚡ Performance & Isolation",
    "🐾 About Pawer",
])

with tab_charts:
    st.subheader("Simulated Real-Time Signal Stream")
    dates = pd.date_range(end=datetime.date.today(), periods=dataset_size)
    np.random.seed(42)
    values_a = np.cumsum(np.random.randn(dataset_size) * noise_level) + 100
    values_b = np.cumsum(np.random.randn(dataset_size) * noise_level) + 80
    df = pd.DataFrame({"Sensor Alpha": values_a, "Sensor Beta": values_b}, index=dates)

    if chart_theme == "Area Chart":
        st.area_chart(df, color=["#cba6f7", "#89b4fa"])
    elif chart_theme == "Line Chart":
        st.line_chart(df, color=["#cba6f7", "#a6e3a1"])
    else:
        st.bar_chart(df, color=["#89b4fa", "#f9e2af"])

with tab_data:
    st.subheader("Dynamic Local DataFrame")
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        search_query = st.text_input("Filter Columns / Search", placeholder="Filter records...")
    with col_filter2:
        num_rows = st.number_input("Display Limit", min_value=5, max_value=100, value=15)

    sample_table = df.reset_index().rename(columns={"index": "Timestamp"})
    st.dataframe(sample_table.head(int(num_rows)), use_container_width=True)

with tab_bench:
    st.subheader("Why Pawer for Local Development?")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            """
            #### 🚀 Performance Highlights
            - **Super lightweight**: Uses the system Edge Chromium WebView2 engine already installed on Windows.
            - **No bundled 200MB Chromium/Electron binary**: Starts in milliseconds.
            - **Low memory consumption**: Takes ~35-50 MB compared to Chrome/Firefox taking 1GB+ with 20 extensions.
            - **Persistent WebSockets**: Switching between tabs never drops your Streamlit session state!
            """
        )
    with c2:
        st.markdown(
            """
            #### 🛡️ Local Isolation & Safety
            - **Zero Internet Wandering**: External internet navigation is strictly intercepted and blocked.
            - **No Telemetry / No Tracking**: No ad networks, no analytics, no external scripts.
            - **Auto Process Cleanup**: Background servers terminate cleanly when Pawer closes.
            - **1-Click Port Switcher**: Instantly jump between Streamlit (8501), FastAPI (8000), and React (3000).
            """
        )

with tab_about:
    st.subheader("About Pawer")
    st.info(
        "Pawer was crafted to provide an ultra-clean, minimal, and lightning-fast browsing application "
        "tailored specifically for running Streamlit dashboards and local web apps without the bloat, ads, "
        "and overhead of general-purpose internet browsers."
    )
    if st.button("Trigger Live Streamlit Rerun"):
        st.success("App refreshed seamlessly in Pawer!")
