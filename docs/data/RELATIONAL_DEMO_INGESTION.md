# Relational Demo Ingestion

This document details the ingestion architecture utilized for the Phase 18 demo dataset, distinguishing it from standard flattened-file ingestion.

## Transaction-Level vs Observation-Level Sources
The CryptoNexus architecture strictly enforces canonical transaction semantics (uniqueness) while explicitly supporting a one-to-many relationship with network observations.

- **`transactions.csv`**: This source represents the canonical blockchain layer. Each row is a unique transaction. The system strictly enforces TXID uniqueness here.
- **`observations.csv`**: This source represents the network layer. Each row is a single observation event. Multiple rows may refer to the same TXID, denoting different peer propagations over time.

## Duplicate TXID Validation
During standard, single-file ingestion (`INGEST`), `DataValidator` tracks `seen_txids` and quarantines duplicates. This ensures flat files do not violate canonical constraints.

When using the explicit relational bridge (`INGEST TRANSACTIONS` followed by `INGEST NETWORK OBSERVATIONS`):
1. **Transactions** are processed via `validate_transaction`, which retains the strict `seen_txids` duplicate quarantine logic.
2. **Observations** are processed via `validate_observation`, which ensures valid schemas but purposefully omits the `seen_txids` check. This accurately preserves the one-to-many network multiplicity.

## Referential Integrity
Referential integrity is guaranteed at the repository layer during observation insertion:
```python
row = self.conn.execute("SELECT 1 FROM transactions WHERE txid = ?", [obs.txid]).fetchone()
if not row:
    raise ValueError(f"Unknown TXID in observation: {obs.txid}")
```
Observations referencing unknown TXIDs are strictly quarantined and do not silently create invalid transaction records.

## Provenance and Run Isolation
- **Run Isolation**: Every ingested observation is scoped to a specific `run_id`. Cross-run data bleeding is mathematically impossible because the schema for `network_obs` is keyed by `run_id`. The Phase 18.1 API guarantees a unique ID per run.
- **Provenance**: Direct evidence (e.g. `source_file` and `source_row`) is rigorously preserved. Transactions point precisely to their line in `transactions.csv`, and observations point precisely to their line in `observations.csv`.

## Preservation of Phase 3 Validation Semantics
This architecture explicitly DOES NOT weaken any Phase 3 constraints. Canonical uniqueness remains fiercely protected; this bridge simply implements the necessary data-modeling semantics to map two relational files into the system's natively supported one-to-many schema.
