---
name: cryptonexus-ml
description: Control the ML pipeline and score interpretation.
---
# cryptonexus-ml

## Purpose
Control the ML pipeline.

## Canonical Pipeline
Feature Engineering → RobustScaler → Isolation Forest → HDBSCAN → SHAP → Human-readable explanation

## Rules
- Respect versions and parameters defined in TRD.
- Do not introduce alternative ML models without explicit authorization.
- Do not describe anomaly scores as crime probabilities.
- Synthetic evaluation must be clearly identified as synthetic.
- Persist model metadata needed for reproducibility.
