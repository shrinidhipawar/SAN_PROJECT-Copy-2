#!/usr/bin/env python3
"""
san_simulator.py

Discrete-time SAN-level simulator (M/M/1 style) for comparing:
 - Traditional SAN (Ethernet 1 Gbps)
 - Improved SAN (Fibre-Channel-like 16 Gbps)

Models:
 - Offered load (MB/s)
 - Queue delay using M/M/1 formulas
 - Encryption overhead (ms per MB)
 - Packetization overhead (increase in packet size)
 - Congestion spikes

Outputs:
 - CSV per-run with time-series metrics
 - Summary printed to console

Usage examples:
  python san_simulator.py --scenario ethernet --encryption 0 --duration 600 --dt 0.1 --out sim_ethernet_noenc.csv
  python san_simulator.py --scenario fc --encryption 1 --duration 600 --dt 0.1 --out sim_fc_enc.csv

Requirements:
  pip install numpy pandas
"""

import argparse
import math
import numpy as np
import pandas as pd
import json
from datetime import datetime

# ----------------------------
# DEFAULT SIM PARAMETERS
# ----------------------------
DEFAULT_PACKET_BYTES = 1500  # bytes (baseline)
DEFAULT_PACKET_OVERHEAD_FRAC = 0.02  # 2% packetization overhead by default
DEFAULT_ENC_MS_PER_MB = 0.12  # ms per MB of data for AES-256 processing (tunable; example)
# Explanation: if enc_ms_per_mb = 0.12 ms/MB => encrypting 1 MB adds 0.12 ms processing
# So for a packet of size 1500 bytes (0.0015 MB), enc delay per packet = 0.0015 * 0.12 ms = 0.00018 ms.

# Link capacities (bps)
LINK_CAPACITIES = {
    "ethernet": 1_000_000_000,   # 1 Gbps
    "fc":       16_000_000_000,  # 16 Gbps (FC-like)
}

# ----------------------------
# HELPER MATH (explicit, careful)
# ----------------------------

def mbps_to_bps(mbps):
    # Accept MB/s as float (MB per second). Convert MB/s -> bits/s
    # 1 MB = 1e6 bytes = 8e6 bits
    return mbps * 8e6

def bps_to_mb_s(bps):
    # Convert bits/s -> MB/s (1 MB = 1e6 bytes)
    return bps / 8e6

def offered_mb_s_to_packet_rate(offered_mb_s, packet_bytes, pkt_overhead_frac):
    """
    Convert offered traffic MB/s into packet arrival rate lambda (packets/sec).
    Steps:
      1. offered_MBps -> offered bits/s: offered_bits_s = offered_MBps * 8e6
      2. effective_packet_size_bytes = packet_bytes * (1 + pkt_overhead_frac)
      3. packet_size_bits = effective_packet_size_bytes * 8
      4. lambda = offered_bits_s / packet_size_bits
    """
    offered_bits_s = offered_mb_s * 8e6  # careful conversion: MB/s -> bits/s
    eff_packet_bytes = packet_bytes * (1.0 + pkt_overhead_frac)
    packet_bits = eff_packet_bytes * 8.0
    if packet_bits <= 0:
        return 0.0
    lam = offered_bits_s / packet_bits  # packets/sec
    return lam

def compute_service_rate(capacity_bps, packet_bytes, pkt_overhead_frac, enc_ms_per_mb):
    """
    Compute service rate mu (packets/sec) given link capacity and per-MB encryption cost.

    Steps (explicit):
      1. eff_packet_bytes = packet_bytes * (1 + pkt_overhead_frac)
      2. service_time_for_packet_without_enc = (eff_packet_bytes * 8) / capacity_bps  (seconds)
      3. encryption_delay_per_packet = (eff_packet_bytes / 1e6) * enc_ms_per_mb / 1000  (seconds)
         (because enc_ms_per_mb is ms per MB)
      4. total_service_time = service_time_without_enc + encryption_delay_per_packet
      5. mu = 1 / total_service_time
    """
    eff_packet_bytes = packet_bytes * (1.0 + pkt_overhead_frac)
    service_time_no_enc = (eff_packet_bytes * 8.0) / float(capacity_bps)  # seconds per packet
    if enc_ms_per_mb <= 0:
        enc_delay_sec = 0.0
    else:
        enc_delay_sec = (eff_packet_bytes / 1e6) * (enc_ms_per_mb / 1000.0)  # convert ms -> s
    total_service_time = service_time_no_enc + enc_delay_sec
    if total_service_time <= 0:
        return float('inf')  # infinite service rate (degenerate)
    mu = 1.0 / total_service_time
    return mu, service_time_no_enc, enc_delay_sec

