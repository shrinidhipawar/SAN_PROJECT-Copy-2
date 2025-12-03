import streamlit as st
import pandas as pd
import os

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
        base_dir = os.path.dirname(__file__)
        data_path = os.path.join(base_dir, "data", "processed_data.csv")
        df = load_data(data_path)
    except Exception as e:
        st.error(f"Could not load data: {e}")
        return

    # Sidebar filters
    st.sidebar.header("Filters")

    scenario = st.sidebar.selectbox("Select SAN Architecture", df["scenario"].unique())
    encryption = st.sidebar.selectbox("Encryption Setting (ON / OFF)", df["encryption"].unique())

    enc_flag = str(encryption).lower() in ["on", "1", "yes", "aes-256", "aes", "true"]

    filtered = df[(df["scenario"] == scenario) & (df["encryption"] == encryption)]

    # Create Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Overview", 
        "Performance Monitoring", 
        "Encryption Analysis", 
        "AI Insights"
    ])

    # ---------------------------------------------------------
    # TAB 1: OVERVIEW
    # ---------------------------------------------------------
    with tab1:
        st.subheader("System Status")
        
        # Calculate KPIs
        avg_throughput = filtered["effective_throughput_MBps"].mean()
        max_throughput = filtered["effective_throughput_MBps"].max()
        avg_latency = filtered["total_delay_s"].mean() * 1000  # convert to ms
        
        # Display KPIs in columns
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Average Throughput", f"{avg_throughput:.2f} MB/s")
        kpi2.metric("Peak Throughput", f"{max_throughput:.2f} MB/s")
        kpi3.metric("Average Latency", f"{avg_latency:.2f} ms")
        
        st.markdown("---")
        st.markdown("#### Configuration Details")
        st.markdown(f"""
        - **Architecture:** {scenario}
        - **Encryption:** {encryption}
        - **Data Points:** {len(filtered)}
        """)

    # ---------------------------------------------------------
    # TAB 2: REAL-TIME MONITORING
    # ---------------------------------------------------------
    with tab2:
        st.subheader("Performance Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Throughput Over Time")
            st.pyplot(plot_throughput_time(filtered))
        
        with col2:
            st.markdown("#### Latency Over Time")
            st.pyplot(plot_latency_time(filtered))
            
        st.markdown("#### Encryption Overhead Comparison")
        st.pyplot(plot_encryption_bar(df))

    # ---------------------------------------------------------
    # TAB 3: ENCRYPTION ANALYSIS
    # ---------------------------------------------------------
    with tab3:
        st.subheader("Encryption Overhead Analysis")
        st.markdown("Analysis of AES-256 encryption impact on SAN performance.")
        
        # Check if encryption analysis plots exist
        plots_dir = os.path.join(os.path.dirname(base_dir), "encryption_analysis_plots")
        
        if os.path.exists(plots_dir):
            st.markdown("#### Key Performance Indicators")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Throughput Comparison**")
                st.caption("Baseline vs. Encrypted Throughput (MB/s)")
                throughput_plot = os.path.join(plots_dir, "throughput_comparison.png")
                if os.path.exists(throughput_plot):
                    st.image(throughput_plot, use_container_width=True)
            
            with col2:
                st.markdown("**Latency Inflation**")
                st.caption("Latency Impact Over Time")
                latency_plot = os.path.join(plots_dir, "latency_inflation.png")
                if os.path.exists(latency_plot):
                    st.image(latency_plot, use_container_width=True)
            
            st.markdown("---")
            st.markdown("#### Operational Impact Analysis")
            col3, col4 = st.columns(2)
            
            with col3:
                st.markdown("**Backup Window Impact**")
                st.caption("Estimated Backup Time Increase")
                backup_plot = os.path.join(plots_dir, "backup_window_increase.png")
                if os.path.exists(backup_plot):
                    st.image(backup_plot, use_container_width=True)
            
            with col4:
                st.markdown("**Overhead Summary Dashboard**")
                st.caption("Comprehensive Metrics Overview")
                summary_plot = os.path.join(plots_dir, "encryption_overhead_summary.png")
                if os.path.exists(summary_plot):
                    st.image(summary_plot, use_container_width=True)
            
            # Load and display summary metrics
            metrics_file = os.path.join(os.path.dirname(base_dir), "encryption_degradation_summary.csv")
            if os.path.exists(metrics_file):
                st.markdown("#### Performance Impact Summary")
                metrics_df = pd.read_csv(metrics_file)
                st.dataframe(metrics_df, use_container_width=True)
        else:
            st.info("Run `encryption_analysis.py` to generate encryption overhead analysis plots.")

    # ---------------------------------------------------------
    # TAB 4: AI INSIGHTS
    # ---------------------------------------------------------
    with tab4:
        st.subheader("AI Insights & Recommendations")
        
        # Congestion forecast
        st.markdown("#### Load Forecast & Backup Planning")
        future_load = st.slider("Select future backup load (MB/s)", min_value=1, max_value=2000, value=100)
        prediction = predict_congestion(df, future_load)
        st.info(f"Forecast: {prediction}")
        
        st.markdown("---")
        st.markdown("#### Generative AI Analysis")

        if st.button("Generate Analysis"):
            scenario_name = scenario
            enc_text = "ON" if enc_flag else "OFF"

            with st.spinner("Analyzing data..."):
                try:
                    llm_text = generate_llm_insights(filtered, scenario_name, enc_text)
                except Exception as e:
                    llm_text = f"Error generating insights: {e}"

            # run the richer LLM wrapper
            with st.spinner("Generating detailed recommendations..."):
                try:
                    llm_full = run_llm(filtered, scenario_name, enc_text)
                except Exception as e:
                    llm_full = f"Error generating recommendations: {e}"

            st.markdown("#### Analysis Summary")
            st.success(llm_text)

            st.markdown("#### Detailed Recommendations")
            st.write(llm_full)


if __name__ == "__main__":
    main()
