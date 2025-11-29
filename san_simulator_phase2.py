import numpy as np
import pandas as pd
import time

# ----------------------------------------
# SAN Simulation Function (Improved)
# ----------------------------------------

def simulate_san(
        scenario_name,
        bandwidth_MBps,
        encryption_enabled=False,
        duration_seconds=60,
        base_latency_ms=0.2
    ):
    """
    Simulates SAN performance for 60 seconds with varying load.
    """

    timestamp_list = []
    load_list = []
    throughput_list = []
    latency_list = []
    queue_delay_list = []
    enc_delay_list = []
    loss_list = []
    eff_throughput_list = []

    for t in range(duration_seconds):

        # -------------------------------
        # Generate varying load pattern:
        # low, medium, high + random spikes
        # -------------------------------

        if t < 15:
            load = np.random.uniform(50, 150)    # low load
        elif t < 30:
            load = np.random.uniform(200, 350)   # medium load
        elif t < 45:
            load = np.random.uniform(400, 600)   # high load
        else:
            load = np.random.uniform(100, 700)   # random spikes

        # Store timestamp
        timestamp_list.append(t)
        load_list.append(load)

        # -------------------------------
        # Compute utilization
        # -------------------------------
        rho = load / bandwidth_MBps
        rho = min(rho, 0.999)   # avoid infinity

        # -------------------------------
        # Queue delay (M/M/1)
        # -------------------------------
        queue_delay = rho / (1 - rho)

        # -------------------------------
        # Transmission latency
        # -------------------------------
        latency = base_latency_ms / 1000 + queue_delay

        # -------------------------------
        # Encryption overhead
        # -------------------------------
        if encryption_enabled:
            enc_delay = load * 0.0005   # 0.5 ms per MB
        else:
            enc_delay = 0

        # -------------------------------
        # Throughput & Packet Loss
        # -------------------------------
        if load > bandwidth_MBps:
            loss = (load - bandwidth_MBps) / load
            throughput = bandwidth_MBps * (1 - loss)
        else:
            loss = 0
            throughput = load

        effective_throughput = throughput - (enc_delay * 10)

        # Append values
        throughput_list.append(throughput)
        latency_list.append(latency)
        queue_delay_list.append(queue_delay)
        enc_delay_list.append(enc_delay)
        loss_list.append(loss)
        eff_throughput_list.append(max(effective_throughput, 0))

    # ---------------------------------
    # Build DataFrame
    # ---------------------------------

    df = pd.DataFrame({
        "timestamp": timestamp_list,
        "scenario": scenario_name,
        "encryption": encryption_enabled,
        "load_MBps": load_list,
        "throughput_MBps": throughput_list,
        "effective_throughput_MBps": eff_throughput_list,
        "latency_s": latency_list,
        "queue_delay_s": queue_delay_list,
        "encryption_delay_s": enc_delay_list,
        "packet_loss": loss_list
    })

    return df


# ----------------------------------------
# Run all 4 scenarios
# ----------------------------------------

print("Running Phase 2 SAN simulations...")

scenarios = []

# Traditional SAN (Ethernet 1 Gbps = 125 MB/s)
scenarios.append(simulate_san("Traditional", 125, False))
scenarios.append(simulate_san("Traditional", 125, True))

# Improved SAN (FC 16 Gbps = 2000 MB/s)
scenarios.append(simulate_san("Improved_SAN_FC", 2000, False))
scenarios.append(simulate_san("Improved_SAN_FC", 2000, True))

# Combine all results
final_df = pd.concat(scenarios, ignore_index=True)

# Save results
final_df.to_csv("sim_results_phase2.csv", index=False)

print("Completed Phase 2.")
print("Saved -> sim_results_phase2.csv")
print(final_df.head())
