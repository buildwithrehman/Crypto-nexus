# Phase 18.4 Explanation Audit

This document contains 10 real alerts from the demo run, generated using the Phase 18.4 Evidence Interpretation Layer.

## Alert 1: 999843b4b15514beef56028bb025b65bd59a750ad24cf149ac7b31d94934d58c

```text
STRUCTURAL ANOMALY

Transaction:
    999843b4b15514beef56028bb025b65bd59a750ad24cf149ac7b31d94934d58c

Anomaly Strength:
    100.0

Why it was surfaced:
    1. louvain_community (value: 8, SHAP: -1.8689)
       Meaning: Topological cluster assignment identifying distinct network communities. [ML_DERIVED]

    2. unique_ip_propagators (value: 16, SHAP: -0.8764)
       Meaning: Number of distinct peer IP addresses through which the transaction was observed. [DERIVED]

    3. propagation_edge_count (value: 16, SHAP: -0.5219)
       Meaning: Total number of network peer-to-peer propagation events recorded. [DERIVED]

Supporting evidence:
    27 distinct evidence artifacts available.

Investigation caveats:
    - Anomaly indicates structural rarity, not criminality.
    - Network observation does not establish IP ownership.
    - GeoIP enrichment is unavailable in this run.
    - Exact UTXO lineage cannot be established without prev_txid/prev_vout fields.

Evidence provenance:
    - data/demo_v1/network/observations_fast.csv:3303
    - data/demo_v1/network/observations_fast.csv:3296
    - data/demo_v1/network/observations_fast.csv:3300
    - ... and 5 more.
```

### Raw Evidence Trace
- **louvain_community**: value 8.0 -> shap -1.8689127174288198 (ML_DERIVED)
- **unique_ip_propagators**: value 16.0 -> shap -0.8764119605393725 (DERIVED)
- **propagation_edge_count**: value 16.0 -> shap -0.5218871239880215 (DERIVED)

---

## Alert 2: 3bd4eb3073d10bbf8b65a44ba00cfe0a42b871358eda08d64243b66f3ce2ded6

```text
STRUCTURAL ANOMALY

Transaction:
    3bd4eb3073d10bbf8b65a44ba00cfe0a42b871358eda08d64243b66f3ce2ded6

Anomaly Strength:
    99.95

Why it was surfaced:
    1. louvain_community (value: 38, SHAP: -1.5710)
       Meaning: Topological cluster assignment identifying distinct network communities. [ML_DERIVED]

    2. unique_ip_propagators (value: 14, SHAP: -0.7768)
       Meaning: Number of distinct peer IP addresses through which the transaction was observed. [DERIVED]

    3. propagation_edge_count (value: 16, SHAP: -0.5068)
       Meaning: Total number of network peer-to-peer propagation events recorded. [DERIVED]

Supporting evidence:
    25 distinct evidence artifacts available.

Investigation caveats:
    - Anomaly indicates structural rarity, not criminality.
    - Network observation does not establish IP ownership.
    - GeoIP enrichment is unavailable in this run.
    - Exact UTXO lineage cannot be established without prev_txid/prev_vout fields.

Evidence provenance:
    - data/demo_v1/network/observations_fast.csv:3506
    - data/demo_v1/network/observations_fast.csv:3503
    - data/demo_v1/network/observations_fast.csv:3502
    - ... and 5 more.
```

### Raw Evidence Trace
- **louvain_community**: value 38.0 -> shap -1.5710409227671576 (ML_DERIVED)
- **unique_ip_propagators**: value 14.0 -> shap -0.7768475690118484 (DERIVED)
- **propagation_edge_count**: value 16.0 -> shap -0.5067660090303833 (DERIVED)

---

## Alert 3: 4d35f62237a8bd3320a2a9f398b6d2d73207746c02f537404ccd47180d37da6d

