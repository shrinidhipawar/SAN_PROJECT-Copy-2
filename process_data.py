import pandas as pd
import numpy as np

# ===============================
# LOAD RAW DATA
# ===============================
df = pd.read_csv("sim_results.csv")

# ===============================
# STANDARDIZE NAMES
# ===============================
df = df.rename(columns={
    "time_s": "time",
    "offered_MB_s": "load_MBps",
    "throughput_MB_s": "throughput_MBps"
})

# ===============================
# DERIVED METRICS
# ===============================

# 1. Effective throughput (MB/s)
# (Throughput reduced by loss)
df["effective_throughput_MBps"] = df["throughput_MBps"] * (1 - df["loss_ratio"])

# 2. Total delay (sec)
# queue delay + processing service time + encryption delay
df["total_delay_s"] = (
    df["avg_queue_time_s"] +
    df["service_time_s"] +
    df["enc_delay_per_pkt_s"]
)

# 3. Utilization threshold markers
df["is_congested"] = (df["utilization_rho"] > 0.7).astype(int)

# 4. Encryption readable labels
df["encryption"] = df["encryption"].map({0: "No Encryption", 1: "AES-256"})

# 5. Scenario readable names
df["scenario"] = df["scenario"].replace({
    "ethernet": "Traditional SAN (Ethernet)",
    "improved": "Improved SAN (Fibre Channel)"
})

# 6. Encryption impact (%)
df["encryption_penalty_pct"] = df.groupby("scenario")["effective_throughput_MBps"].transform(
    lambda x: 100 * (1 - x / x.max())
)

# 7. Backup window estimate (for 1000 MB backup)
TOTAL_BACKUP_MB = 1000
df["backup_time_estimate_s"] = TOTAL_BACKUP_MB / (df["effective_throughput_MBps"] + 1e-9)

# 8. Peak latency flag
latency_threshold = df["total_delay_s"].quantile(0.90)
df["high_latency"] = (df["total_delay_s"] > latency_threshold).astype(int)

# ===============================
# SAVE PROCESSED DATA
# ===============================
df.to_csv("processed_data.csv", index=False)

print("\nPHASE 3 COMPLETED SUCCESSFULLY")
print("Generated: processed_data.csv")
print(f"Rows: {len(df)}")
print("\nColumns generated:")
print(df.columns)
