import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style for better-looking plots
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

# ========================================
# ENHANCED ENCRYPTION MODEL
# ========================================

def simulate_san_with_encryption(
        scenario_name,
        bandwidth_MBps,
        encryption_enabled=False,
        duration_seconds=60,
        base_latency_ms=0.2,
        cpu_cost_per_MB_ms=0.15,  # CPU processing cost: 0.05-0.3 ms per MB
        packet_overhead_pct=0.02   # 2% packet overhead
    ):
    """
    Enhanced SAN simulation with realistic encryption overhead model.
    
    Encryption Model:
    - CPU cost: configurable ms per MB (default 0.15ms)
    - Packet overhead: 2% additional data
    - Processing delay applied before queuing
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
        # Generate varying load pattern
        if t < 15:
            load = np.random.uniform(50, 150)    # low load
        elif t < 30:
            load = np.random.uniform(200, 350)   # medium load
        elif t < 45:
            load = np.random.uniform(400, 600)   # high load
        else:
            load = np.random.uniform(100, 700)   # random spikes
        
        timestamp_list.append(t)
        
        # Apply packet overhead if encryption is enabled
        if encryption_enabled:
            actual_load = load * (1 + packet_overhead_pct)  # 2% more data
        else:
            actual_load = load
            
        load_list.append(load)
        
        # Compute utilization
        rho = actual_load / bandwidth_MBps
        rho = min(rho, 0.999)   # avoid infinity
        
        # Queue delay (M/M/1)
        queue_delay = rho / (1 - rho)
        
        # CPU processing delay for encryption (applied before queuing)
        if encryption_enabled:
            enc_delay = (load * cpu_cost_per_MB_ms) / 1000  # convert ms to seconds
        else:
            enc_delay = 0
        
        # Total latency = base + encryption processing + queue delay
        latency = (base_latency_ms / 1000) + enc_delay + queue_delay
        
        # Throughput & Packet Loss
        if actual_load > bandwidth_MBps:
            loss = (actual_load - bandwidth_MBps) / actual_load
            throughput = bandwidth_MBps * (1 - loss)
        else:
            loss = 0
            throughput = actual_load
        
        # Effective throughput (accounting for packet overhead)
        if encryption_enabled:
            effective_throughput = throughput / (1 + packet_overhead_pct)
        else:
            effective_throughput = throughput
        
        # Append values
        throughput_list.append(throughput)
        latency_list.append(latency)
        queue_delay_list.append(queue_delay)
        enc_delay_list.append(enc_delay)
        loss_list.append(loss)
        eff_throughput_list.append(max(effective_throughput, 0))
    
    # Build DataFrame
    df = pd.DataFrame({
        "timestamp": timestamp_list,
        "scenario": scenario_name,
        "encryption": "AES-256" if encryption_enabled else "No Encryption",
        "load_MBps": load_list,
        "throughput_MBps": throughput_list,
        "effective_throughput_MBps": eff_throughput_list,
        "latency_s": latency_list,
        "queue_delay_s": queue_delay_list,
        "encryption_delay_s": enc_delay_list,
        "packet_loss": loss_list
    })
    
    return df


# ========================================
# RUN SIMULATIONS
# ========================================

print("=" * 60)
print("PHASE 6: ENCRYPTION OVERHEAD ANALYSIS")
print("=" * 60)
print("\nRunning simulations with enhanced encryption model...")
print("- CPU cost per MB: 0.15 ms")
print("- Packet overhead: 2%")
print("- Processing delay: Applied before queuing\n")

scenarios = []

# Traditional SAN (Ethernet 1 Gbps = 125 MB/s)
print("Simulating Traditional SAN (Ethernet 1 Gbps)...")
scenarios.append(simulate_san_with_encryption("Traditional SAN", 125, False))
scenarios.append(simulate_san_with_encryption("Traditional SAN", 125, True))

# Improved SAN (FC 16 Gbps = 2000 MB/s)
print("Simulating Improved SAN (FC 16 Gbps)...")
scenarios.append(simulate_san_with_encryption("Improved SAN (FC)", 2000, False))
scenarios.append(simulate_san_with_encryption("Improved SAN (FC)", 2000, True))

# Combine all results
df_all = pd.concat(scenarios, ignore_index=True)

print("\nSimulations complete!")
print(f"Total data points: {len(df_all)}")


# ========================================
# CALCULATE SUMMARY METRICS
# ========================================

print("\n" + "=" * 60)
print("CALCULATING SUMMARY METRICS")
print("=" * 60)

summary_metrics = []

for scenario in df_all['scenario'].unique():
    for enc in df_all['encryption'].unique():
        subset = df_all[(df_all['scenario'] == scenario) & (df_all['encryption'] == enc)]
        
        metrics = {
            'Scenario': scenario,
            'Encryption': enc,
            'Avg_Throughput_MBps': subset['effective_throughput_MBps'].mean(),
            'Max_Throughput_MBps': subset['effective_throughput_MBps'].max(),
            'Min_Throughput_MBps': subset['effective_throughput_MBps'].min(),
            'Avg_Latency_ms': subset['latency_s'].mean() * 1000,
            'Max_Latency_ms': subset['latency_s'].max() * 1000,
            'Avg_Encryption_Delay_ms': subset['encryption_delay_s'].mean() * 1000,
            'Avg_Packet_Loss_pct': subset['packet_loss'].mean() * 100
        }
        summary_metrics.append(metrics)

df_summary = pd.DataFrame(summary_metrics)

# Calculate degradation percentages
degradation_data = []
for scenario in df_all['scenario'].unique():
    baseline = df_summary[(df_summary['Scenario'] == scenario) & 
                          (df_summary['Encryption'] == 'No Encryption')]['Avg_Throughput_MBps'].values[0]
    encrypted = df_summary[(df_summary['Scenario'] == scenario) & 
                           (df_summary['Encryption'] == 'AES-256')]['Avg_Throughput_MBps'].values[0]
    
    baseline_latency = df_summary[(df_summary['Scenario'] == scenario) & 
                                   (df_summary['Encryption'] == 'No Encryption')]['Avg_Latency_ms'].values[0]
    encrypted_latency = df_summary[(df_summary['Scenario'] == scenario) & 
                                    (df_summary['Encryption'] == 'AES-256')]['Avg_Latency_ms'].values[0]
    
    throughput_degradation = ((baseline - encrypted) / baseline) * 100
    latency_inflation = ((encrypted_latency - baseline_latency) / baseline_latency) * 100
    
    degradation_data.append({
        'Scenario': scenario,
        'Throughput_Degradation_pct': throughput_degradation,
        'Latency_Inflation_pct': latency_inflation
    })

df_degradation = pd.DataFrame(degradation_data)

# Calculate backup window estimates for different backup sizes
backup_sizes_GB = [1000, 5000, 10000]  # 1TB, 5TB, 10TB
backup_window_data = []

for scenario in df_all['scenario'].unique():
    for enc in df_all['encryption'].unique():
        avg_throughput = df_summary[(df_summary['Scenario'] == scenario) & 
                                     (df_summary['Encryption'] == enc)]['Avg_Throughput_MBps'].values[0]
        
        for size_GB in backup_sizes_GB:
            size_MB = size_GB * 1024
            time_seconds = size_MB / avg_throughput
            time_hours = time_seconds / 3600
            
            backup_window_data.append({
                'Scenario': scenario,
                'Encryption': enc,
                'Backup_Size_TB': size_GB / 1000,
                'Backup_Time_hours': time_hours
            })

df_backup_windows = pd.DataFrame(backup_window_data)

# Save summary metrics
df_summary.to_csv('encryption_metrics_summary.csv', index=False)
df_degradation.to_csv('encryption_degradation_summary.csv', index=False)
df_backup_windows.to_csv('backup_window_estimates.csv', index=False)

print("\n✓ Summary metrics saved to:")
print("  - encryption_metrics_summary.csv")
print("  - encryption_degradation_summary.csv")
print("  - backup_window_estimates.csv")

print("\n" + "-" * 60)
print("PERFORMANCE DEGRADATION SUMMARY")
print("-" * 60)
print(df_degradation.to_string(index=False))


# ========================================
# GENERATE VISUALIZATIONS
# ========================================

print("\n" + "=" * 60)
print("GENERATING VISUALIZATIONS")
print("=" * 60)

# Create output directory
os.makedirs('encryption_analysis_plots', exist_ok=True)

# ----------------------------------------
# Plot 1: Throughput Comparison (Bar Chart)
# ----------------------------------------
print("\n1. Creating throughput comparison bar chart...")

plt.figure(figsize=(12, 6))
throughput_data = df_summary.pivot(index='Scenario', columns='Encryption', values='Avg_Throughput_MBps')
ax = throughput_data.plot(kind='bar', width=0.7, color=['#2ecc71', '#e74c3c'])
plt.title('Baseline vs Encrypted Throughput Comparison', fontsize=16, fontweight='bold')
plt.xlabel('SAN Architecture', fontsize=12)
plt.ylabel('Average Throughput (MB/s)', fontsize=12)
plt.legend(title='Encryption Status', fontsize=10)
plt.xticks(rotation=0)
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('encryption_analysis_plots/throughput_comparison.png', dpi=300, bbox_inches='tight')
print("   ✓ Saved: encryption_analysis_plots/throughput_comparison.png")
plt.close()

# ----------------------------------------
# Plot 2: Latency Inflation Curve
# ----------------------------------------
print("2. Creating latency inflation curve...")

plt.figure(figsize=(14, 6))
for scenario in df_all['scenario'].unique():
    for enc in df_all['encryption'].unique():
        subset = df_all[(df_all['scenario'] == scenario) & (df_all['encryption'] == enc)]
        label = f"{scenario} - {enc}"
        linestyle = '-' if enc == 'No Encryption' else '--'
        plt.plot(subset['timestamp'], subset['latency_s'] * 1000, 
                label=label, linestyle=linestyle, linewidth=2)

plt.title('Latency Inflation: Baseline vs Encrypted', fontsize=16, fontweight='bold')
plt.xlabel('Time (seconds)', fontsize=12)
plt.ylabel('Latency (ms)', fontsize=12)
plt.legend(fontsize=9, loc='best')
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('encryption_analysis_plots/latency_inflation.png', dpi=300, bbox_inches='tight')
print("   ✓ Saved: encryption_analysis_plots/latency_inflation.png")
plt.close()

# ----------------------------------------
# Plot 3: Backup Window Increase
# ----------------------------------------
print("3. Creating backup window comparison...")

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
backup_sizes = [1, 5, 10]  # TB

for idx, size_tb in enumerate(backup_sizes):
    ax = axes[idx]
    subset = df_backup_windows[df_backup_windows['Backup_Size_TB'] == size_tb]
    pivot_data = subset.pivot(index='Scenario', columns='Encryption', values='Backup_Time_hours')
    pivot_data.plot(kind='bar', ax=ax, width=0.7, color=['#3498db', '#e67e22'])
    ax.set_title(f'{size_tb} TB Backup', fontsize=14, fontweight='bold')
    ax.set_xlabel('SAN Architecture', fontsize=11)
    ax.set_ylabel('Backup Time (hours)', fontsize=11)
    ax.legend(title='Encryption', fontsize=9)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    ax.grid(axis='y', alpha=0.3)

plt.suptitle('Backup Window Increase with Encryption', fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('encryption_analysis_plots/backup_window_increase.png', dpi=300, bbox_inches='tight')
print("   ✓ Saved: encryption_analysis_plots/backup_window_increase.png")
plt.close()

# ----------------------------------------
# Plot 4: Encryption Overhead Summary
# ----------------------------------------
print("4. Creating encryption overhead summary...")

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Subplot 1: Throughput degradation
ax1 = axes[0, 0]
df_degradation.plot(x='Scenario', y='Throughput_Degradation_pct', kind='bar', 
                    ax=ax1, color='#e74c3c', legend=False)
ax1.set_title('Throughput Degradation (%)', fontsize=13, fontweight='bold')
ax1.set_xlabel('SAN Architecture', fontsize=11)
ax1.set_ylabel('Degradation (%)', fontsize=11)
ax1.set_xticklabels(ax1.get_xticklabels(), rotation=0)
ax1.grid(axis='y', alpha=0.3)

# Subplot 2: Latency inflation
ax2 = axes[0, 1]
df_degradation.plot(x='Scenario', y='Latency_Inflation_pct', kind='bar', 
                    ax=ax2, color='#f39c12', legend=False)
ax2.set_title('Latency Inflation (%)', fontsize=13, fontweight='bold')
ax2.set_xlabel('SAN Architecture', fontsize=11)
ax2.set_ylabel('Inflation (%)', fontsize=11)
ax2.set_xticklabels(ax2.get_xticklabels(), rotation=0)
ax2.grid(axis='y', alpha=0.3)

# Subplot 3: Average encryption delay
ax3 = axes[1, 0]
enc_delay_data = df_summary[df_summary['Encryption'] == 'AES-256']
enc_delay_data.plot(x='Scenario', y='Avg_Encryption_Delay_ms', kind='bar', 
                    ax=ax3, color='#9b59b6', legend=False)
ax3.set_title('Average Encryption Processing Delay', fontsize=13, fontweight='bold')
ax3.set_xlabel('SAN Architecture', fontsize=11)
ax3.set_ylabel('Delay (ms)', fontsize=11)
ax3.set_xticklabels(ax3.get_xticklabels(), rotation=0)
ax3.grid(axis='y', alpha=0.3)

# Subplot 4: Packet loss comparison
ax4 = axes[1, 1]
loss_data = df_summary.pivot(index='Scenario', columns='Encryption', values='Avg_Packet_Loss_pct')
loss_data.plot(kind='bar', ax=ax4, width=0.7, color=['#1abc9c', '#e74c3c'])
ax4.set_title('Packet Loss Comparison', fontsize=13, fontweight='bold')
ax4.set_xlabel('SAN Architecture', fontsize=11)
ax4.set_ylabel('Packet Loss (%)', fontsize=11)
ax4.legend(title='Encryption', fontsize=9)
ax4.set_xticklabels(ax4.get_xticklabels(), rotation=0)
ax4.grid(axis='y', alpha=0.3)

plt.suptitle('Encryption Overhead Summary Dashboard', fontsize=16, fontweight='bold', y=0.995)
plt.tight_layout()
plt.savefig('encryption_analysis_plots/encryption_overhead_summary.png', dpi=300, bbox_inches='tight')
print("   ✓ Saved: encryption_analysis_plots/encryption_overhead_summary.png")
plt.close()

print("\n" + "=" * 60)
print("PHASE 6 COMPLETE!")
print("=" * 60)
print("\n✓ All visualizations generated successfully!")
print("\nDeliverables:")
print("  📊 4 visualization plots in 'encryption_analysis_plots/'")
print("  📈 3 summary CSV files with performance metrics")
print("\nKey Findings:")
print(f"  • Traditional SAN throughput degradation: {df_degradation[df_degradation['Scenario']=='Traditional SAN']['Throughput_Degradation_pct'].values[0]:.2f}%")
print(f"  • Improved SAN throughput degradation: {df_degradation[df_degradation['Scenario']=='Improved SAN (FC)']['Throughput_Degradation_pct'].values[0]:.2f}%")
print(f"  • Traditional SAN latency inflation: {df_degradation[df_degradation['Scenario']=='Traditional SAN']['Latency_Inflation_pct'].values[0]:.2f}%")
print(f"  • Improved SAN latency inflation: {df_degradation[df_degradation['Scenario']=='Improved SAN (FC)']['Latency_Inflation_pct'].values[0]:.2f}%")
print("\n" + "=" * 60)
