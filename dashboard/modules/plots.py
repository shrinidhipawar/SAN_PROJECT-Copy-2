import matplotlib.pyplot as plt
import seaborn as sns

sns.set(style="whitegrid")

def plot_throughput_time(df):
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=df, x="time", y="effective_throughput_MBps")
    plt.title("Throughput Over Time")
    plt.xlabel("Time (s)")
    plt.ylabel("Effective Throughput (MB/s)")
    return plt.gcf()

def plot_latency_time(df):
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=df, x="time", y="total_delay_s")
    plt.title("Latency Over Time")
    plt.xlabel("Time (s)")
    plt.ylabel("Total Delay (s)")
    return plt.gcf()

def plot_encryption_bar(df):
    plt.figure(figsize=(8, 5))
    avg_enc = df.groupby("encryption")["effective_throughput_MBps"].mean().reset_index()
    sns.barplot(data=avg_enc, x="encryption", y="effective_throughput_MBps")
    plt.title("Encryption Impact on Throughput")
    plt.ylabel("Avg Effective Throughput (MB/s)")
    return plt.gcf()
