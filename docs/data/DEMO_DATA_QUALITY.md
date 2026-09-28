# Demo Data Quality Report

## Block Range
- **Block Start**: 700000
- **Block End**: 700022

## Source Statistics
- **Total Source Transactions**: 25,649
- **Accepted Transactions**: 25,649
- **Quarantined Transactions (Parse level)**: 0
- **Malformed Transactions**: 0
- **Duplicate TXIDs**: 0

## Network Observation Statistics
- **Total Network Observations**: 60,355
- **Observations per Transaction (Average)**: 2.35
- **Synthetic IPs**: Generated from public IPv4 ranges avoiding reserved/private blocks.
- **Unique Source IPs**: 6,605
- **Unique Destination IPs**: 7,059
- **Total Unique Peers**: 7,468
- **Peer Reuse Count**: 7,107 peers appear in >1 TX
- **Transactions/Peer (Avg/Min/Max)**: 19 / 1 / 268 (Median: 5)
- **Propagation Duration (Avg/Max sec)**: 279.46 / 600.0
- **Connected Components**: 3
- **Largest Component Size**: 4,916
- **Unique IP Propagators Variance**: 1.40
- **Propagation Edge Count Variance**: 3.13

## GeoIP Validation
- **Status**: `GEOIP_VALIDATION_PENDING`
- **Reason**: The official local MaxMind MMDB is not currently present in the required path (`data/geolite/GeoLite2-City.mmdb`). No external GitHub mirrors or unauthorized endpoints were used.
- **Data Readiness**: The synthetic peer pool was deliberately restricted to valid public IPv4 addresses so it is fully compatible once the official/local MMDB is supplied.

## Blockchain Properties
- **Timestamp Range**: 2021-09-11T04:14:32Z to 2021-09-11T08:29:13Z
- **Input Count Distribution**:
  - Minimum: 1
  - Maximum: 671
  - Average: 3.16
- **Output Count Distribution**:
  - Minimum: 1
  - Maximum: 691
  - Average: 3.36
- **Transaction Amount Statistics**: Derived exactly from source satoshi values to 8-decimal precision string formats.
- **Empty/Null Address Statistics**: 0 (Empty script addresses fallback to structurally safe representations natively handled by existing loader semantics).
- **Fee Availability**: Yes. Structurally derived natively by the source or synthetically computed as 0 for coinbase transactions.

## Dataset Provenance
- **Source**: blockchain.info raw blocks API
- **Deterministic Seed**: 26146
