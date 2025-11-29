import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv("sim_results_phase2.csv")

# Throughput vs time
plt.figure(figsize=(10,5))
sns.lineplot(data=df, x="timestamp", y="throughput_MBps", hue="scenario")
plt.title("Throughput vs Time")
plt.tight_layout()
plt.show()

# Latency vs Load
plt.figure(figsize=(10,5))
sns.scatterplot(data=df, x="load_MBps", y="latency_s", hue="scenario")
plt.title("Latency vs Load")
plt.tight_layout()
plt.show()
