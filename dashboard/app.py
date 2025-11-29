import streamlit as st
import pandas as pd

# Import plotting and llm helpers from local modules
from modules.plots import (
    plot_throughput_time,
    plot_latency_time,
    plot_encryption_bar,
)

from modules.llm import (
    generate_llm_insights,
    predict_congestion,
    run_llm,
)


@st.cache_data
def load_data(path: str):
    return pd.read_csv(path)


def main():
    st.set_page_config(page_title="SAN Performance Dashboard", layout="wide")

    st.title("🔧 SAN Performance & Backup Optimization Dashboard")
    st.markdown("Interactive analytics for **Traditional SAN**, **FC SAN**, with/without AES-256 encryption.")

    # Load processed data
    try:
        df = load_data("data/processed_data.csv")
    except Exception as e:
        st.error(f"Could not load data: {e}")
        return

    # Sidebar filters
    st.sidebar.header("Filters")

    scenario = st.sidebar.selectbox("Select SAN Architecture", df["scenario"].unique())
    encryption = st.sidebar.selectbox("Encryption Setting (ON / OFF)", df["encryption"].unique())

    enc_flag = str(encryption).lower() in ["on", "1", "yes", "aes-256", "aes", "true"]

    filtered = df[(df["scenario"] == scenario) & (df["encryption"] == encryption)]

    st.subheader(f"📌 Current View: **{scenario} — {encryption}**")

    # Visualizations
    st.markdown("### 📈 Throughput Over Time")
    st.pyplot(plot_throughput_time(filtered))

    st.markdown("### 📉 Latency Over Time")
    st.pyplot(plot_latency_time(filtered))

    st.markdown("### 🔐 Encryption Overhead Comparison")
    st.pyplot(plot_encryption_bar(df))

    # Congestion forecast
    st.markdown("---")
    st.header("📡 Load Forecast & Backup Planning")

    future_load = st.slider("Select future backup load (MB/s)", min_value=1, max_value=2000, value=100)
    prediction = predict_congestion(df, future_load)
    st.info(f"**Forecast:** {prediction}")

    # LLM Insights panel
    st.markdown("---")
    st.header("🤖 AI Insights & Recommendations")

    if st.button("Generate AI Insights"):
        scenario_name = scenario
        enc_text = "ON" if enc_flag else "OFF"

        with st.spinner("Generating short insights..."):
            try:
                llm_text = generate_llm_insights(filtered, scenario_name, enc_text)
            except Exception as e:
                llm_text = f"LLM short-insight error: {e}"

        # run the richer LLM wrapper
        with st.spinner("Generating recommendations..."):
            try:
                llm_full = run_llm(filtered, scenario_name, enc_text)
            except Exception as e:
                llm_full = f"LLM recommendation error: {e}"

        st.subheader("🔍 AI Insights Summary")
        st.success(llm_text)

        st.subheader("📘 Recommendations")
        st.write(llm_full)


if __name__ == "__main__":
    main()