```text
STRUCTURAL ANOMALY

Transaction:
    4d35f62237a8bd3320a2a9f398b6d2d73207746c02f537404ccd47180d37da6d

Anomaly Strength:
    99.9

Why it was surfaced:
    1. louvain_community (value: 20, SHAP: -1.2633)
       Meaning: Topological cluster assignment identifying distinct network communities. [ML_DERIVED]

    2. unique_ip_propagators (value: 14, SHAP: -0.7532)
       Meaning: Number of distinct peer IP addresses through which the transaction was observed. [DERIVED]

    3. total_degree (value: 16, SHAP: -0.5077)
       Meaning: Total number of unique addresses involved as inputs or outputs. [DERIVED]

Supporting evidence:
    25 distinct evidence artifacts available.

Investigation caveats:
    - Anomaly indicates structural rarity, not criminality.
    - Network observation does not establish IP ownership.
    - GeoIP enrichment is unavailable in this run.
    - Exact UTXO lineage cannot be established without prev_txid/prev_vout fields.

Evidence provenance:
    - data/demo_v1/network/observations_fast.csv:4583
    - data/demo_v1/network/observations_fast.csv:4588
    - data/demo_v1/network/observations_fast.csv:4587
    - ... and 5 more.
```

### Raw Evidence Trace
- **louvain_community**: value 20.0 -> shap -1.2632784955428538 (ML_DERIVED)
- **unique_ip_propagators**: value 14.0 -> shap -0.753225935998449 (DERIVED)
- **total_degree**: value 16.0 -> shap -0.5077022038664315 (DERIVED)

---

## Alert 4: 4cba62baf4820ef11e7db9a0224c3ce59aedc5e8a67d1fae06ef4bb66b5ab3e8

```text
STRUCTURAL ANOMALY

Transaction:
    4cba62baf4820ef11e7db9a0224c3ce59aedc5e8a67d1fae06ef4bb66b5ab3e8

Anomaly Strength:
    99.85000000000001

Why it was surfaced:
    1. louvain_community (value: 21, SHAP: -1.2694)
       Meaning: Topological cluster assignment identifying distinct network communities. [ML_DERIVED]

    2. unique_ip_propagators (value: 14, SHAP: -0.8387)
       Meaning: Number of distinct peer IP addresses through which the transaction was observed. [DERIVED]

    3. propagation_edge_count (value: 16, SHAP: -0.4648)
       Meaning: Total number of network peer-to-peer propagation events recorded. [DERIVED]

Supporting evidence:
    25 distinct evidence artifacts available.

Investigation caveats:
    - Anomaly indicates structural rarity, not criminality.
    - Network observation does not establish IP ownership.
    - GeoIP enrichment is unavailable in this run.
    - Exact UTXO lineage cannot be established without prev_txid/prev_vout fields.

Evidence provenance:
    - data/demo_v1/network/observations_fast.csv:1821
    - data/demo_v1/network/observations_fast.csv:1822
    - data/demo_v1/network/observations_fast.csv:1826
    - ... and 5 more.
```

### Raw Evidence Trace
- **louvain_community**: value 21.0 -> shap -1.2694145375711474 (ML_DERIVED)
- **unique_ip_propagators**: value 14.0 -> shap -0.838713340437594 (DERIVED)
- **propagation_edge_count**: value 16.0 -> shap -0.4648012560519362 (DERIVED)

---

## Alert 5: 46951cfd631ff75140c8ec38af1927909dd2e5ed4192500982b591902d7e4fbb

```text
STRUCTURAL ANOMALY

Transaction:
    46951cfd631ff75140c8ec38af1927909dd2e5ed4192500982b591902d7e4fbb

Anomaly Strength:
    99.8

Why it was surfaced:
    1. louvain_community (value: 32, SHAP: -1.0345)
       Meaning: Topological cluster assignment identifying distinct network communities. [ML_DERIVED]

    2. unique_ip_propagators (value: 13, SHAP: -0.5692)
       Meaning: Number of distinct peer IP addresses through which the transaction was observed. [DERIVED]

    3. fee (value: 0.0006, SHAP: -0.4656)
       Meaning: Network fee explicitly attached to this transaction. [OBSERVED]

Supporting evidence:
    24 distinct evidence artifacts available.

Investigation caveats:
    - Anomaly indicates structural rarity, not criminality.
    - Network observation does not establish IP ownership.
    - GeoIP enrichment is unavailable in this run.
    - Exact UTXO lineage cannot be established without prev_txid/prev_vout fields.

Evidence provenance:
    - data/demo_v1/network/observations_fast.csv:30
    - data/demo_v1/network/observations_fast.csv:34
    - data/demo_v1/network/observations_fast.csv:36
    - ... and 5 more.
```

### Raw Evidence Trace
- **louvain_community**: value 32.0 -> shap -1.0344988910827244 (ML_DERIVED)
- **unique_ip_propagators**: value 13.0 -> shap -0.5691554396732775 (DERIVED)
- **fee**: value 0.0006 -> shap -0.4655500869692198 (OBSERVED)