def mm1_metrics(lam, mu):
    """
    Given arrival rate lambda (packets/sec) and service rate mu (packets/sec),
    compute:
      - utilization rho = lam / mu
      - average time in system W = 1 / (mu - lam)  [includes service time]
      - average waiting time Wq = lam / (mu * (mu - lam))
      - average service time S = 1 / mu
    If lam >= mu, metrics indicate congestion; we will return large values and loss.
    """
    if mu <= 0.0:
        return {
            "rho": float('nan'),
            "W": float('inf'),
            "Wq": float('inf'),
            "S": float('inf')
        }
    rho = lam / mu
    if lam >= mu:
        # system unstable; queue grows unbounded in theory. We return sentinel large values.
        return {
            "rho": rho,
            "W": float('inf'),
            "Wq": float('inf'),
            "S": 1.0 / mu
        }
    S = 1.0 / mu
    W = 1.0 / (mu - lam)
    Wq = W - S  # same as lam / (mu * (mu - lam))
    return {
        "rho": rho,
        "W": W,
        "Wq": Wq,
        "S": S
    }

# ----------------------------
# OFFERED LOAD / SPIKES GENERATOR
# ----------------------------

def generate_offered_load_profile(duration_s, dt, base_mb_s, peak_mb_s, spike_times=None, spike_duration=10.0, spike_shape="gaussian", noise_level=0.0, seed=None):
    """
    Generate a time series (numpy array) of offered load in MB/s sampled at dt seconds.
    - base_mb_s: baseline offered load (MB/s)
    - peak_mb_s: peak offered load (MB/s) for scheduled backups
    - spike_times: list of time offsets (s) where a spike occurs (e.g., [120, 360])
    - spike_duration: width of spike in seconds (for gaussian or rectangular)
    - spike_shape: "gaussian" or "rect"
    - noise_level: relative noise amplitude (e.g., 0.05)
    """
    if seed is not None:
        np.random.seed(seed)
    t = np.arange(0.0, duration_s + 1e-9, dt)
    profile = np.ones_like(t) * base_mb_s
    # Add scheduled backup ramp: we'll create a larger plateau in middle of simulation
    # If peak_mb_s > base_mb_s, ramp up to peak for a period (e.g., center 20% of duration)
    center = duration_s / 2.0
    ramp_width = max(10.0, 0.2 * duration_s)
    ramp_mask = np.abs(t - center) < (ramp_width / 2.0)
    profile[ramp_mask] = np.maximum(profile[ramp_mask], peak_mb_s)
    # Add spikes
    if spike_times:
        for st in spike_times:
            if spike_shape == "gaussian":
                sigma = spike_duration / 4.0
                spike = peak_mb_s * np.exp(-0.5 * ((t - st) / sigma) ** 2)
                profile += spike
            else:
                # rectangular spike
                mask = (t >= st) & (t < st + spike_duration)
                profile[mask] += peak_mb_s
    # Add some noise
    if noise_level and noise_level > 0.0:
        noise = np.random.normal(loc=0.0, scale=noise_level * base_mb_s, size=profile.shape)
        profile += noise
        profile = np.maximum(profile, 0.0)
    return t, profile

# ----------------------------
# SIMULATION RUN
# ----------------------------

