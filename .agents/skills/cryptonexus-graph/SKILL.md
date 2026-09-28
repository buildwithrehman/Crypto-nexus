---
name: cryptonexus-graph
description: Protect graph semantics and graph-analysis implementation.
---
# cryptonexus-graph

## Purpose
Protect graph semantics and graph-analysis implementation.

## Canonical Graph
NetworkX MultiDiGraph

## Nodes
IP, Transaction, Address

## Edges
- IP → Transaction [PROPAGATED]
- Address → Transaction [INPUT]
- Transaction → Address [OUTPUT]

## Invariants
- Never create: IP → OWNS → Address
- Graph must support investigation, traversal, analysis, and evidence visualization.
- Algorithms follow TRD/Architecture/Phases.
