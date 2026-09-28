# Source to Canonical Schema Mapping

## Overview
This document maps the `bigquery-public-data.crypto_bitcoin` schema to the CryptoNexus Phase 1 canonical transaction schema.

## Transaction Mapping

| CryptoNexus field | Source field(s) | Transformation | Availability | Notes |
|---|---|---|---|---|
| `txid` | `transactions.hash` | None | SOURCE_AVAILABLE | Canonical primary key. |
| `input_addresses[]` | `inputs.addresses` | Flatten array if needed, extract string. | SOURCE_AVAILABLE | Address array usually contains 1 address for standard inputs. |
| `output_addresses[]` | `outputs.addresses` | Flatten array, extract string. | SOURCE_AVAILABLE | Null/empty for complex unparseable scripts (e.g. OP_RETURN). |
| `input_amounts[]` | `inputs.value` | Convert Satoshi or Decimal to canonical format. | SOURCE_AVAILABLE | |
| `output_amounts[]` | `outputs.value` | Convert Satoshi or Decimal to canonical format. | SOURCE_AVAILABLE | |
| `fee` | `transactions.fee` | Convert to canonical float/decimal. | SOURCE_AVAILABLE | BigQuery natively computes `fee` via `input_value - output_value`. |
| `script_type` | `inputs.type` / `outputs.type` | String translation (e.g., `pubkeyhash`, `scripthash`). | SOURCE_AVAILABLE | |
| `timestamp` | `transactions.block_timestamp`| Use as fallback for network obs if needed. | SOURCE_AVAILABLE | Block timestamp only. Network timestamp is NOT_AVAILABLE. |

## Network Layer Gap Analysis

| CryptoNexus field | Source field(s) | Transformation | Availability | Notes |
|---|---|---|---|---|
| `src_ip` | N/A | Generated synthetically. | NOT_AVAILABLE | Blockchain lacks P2P propagation data. |
| `dst_ip` | N/A | Generated synthetically. | NOT_AVAILABLE | Blockchain lacks P2P propagation data. |
| `src_port` / `dst_port` | N/A | Generated synthetically. | NOT_AVAILABLE | |
| `network_obs_timestamp` | N/A | Synthetically generated slightly before `block_timestamp`. | NOT_AVAILABLE | |

## Missing Data / Null Policy

- **REQUIRED STRUCTURAL DATA**: `txid`, `input_index`, `output_index`. If these are fundamentally missing or corrupt, the row must be quarantined.
- **OPTIONAL DATA**: `address`. For `OP_RETURN` or complex multisig, the address may be legitimately NULL in outputs. Handled gracefully.
- **DERIVABLE DATA**: `fee` is derived structurally, provided natively by the source. If missing, derived as sum(inputs) - sum(outputs), or quarantined if coinbase.
- **UNAVAILABLE DATA**: Network IP/Ports. These remain structurally unavailable from the source and rely explicitly on the synthetic generator.