def run_simulation(scenario="ethernet",
                   duration_s=600.0,
                   dt=0.1,
                   packet_bytes=DEFAULT_PACKET_BYTES,
                   pkt_overhead_frac=DEFAULT_PACKET_OVERHEAD_FRAC,
                   enc_enabled=False,
                   enc_ms_per_mb=DEFAULT_ENC_MS_PER_MB,
                   base_mb_s=10.0,
                   peak_mb_s=400.0,
                   spike_times=None,
                   spike_duration=8.0,
                   noise_level=0.02,
                   out_csv="sim_results.csv",
                   verbose=True):
    """
    Run the time-stepped simulation and write results to out_csv.
    """
    # 1) get capacity
    if scenario not in LINK_CAPACITIES:
        raise ValueError("Unknown scenario: choose from: " + ", ".join(LINK_CAPACITIES.keys()))
    capacity_bps = LINK_CAPACITIES[scenario]

    # 2) build offered load
    t, offered_profile = generate_offered_load_profile(duration_s, dt, base_mb_s, peak_mb_s,
                                                       spike_times=spike_times,
                                                       spike_duration=spike_duration,
                                                       noise_level=noise_level)

    # 3) simulation arrays
    rows = []
    for i, time in enumerate(t):
        offered_mb_s = float(offered_profile[i])  # MB/s
        # Convert to packet arrival rate lambda
        lam = offered_mb_s_to_packet_rate(offered_mb_s, packet_bytes, pkt_overhead_frac)
        # Compute service rate mu (packets/sec) including encryption overhead if enabled
        enc_ms = enc_ms_per_mb if enc_enabled else 0.0
        mu, service_time_no_enc, enc_delay_per_pkt = compute_service_rate(capacity_bps, packet_bytes, pkt_overhead_frac, enc_ms)
        # numeric safety: if mu is a tuple None, adjust
        # mm1 metrics
        metrics = mm1_metrics(lam, mu if isinstance(mu, float) else mu[0])
        rho = metrics["rho"]
        W = metrics["W"]
        Wq = metrics["Wq"]
        S = metrics["S"]
        # Loss modeling: simple approximation:
        if lam <= 0:
            loss = 0.0
        elif lam >= (mu if isinstance(mu, float) else mu[0]):
            # saturation: significant loss (we approximate)
            loss = 0.9  # 90% of packets lost in extreme congestion (tunable)
            W = float('inf')
            Wq = float('inf')
        else:
            loss = max(0.0, (lam - (mu if isinstance(mu, float) else mu[0])) / lam)
            loss = min(max(loss, 0.0), 0.999)
        # throughput in MB/s (after loss)
        throughput_mb_s = offered_mb_s * (1.0 - loss)
        # total latency experienced per packet (seconds): W includes service time; we may want to include encryption enc_delay explicitly
        total_latency_s = W if math.isfinite(W) else None
        queue_delay_s = Wq if math.isfinite(Wq) else None
        # Utilization (rho)
        util = rho if not math.isnan(rho) else None
        # Service-time components (seconds)
        # compute service_time_no_enc and enc_delay_per_pkt via compute_service_rate call earlier; if mu is tuple
        # Note: compute_service_rate returned (mu, service_time_no_enc, enc_delay_sec) in our definition
        mu_val, service_time_without_enc, enc_delay_per_pkt = compute_service_rate(capacity_bps, packet_bytes, pkt_overhead_frac, enc_ms)
        # convert some values to human-friendly
        throughput_mbps = throughput_mb_s * 8.0  # MB/s -> Mb/s
        capacity_mbps = capacity_bps / 1e6 * 8.0 if False else (capacity_bps / 1e6) * 8.0  # <-- careful: capacity_bps is bits/s, capacity_mbps = bits/s / 1e6
        # For clarity: we will compute capacity in Gbps or Mbps separately:
        capacity_gbps = capacity_bps / 1e9
        # Append row
        rows.append({
            "time_s": time,
            "scenario": scenario,
            "encryption": int(enc_enabled),
            "offered_MB_s": offered_mb_s,
            "throughput_MB_s": throughput_mb_s,
            "throughput_Mbps": throughput_mbps,
            "capacity_Gbps": capacity_gbps,
            "packet_bytes": packet_bytes,
            "pkt_overhead_frac": pkt_overhead_frac,
            "lambda_pkts_s": lam,
            "mu_pkts_s": mu_val,
            "service_time_s": service_time_without_enc,
            "enc_delay_per_pkt_s": enc_delay_per_pkt,
            "utilization_rho": util,
            "avg_system_time_s": total_latency_s,
            "avg_queue_time_s": queue_delay_s,
            "loss_ratio": loss
        })

    # 4) Write CSV
    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)
    if verbose:
        print(f"Simulation complete. Wrote {len(df)} rows to {out_csv}")
    return df

