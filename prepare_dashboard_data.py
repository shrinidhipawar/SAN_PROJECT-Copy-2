import pandas as pd
import os

print("=" * 60)
print("DATA INTEGRATION: Phase 2 Simulator → Dashboard")
print("=" * 60)

# Load Phase 2 simulation results
print("\n1. Loading sim_results_phase2.csv...")
df = pd.read_csv("sim_results_phase2.csv")
print(f"   ✓ Loaded {len(df)} rows")

# Rename columns to match dashboard expectations
print("\n2. Renaming columns for dashboard compatibility...")
df = df.rename(columns={
    "timestamp": "time",
    "latency_s": "total_delay_s"
})

# Map encryption boolean to readable labels
print("\n3. Converting encryption labels...")
df["encryption"] = df["encryption"].map({
    True: "AES-256",
    False: "No Encryption"
})

# Add utilization_rho column (required by dashboard)
print("\n4. Calculating utilization_rho...")
# Estimate utilization based on load and effective throughput
df["utilization_rho"] = df["load_MBps"] / (df["effective_throughput_MBps"] + 1e-9)
df["utilization_rho"] = df["utilization_rho"].clip(upper=0.999)  # Cap at 0.999

# Verify required columns exist
required_cols = ["time", "scenario", "encryption", "effective_throughput_MBps", 
                 "total_delay_s", "utilization_rho"]
missing_cols = [col for col in required_cols if col not in df.columns]

if missing_cols:
    print(f"\n   ⚠️  Warning: Missing columns: {missing_cols}")
else:
    print(f"   ✓ All required columns present")

# Save to dashboard data directory
output_path = "dashboard/data/processed_data.csv"
print(f"\n5. Saving to {output_path}...")
os.makedirs("dashboard/data", exist_ok=True)
df.to_csv(output_path, index=False)
print(f"   ✓ Saved {len(df)} rows")

print("\n" + "=" * 60)
print("DATA INTEGRATION COMPLETE!")
print("=" * 60)
print("\nColumn mapping:")
print("  timestamp → time")
print("  latency_s → total_delay_s")
print("  encryption: True/False → AES-256/No Encryption")
print("\nAdded columns:")
print("  utilization_rho (calculated)")
print("\nDashboard is now ready to use with Phase 2 data!")
print("=" * 60)
