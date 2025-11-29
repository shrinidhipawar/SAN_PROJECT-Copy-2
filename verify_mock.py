import pandas as pd
from dashboard.modules.llm import run_llm

# Create dummy data
data = {
    "throughput_MBps": [100, 120, 110, 130, 90],
    "latency_ms": [5, 6, 5, 7, 4],
    "utilization_rho": [0.5, 0.6, 0.55, 0.65, 0.45]
}
df = pd.DataFrame(data)

# Test run_llm with invalid key (should trigger fallback)
print("Testing run_llm with invalid API key...")
try:
    # Ensure openai key is invalid or missing for this test context
    import openai
    openai.api_key = "invalid_key"
    
    result = run_llm(df, "Test Scenario", "OFF")
    print("\n--- Result ---")
    print(result)
    
    if "[MOCK AI RESPONSE - API UNAVAILABLE]" in result:
        print("\nSUCCESS: Mock response generated.")
    else:
        print("\nFAILURE: Mock response NOT generated.")
        
except Exception as e:
    print(f"\nERROR: Script failed with {e}")
