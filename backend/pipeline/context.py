import os
from dataclasses import dataclass
from typing import Optional
from backend.database.repository import CryptoNexusRepository

@dataclass
class PipelineContext:
    run_id: str
    source_file: str
    repo: CryptoNexusRepository
    artifact_dir: str
    model_version: str = "1.0"
    is_training_run: bool = False

    def get_run_artifact_dir(self) -> str:
        """
        If this is an inference run, we load from the model artifact dir.
        If it's a training run, we might overwrite or version it.
        We stick to a single artifact dir for models, but we can have a run-specific one for alerts.
        """
        # We use a central artifact dir for ML models (e.g. backend/ml/artifacts).
        # We ensure it exists.
        os.makedirs(self.artifact_dir, exist_ok=True)
        return self.artifact_dir

