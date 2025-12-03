# Project Architecture Diagram

This diagram illustrates the end-to-end flow of the SAN Optimization Project, from the mathematical simulation engine to the user-facing dashboard.

```mermaid
graph TD
    %% Nodes
    User((User))
    
    subgraph "Simulation Engine (Python)"
        TrafficGen[Traffic Generator]
        NetSim[Network Simulator<br/>M/M/1 Queue Model]
        EncModel[Encryption Model<br/>AES-256 Overhead]
        RawLogs[Raw CSV Logs<br/>sim_results_phase2.csv]
    end
    
    subgraph "Data Processing"
        DataPrep[Data Processor<br/>prepare_dashboard_data.py]
        ProcData[Processed Data<br/>dashboard/data/processed_data.csv]
    end
    
    subgraph "Intelligence Layer"
        AIMod[AI Module<br/>dashboard/modules/llm.py]
        Gemini[Google Gemini Pro API]
        Insights[Predictive Insights<br/>& Recommendations]
    end
    
    subgraph "Presentation Layer (Streamlit)"
        Dash[Interactive Dashboard<br/>dashboard/app.py]
        Plots[Performance Plots]
        Metrics[KPI Metrics]
    end

    %% Edges - Simulation Flow
    TrafficGen -->|1. Generate Load| NetSim
    NetSim -->|2. Apply Physics| EncModel
    EncModel -->|3. Calculate Latency/Throughput| RawLogs
    
    %% Edges - Data Flow
    RawLogs -->|4. Clean & Format| DataPrep
    DataPrep -->|5. Export| ProcData
    
    %% Edges - Dashboard Flow
    ProcData -->|6. Load Data| Dash
    Dash -->|7. Visualize| Plots
    Dash -->|8. Calculate| Metrics
    
    %% Edges - AI Flow
    ProcData -->|9. Analyze Metrics| AIMod
    AIMod -->|10. Query| Gemini
    Gemini -->|11. Return Analysis| Insights
    Insights -->|12. Display| Dash
    
    %% User Interaction
    Dash -->|13. Present Interface| User
    User -->|14. Select Scenarios| Dash

    %% Styling
    classDef sim fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef data fill:#fff3e0,stroke:#e65100,stroke-width:2px;
    classDef ai fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    classDef ui fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px;
    
    class TrafficGen,NetSim,EncModel,RawLogs sim;
    class DataPrep,ProcData data;
    class AIMod,Gemini,Insights ai;
    class Dash,Plots,Metrics ui;
```

## Component Breakdown

1.  **Simulation Engine**:
    *   Generates synthetic traffic patterns (Low, Medium, High, Spikes).
    *   Simulates network physics using M/M/1 queuing theory.
    *   Applies the AES-256 encryption model (CPU cost + packet overhead).

2.  **Data Processing**:
    *   Ingests raw simulation logs.
    *   Standardizes column names and calculates derived metrics (e.g., Utilization).
    *   Prepares data for the dashboard.

3.  **Intelligence Layer**:
    *   Monitors performance metrics in real-time.
    *   Sends context to Google Gemini Pro.
    *   Returns human-readable predictions and backup scheduling recommendations.

4.  **Presentation Layer**:
    *   **Streamlit Dashboard**: The central control plane.
    *   Visualizes throughput, latency, and encryption impact.
    *   Displays AI-generated insights to the user.
