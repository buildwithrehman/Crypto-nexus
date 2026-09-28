# Public Data Source

## Source Information
- **Dataset Name**: Google BigQuery Public Datasets: Bitcoin (`bigquery-public-data.crypto_bitcoin`)
- **Publisher**: Google Cloud / Blockchain ETL
- **Official URL**: https://console.cloud.google.com/marketplace/details/bitcoin/crypto-bitcoin
- **Approximate Size**: >1TB (Full Blockchain), highly partitioned.
- **Historical Coverage**: Genesis block (2009) to present (updated daily).

## License & Provenance
- **License**: Public Domain (CC0 / Open Data). The raw Bitcoin blockchain is a public ledger. The curated extraction by Google / Blockchain ETL is distributed as a public dataset without restrictive copyright.
- **Redistribution**: Permitted.
- **Attribution Requirements**: Best practice to attribute "Google Cloud Public Datasets" and "Blockchain ETL" when republishing derived subsets.
- **Offline / Prototype Use**: Fully permitted for academic, SIH prototypes, and offline development. Modified subsets can be freely created and redistributed.
- **License Status**: VERIFIED.

## Intended Use
CryptoNexus will extract a deterministic, contiguous, bounded subset of raw historical transactions (approx. 10,000–25,000 transactions, e.g., representing 4–10 consecutive blocks) to serve as the realistic, relationship-preserving blockchain data baseline.

## Limitations
- **Network Metadata Absence**: This dataset ONLY contains ledger data (blocks, transactions, inputs, outputs). It does NOT contain Peer-to-Peer network observations (e.g., src_ip, dst_ip, ports, network timestamps).
- **Identity Absence**: The dataset contains only pseudonymous addresses, completely devoid of off-chain identities.

## Provenance Semantics
Data derived from this source will be explicitly tagged:
- `PUBLIC_DERIVED`: Legitimate historical ledger records.
- `SYNTHETIC`: Any artificially attached network P2P IP observations.
- `ENRICHED`: Derived geographical/ASN information.
