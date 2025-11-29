import pandas as pd
import os
from dashboard.modules.llm import run_llm, load_api_key

# Create dummy data
data = {
    "throughput_MBps": [100, 120, 110, 130, 90],
    "latency_ms": [5, 6, 5, 7, 4],
    "utilization_rho": [0.5, 0.6, 0.55, 0.65, 0.45]
}
df = pd.DataFrame(data)

# Check if key exists
key = load_api_key()
if not key:
    print("No API key found. Please create 'gemini_key.txt' with your Google Gemini API key.")
    # We can't really test further without a key
else:
    print(f"Found API key: {key[:4]}...{key[-4:]}")
    print("Testing run_llm with Gemini...")
    try:
        result = run_llm(df, "Test Scenario", "OFF")
        print("\n--- Result ---")
        print(result)
        
        if "LLM Error" not in result and "Missing API Key" not in result:
            print("\nSUCCESS: Gemini response generated.")
        else:
            print("\nFAILURE: Gemini response failed.")
            
    except Exception as e:
        print(f"\nERROR: Script failed with {e}")
