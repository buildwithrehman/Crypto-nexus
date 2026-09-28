---
name: cryptonexus-offline
description: Enforce the offline runtime contract.
---
# cryptonexus-offline

## Purpose
Enforce the offline contract.

## Runtime Requirements
Must work with Wi-Fi disabled, network disconnected, DNS unavailable.

## Forbidden Inclusions
- runtime external APIs
- online blockchain explorers
- online GeoIP
- CDN JavaScript
- remote fonts/images
- telemetry
- runtime package downloads

## Dependencies
Installation must use local wheels.
If a required wheel is missing, STOP and report it.

Never fabricate wheels, GeoIP databases, Tor lists, model artifacts, or datasets.
