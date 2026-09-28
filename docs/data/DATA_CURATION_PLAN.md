# Data Curation Plan

## Objective
Extract a bounded, realistic, and relationship-preserving dataset from the public Bitcoin blockchain, supplemented by a verifiable synthetic network layer, strictly for offline SIH/prototype demonstration.

## Data Volume & Selection Strategy
- **Target Volume**: 10,000–25,000 transactions.
- **Selection Strategy**: **Contiguous Block Window**. 
  - Instead of randomly sampling rows (which breaks graph connectivity, UXTO lineage, and input/output integrity), we will select all transactions from a small contiguous sequence of blocks (e.g., blocks 700,000 to 700,010).
  - This ensures that combinatorial/remainder clustering heuristics (CIH) operate on structurally valid local subgraphs.

## Data Quality Profile (Simulated Benchmark)
Based on public historical block metrics, a representative 10-block contiguous slice yields:
- **Transaction Count**: ~20,000 unique TXIDs.
- **Missing/Malformed Values**: < 0.01% (typically limited to OP_RETURN null addresses).
- **Zero Values**: Valid for some OP_RETURNs; structurally quarantined if violating protocol rules.
- **Input/Output Distribution**: Power-law distribution (majority 1-2 inputs, 1-2 outputs; heavy tail of exchange/mining payouts with hundreds of outputs).
- **Duplicates**: 0 (TXID is strongly constrained as unique per run).

## CryptoNexus Compatibility
- **NATIVELY SUPPORTED BY SOURCE**: Transaction graph structure, input/output nodes, exact UTXO amounts, fees, address-reuse heuristics, remainder-change heuristics, and base feature engineering.
- **REQUIRES SYNTHETIC ADDITION**: P2P network propagation (`network_obs`), node topology (IPs), and GeoIP geolocation clusters.

## GeoIP Compatibility Requirements
The synthetic network layer must generate valid, globally distributed public IPv4 (and IPv6) addresses to ensure compatibility with Phase 6's local MaxMind/GeoLite2 offline mmdb lookups. Generated IPs must NOT be restricted exclusively to reserved/private ranges (`10.0.0.0/8`, `192.168.0.0/16`), or GeoIP enrichment will trivially fail.

## Provenance Design
The final dataset manifest will enforce strict provenance boundaries:
```json
{
  "dataset_name": "CryptoNexus Demo Dataset",
  "dataset_version": "1.0",
  "source_name": "Google BigQuery crypto_bitcoin",
  "source_license": "CC0 / Public Domain",
  "selection_method": "Contiguous Block Sequence",
  "block_range": "700000 - 700010",
  "provenance_layers": {
    "blockchain": "PUBLIC_DERIVED",
    "network_obs": "SYNTHETIC",
    "enrichment": "ENRICHED"
  }
}
```

## Security & Ethics
- No seized or deanonymized datasets will be used.
- IP addresses generated for the network layer will be mathematically synthetic. Any collision with real-world infrastructure is coincidental and explicitly declared non-attributable in the prototype interface.
- No human identities, wallet owner labels, or probabilistic crime attributions will be fabricated in the baseline truth data.
