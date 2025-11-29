import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load dataset
df = pd.read_csv("sim_results.csv")

# Use time_s directly
df = df.rename(columns={
    "time_s": "time",
    "throughput_Mbps": "throughput",
    "offered_MB_s": "load"
})

# Map encryption labels
df["encryption"] = df["encryption"].map({0: "No Encryption", 1: "AES-256"})

# Map scenario labels
df["scenario"] = df["scenario"].replace({
    "ethernet": "Traditional SAN (Ethernet)",
    "improved": "Improved SAN (Fibre Channel)"
})

sns.set(style="whitegrid", font_scale=1.2)

# ==================================
# 1️⃣ Throughput vs Time
# ==================================
plt.figure(figsize=(14, 7))
sns.lineplot(
    data=df,
    x="time",
    y="throughput",
    hue="scenario",
    style="encryption",
    linewidth=2.2
)
plt.title("Throughput vs Time")
plt.xlabel("Time (s)")
plt.ylabel("Throughput (Mbps)")
plt.tight_layout()
plt.show()


# ==================================
# 2️⃣ Latency vs Load
# ==================================
plt.figure(figsize=(14, 7))
sns.lineplot(
    data=df,
    x="load",
    y="avg_system_time_s",
    hue="scenario",
    style="encryption",
    linewidth=2.2
)
plt.title("Latency vs Load")
plt.xlabel("Load (MB/s)")
plt.ylabel("Avg System Time (s)")
plt.tight_layout()
plt.show()


# ==================================
# 3️⃣ Queue Delay vs Time
# ==================================
plt.figure(figsize=(14, 7))
sns.lineplot(
    data=df,
    x="time",
    y="avg_queue_time_s",
    hue="scenario",
    style="encryption",
    linewidth=2.2
)
plt.title("Queue Delay vs Time")
plt.xlabel("Time (s)")
plt.ylabel("Queue Delay (s)")
plt.tight_layout()
plt.show()


# ==================================
# 4️⃣ Packet Loss vs Load
# ==================================
plt.figure(figsize=(14, 7))
sns.lineplot(
    data=df,
    x="load",
    y="loss_ratio",
    hue="scenario",
    style="encryption",
    linewidth=2.2
)
plt.title("Packet Loss vs Load")
plt.xlabel("Load (MB/s)")
plt.ylabel("Loss Ratio")
plt.ylim(0, 1)
plt.tight_layout()
plt.show()

print("Phase-2 plots generated successfully!")
