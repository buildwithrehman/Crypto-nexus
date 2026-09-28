# Provenance

The blockchain transaction layer (`blockchain/transactions.csv`) is derived from public Bitcoin blockchain data fetched via the `blockchain.info` raw blocks API.

The network observation layer (`network/observations.csv`) is synthetically generated because the public blockchain ledger does not contain the required P2P observation fields (IPs, ports, observation timestamps).

GeoIP results are locally enriched from the offline GeoIP database.

Synthetic network observations are demonstration data and must not be interpreted as historical evidence of actual peer-to-peer communication.