---

## Alert 6: c2d66154d82a1e6fbcb27a994a4b1db8993f570ea32601ed25f71fb418642673

```text
STRUCTURAL ANOMALY

Transaction:
    c2d66154d82a1e6fbcb27a994a4b1db8993f570ea32601ed25f71fb418642673

Anomaly Strength:
    99.75

Why it was surfaced:
    1. louvain_community (value: 14, SHAP: -1.2210)
       Meaning: Topological cluster assignment identifying distinct network communities. [ML_DERIVED]

    2. unique_ip_propagators (value: 16, SHAP: -0.8200)
       Meaning: Number of distinct peer IP addresses through which the transaction was observed. [DERIVED]

    3. propagation_edge_count (value: 16, SHAP: -0.5229)
       Meaning: Total number of network peer-to-peer propagation events recorded. [DERIVED]

Supporting evidence:
    27 distinct evidence artifacts available.

Investigation caveats:
    - Anomaly indicates structural rarity, not criminality.
    - Network observation does not establish IP ownership.
    - GeoIP enrichment is unavailable in this run.
    - Exact UTXO lineage cannot be established without prev_txid/prev_vout fields.

Evidence provenance:
    - data/demo_v1/network/observations_fast.csv:424
    - data/demo_v1/network/observations_fast.csv:422
    - data/demo_v1/network/observations_fast.csv:425
    - ... and 5 more.
```

### Raw Evidence Trace
- **louvain_community**: value 14.0 -> shap -1.2210111722971482 (ML_DERIVED)
- **unique_ip_propagators**: value 16.0 -> shap -0.8199999327276657 (DERIVED)
- **propagation_edge_count**: value 16.0 -> shap -0.5229020573194059 (DERIVED)

---

## Alert 7: 6000a45797e5d20db47f4bafb4eafe6f7c472282e75a9424f5e876b348ba95b5

```text
STRUCTURAL ANOMALY

Transaction:
    6000a45797e5d20db47f4bafb4eafe6f7c472282e75a9424f5e876b348ba95b5

Anomaly Strength:
    99.7

Why it was surfaced:
    1. louvain_community (value: 12, SHAP: -1.2745)
       Meaning: Topological cluster assignment identifying distinct network communities. [ML_DERIVED]

    2. unique_ip_propagators (value: 16, SHAP: -0.8369)
       Meaning: Number of distinct peer IP addresses through which the transaction was observed. [DERIVED]

    3. propagation_edge_count (value: 16, SHAP: -0.4904)
       Meaning: Total number of network peer-to-peer propagation events recorded. [DERIVED]

Supporting evidence:
    27 distinct evidence artifacts available.

Investigation caveats:
    - Anomaly indicates structural rarity, not criminality.
    - Network observation does not establish IP ownership.
    - GeoIP enrichment is unavailable in this run.
    - Exact UTXO lineage cannot be established without prev_txid/prev_vout fields.

Evidence provenance:
    - data/demo_v1/network/observations_fast.csv:3905
    - data/demo_v1/network/observations_fast.csv:3906
    - data/demo_v1/network/observations_fast.csv:3903
    - ... and 5 more.
```

### Raw Evidence Trace
- **louvain_community**: value 12.0 -> shap -1.2745416109758745 (ML_DERIVED)
- **unique_ip_propagators**: value 16.0 -> shap -0.8368637143073469 (DERIVED)
- **propagation_edge_count**: value 16.0 -> shap -0.4904000353822734 (DERIVED)

---

## Alert 8: b9cb5589e9289d7e31ecda2271cc78808ee6fd05fc26a1f0eea6806156e8294f

```text
STRUCTURAL ANOMALY

Transaction:
    b9cb5589e9289d7e31ecda2271cc78808ee6fd05fc26a1f0eea6806156e8294f

Anomaly Strength:
    99.65

Why it was surfaced:
    1. louvain_community (value: 37, SHAP: -1.0596)
       Meaning: Topological cluster assignment identifying distinct network communities. [ML_DERIVED]

    2. unique_ip_propagators (value: 15, SHAP: -0.8703)
       Meaning: Number of distinct peer IP addresses through which the transaction was observed. [DERIVED]

    3. propagation_edge_count (value: 16, SHAP: -0.5184)
       Meaning: Total number of network peer-to-peer propagation events recorded. [DERIVED]

Supporting evidence:
    26 distinct evidence artifacts available.

Investigation caveats:
    - Anomaly indicates structural rarity, not criminality.
    - Network observation does not establish IP ownership.
    - GeoIP enrichment is unavailable in this run.
    - Exact UTXO lineage cannot be established without prev_txid/prev_vout fields.

Evidence provenance:
    - data/demo_v1/network/observations_fast.csv:280
    - data/demo_v1/network/observations_fast.csv:279
    - data/demo_v1/network/observations_fast.csv:281
    - ... and 5 more.
```

