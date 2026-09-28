# Network Structure Analysis

## Overview
- **Total Observations**: 60355
- **Unique Source IPs**: 6605
- **Unique Destination IPs**: 7059
- **Total Peers (Src+Dst)**: 7468

## Peer Heterogeneity
- **Peer Reuse Count**: 7107 peers appeared in >1 TX.
- **Peer Reuse Distribution**: {"1": 361, "2-5": 3478, "6-20": 1916, "21-100": 1663, ">100": 50}
- **Transactions/Peer (Min/Med/Max)**: 1 / 5 / 268

## Transaction Propagation
- **Observations/TX Distribution**: {"1": 10295, "2": 7576, "3": 3914, "4": 0, "5": 2582, "6-8": 1282}

## Graph Connectivity
- **Connected Component Count**: 3
- **Largest Component Size**: 4916
- **Component Size Distribution**: {"1": 0, "2-5": 1, "6-50": 0, ">50": 2}

## Feature Readiness
Meaningful variance EXISTS in the required network features:

### 1. Unique IP Propagators (`unique_ip_propagators`)
- **Min / Median / Max**: 1 / 1 / 8
- **Variance**: 1.40

### 2. Propagation Edge Count (`propagation_edge_count`)
- **Min / Median / Max**: 1 / 2 / 8
- **Variance**: 3.13

### 3. Duration Active Seconds (`duration_active_seconds`)
- **Min / Median / Max**: 0.00 / 158.00 / 600.00
- **Variance**: 20878.88