# ----------------------------
# CLI
# ----------------------------
def parse_args():
    p = argparse.ArgumentParser(description="SAN-level Python simulator (M/M/1 approximation)")
    p.add_argument("--scenario", choices=list(LINK_CAPACITIES.keys()), default="ethernet", help="Network scenario")
    p.add_argument("--duration", type=float, default=600.0, help="Simulation duration (s)")
    p.add_argument("--dt", type=float, default=0.1, help="Time step (s)")
    p.add_argument("--packet-bytes", type=int, default=DEFAULT_PACKET_BYTES, help="Base packet size in bytes")
    p.add_argument("--pkt-overhead", type=float, default=DEFAULT_PACKET_OVERHEAD_FRAC, help="Packetization overhead fraction (e.g., 0.02 for 2%)")
    p.add_argument("--encryption", type=int, choices=[0,1], default=0, help="Enable encryption cost model (0/1)")
    p.add_argument("--enc-ms-per-mb", type=float, default=DEFAULT_ENC_MS_PER_MB, help="Encryption processing cost in ms per MB")
    p.add_argument("--base-mb-s", type=float, default=10.0, help="Base offered load in MB/s")
    p.add_argument("--peak-mb-s", type=float, default=400.0, help="Peak offered load used for scheduled backups (MB/s)")
    p.add_argument("--spike-times", type=str, default="", help="Comma-separated spike start times in seconds (e.g. '60,180,300')")
    p.add_argument("--spike-duration", type=float, default=8.0, help="Spike duration (s)")
    p.add_argument("--noise", type=float, default=0.02, help="Relative noise level")
    p.add_argument("--out", type=str, default="sim_results.csv", help="Output CSV file")
    return p.parse_args()

def main():
    args = parse_args()
    spike_times = None
    if args.spike_times:
        spike_times = [float(x.strip()) for x in args.spike_times.split(",") if x.strip() != ""]
    df = run_simulation(scenario=args.scenario,
                        duration_s=args.duration,
                        dt=args.dt,
                        packet_bytes=args.packet_bytes,
                        pkt_overhead_frac=args.pkt_overhead,
                        enc_enabled=bool(args.encryption),
                        enc_ms_per_mb=args.enc_ms_per_mb,
                        base_mb_s=args.base_mb_s,
                        peak_mb_s=args.peak_mb_s,
                        spike_times=spike_times,
                        spike_duration=args.spike_duration,
                        noise_level=args.noise,
                        out_csv=args.out,
                        verbose=True)
    # print summary (aggregate)
    try:
        print("\nSummary statistics (per-run):")
        grouped = df.groupby(["scenario","encryption"])
        for (sc,enc), g in grouped:
            avg_throughput = g["throughput_MB_s"].mean()
            max_latency = g["avg_system_time_s"].replace(np.inf, np.nan).max()
            avg_loss = g["loss_ratio"].mean()
            print(f"  Scenario={sc} enc={enc} -> avg_throughput={avg_throughput:.2f} MB/s, max_latency={max_latency:.3f} s, avg_loss={avg_loss:.3f}")
    except Exception as e:
        print("Error printing summary:", e)

if __name__ == "__main__":
    main()