### Raw Evidence Trace
- **louvain_community**: value 37.0 -> shap -1.0596261504405082 (ML_DERIVED)
- **unique_ip_propagators**: value 15.0 -> shap -0.8702976719143399 (DERIVED)
- **propagation_edge_count**: value 16.0 -> shap -0.518385361247788 (DERIVED)

---

## Alert 9: 69fe8000afa49640370273a3e581a8700ae3169884ede3da33c73acf72cb9ec7

```text
STRUCTURAL ANOMALY

Transaction:
    69fe8000afa49640370273a3e581a8700ae3169884ede3da33c73acf72cb9ec7

Anomaly Strength:
    99.6

Why it was surfaced:
    1. louvain_community (value: 20, SHAP: -1.2642)
       Meaning: Topological cluster assignment identifying distinct network communities. [ML_DERIVED]

    2. unique_ip_propagators (value: 12, SHAP: -0.5330)
       Meaning: Number of distinct peer IP addresses through which the transaction was observed. [DERIVED]

    3. total_degree (value: 16, SHAP: -0.5060)
       Meaning: Total number of unique addresses involved as inputs or outputs. [DERIVED]

Supporting evidence:
    23 distinct evidence artifacts available.

Investigation caveats:
    - Anomaly indicates structural rarity, not criminality.
    - Network observation does not establish IP ownership.
    - GeoIP enrichment is unavailable in this run.
    - Exact UTXO lineage cannot be established without prev_txid/prev_vout fields.

Evidence provenance:
    - data/demo_v1/network/observations_fast.csv:3396
    - data/demo_v1/network/observations_fast.csv:3400
    - data/demo_v1/network/observations_fast.csv:3397
    - ... and 5 more.
```

### Raw Evidence Trace
- **louvain_community**: value 20.0 -> shap -1.2642223612835946 (ML_DERIVED)
- **unique_ip_propagators**: value 12.0 -> shap -0.5330319609687094 (DERIVED)
- **total_degree**: value 16.0 -> shap -0.5060077640000293 (DERIVED)

---

## Alert 10: 73da85a24cc4931cece4ec94eb60ddabe1cc9da06d7bda1f78f57c0af90d94e5

```text
STRUCTURAL ANOMALY

Transaction:
    73da85a24cc4931cece4ec94eb60ddabe1cc9da06d7bda1f78f57c0af90d94e5

Anomaly Strength:
    99.55000000000001

Why it was surfaced:
    1. louvain_community (value: 31, SHAP: -1.0926)
       Meaning: Topological cluster assignment identifying distinct network communities. [ML_DERIVED]

    2. unique_ip_propagators (value: 14, SHAP: -0.7433)
       Meaning: Number of distinct peer IP addresses through which the transaction was observed. [DERIVED]

    3. propagation_edge_count (value: 16, SHAP: -0.5391)
       Meaning: Total number of network peer-to-peer propagation events recorded. [DERIVED]

Supporting evidence:
    25 distinct evidence artifacts available.

Investigation caveats:
    - Anomaly indicates structural rarity, not criminality.
    - Network observation does not establish IP ownership.
    - GeoIP enrichment is unavailable in this run.
    - Exact UTXO lineage cannot be established without prev_txid/prev_vout fields.

Evidence provenance:
    - data/demo_v1/network/observations_fast.csv:909
    - data/demo_v1/network/observations_fast.csv:905
    - data/demo_v1/network/observations_fast.csv:910
    - ... and 5 more.
```

### Raw Evidence Trace
- **louvain_community**: value 31.0 -> shap -1.0925890786647563 (ML_DERIVED)
- **unique_ip_propagators**: value 14.0 -> shap -0.7433386543154585 (DERIVED)
- **propagation_edge_count**: value 16.0 -> shap -0.5390784062576287 (DERIVED)

---

