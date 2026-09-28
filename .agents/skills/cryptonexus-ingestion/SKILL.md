---
name: cryptonexus-ingestion
description: Enforce the canonical ingestion contract and data integrity.
---
# cryptonexus-ingestion

## Purpose
Enforce the canonical ingestion contract.

## Pipeline
Detect → Parse → Validate → Cast → Normalize → Quarantine / Accept

## Supported Formats
CSV, JSON, XML

## Rules
- Never silently drop records.
- Never silently coerce invalid data.
- Never invent fields.
- Never silently repair array mismatches.
- Never overwrite duplicate TXIDs.

## Provenance to Preserve
- source file
- row/record identity
- run ID
- validation status
- rejection reason
