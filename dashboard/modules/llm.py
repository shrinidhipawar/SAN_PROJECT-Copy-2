import google.generativeai as genai
import pandas as pd
import os

# Load API key
def load_api_key():
    try:
        # Check for gemini_key.txt
        if os.path.exists("gemini_key.txt"):
            with open("gemini_key.txt", "r") as f:
                return f.read().strip()
        # Fallback to openai_key.txt if user put it there by mistake, or just return None
        elif os.path.exists("openai_key.txt"):
             with open("openai_key.txt", "r") as f:
                return f.read().strip()
        return None
    except Exception:
        return None

api_key = load_api_key()
if api_key:
    genai.configure(api_key=api_key)


# -----------------------------------------------------------
# Function 1: Predict Congestion Risk
# -----------------------------------------------------------
def predict_congestion(df, future_load):
    """
    Predicts congestion using historical utilization and future load.
    Fully compatible with processed_data.csv column names.
    """

    # --- 1) Historical Utilization ---
    historical_util = df["utilization_rho"].mean()

    # --- 2) Determine max capacity dynamically ---
    if "effective_throughput_MBps" in df.columns:
        max_capacity = df["effective_throughput_MBps"].max()

    elif "throughput_MBps" in df.columns:
        max_capacity = df["throughput_MBps"].max()

    elif "throughput_Mbps" in df.columns:
        max_capacity = df["throughput_Mbps"].max() / 8  # convert Mbps → MB/s

    else:
        # Extreme fallback
        max_capacity = df["load_MBps"].max()

    if max_capacity <= 0:
        max_capacity = 1

    # --- 3) Estimate future utilization ---
    future_util = future_load / max_capacity

    # Weighted model: 50% past + 50% future
    combined_util = 0.5 * historical_util + 0.5 * future_util

    # --- 4) Congestion status ---
    if combined_util < 0.4:
        return "Low congestion expected. Safe for heavy backups."

    elif combined_util < 0.7:
        return "Medium congestion expected. Consider staggering backup jobs."

    else:
        return "⚠ High congestion risk! Avoid backup-heavy operations."


# -----------------------------------------------------------
# Function 2: Generate LLM Insights
# -----------------------------------------------------------
def generate_llm_insights(df, scenario, enc):
    # Convert a small portion of data to CSV for LLM context
    snippet = df.head(20).to_csv(index=False)

    prompt = f"""
    You are an expert storage engineer.

    Here are SAN performance metrics:
    {snippet}

    Scenario: {scenario}
    Encryption enabled: {enc}

    Analyze and return:
    1. Throughput stability summary
    2. Latency behavior
    3. Impact of encryption
    4. Backup window recommendations
    5. Whether improved SAN (FC) is better here
    """

    # Call Gemini Pro
    model = genai.GenerativeModel('gemini-flash-latest')
    response = model.generate_content(prompt)

    return response.text


def run_llm(df, scenario, encryption):
    """
    Wrapper function so app.py can call a single LLM interface.
    Produces insights using generate_llm_insights().
    """

    try:
        if not api_key:
            return "⚠️ Missing API Key. Please create 'gemini_key.txt' with your Google Gemini API key."
            
        insights = generate_llm_insights(df, scenario, encryption)
        return insights

    except Exception as e:
        return f"LLM Error: {str(e)}"
