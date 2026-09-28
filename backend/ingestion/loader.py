from datetime import datetime
from backend.ingestion.parser import parse_file
from backend.ingestion.validator import DataValidator
from backend.database.repository import CryptoNexusRepository
from backend.schema import IngestionMetadata

class IngestionLoader:
    def __init__(self, repo: CryptoNexusRepository):
        self.repo = repo

    def load_file(self, run_id: str, source_file: str) -> IngestionMetadata:
        meta = IngestionMetadata(
            run_id=run_id,
            source_file=source_file,
            ingestion_timestamp=datetime.utcnow(),
            record_count=0,
            quarantine_count=0
        )
        self.repo.insert_ingestion_run(meta)

        validator = DataValidator(run_id=run_id, source_file=source_file)
        
        accepted_count = 0
        quarantined_count = 0
        
        for row_index, raw_dict in enumerate(parse_file(source_file), start=1):
            is_valid, result = validator.validate_record(raw_dict, row_index)
            if is_valid:
                obs, tx, prov = result
                self.repo.insert_accepted_record(obs, tx, prov)
                accepted_count += 1
            else:
                self.repo.insert_quarantine_record(result)
                quarantined_count += 1
                
        self.repo.update_ingestion_counts(run_id, accepted_count, quarantined_count)
        meta.record_count = accepted_count
        meta.quarantine_count = quarantined_count
        return meta

    def load_transaction_file(self, run_id: str, source_file: str) -> IngestionMetadata:
        meta = IngestionMetadata(
            run_id=run_id,
            source_file=source_file,
            ingestion_timestamp=datetime.utcnow(),
            record_count=0,
            quarantine_count=0
        )
        # Assuming ingestion run is already created for the run_id, we might need to handle uniqueness,
        # but the orchestrator usually creates the run. Let's insert a tracking record specific to this file.
        try:
            self.repo.insert_ingestion_run(meta)
        except Exception:
            pass # Handle if already exists for this run_id (the API uses run_uploads to track uniqueness)

        validator = DataValidator(run_id=run_id, source_file=source_file)
        
        accepted_count = 0
        quarantined_count = 0
        
        for row_index, raw_dict in enumerate(parse_file(source_file), start=1):
            is_valid, result = validator.validate_transaction(raw_dict, row_index)
            if is_valid:
                tx, prov = result
                self.repo.insert_transaction_record(tx, prov)
                accepted_count += 1
            else:
                self.repo.insert_quarantine_record(result)
                quarantined_count += 1
                
        # Update could overwrite the other file's counts, so we can just rely on the API side or sum it.
        # But this is fine for now as an internal metric.
        meta.record_count = accepted_count
        meta.quarantine_count = quarantined_count
        return meta

    def load_observation_file(self, run_id: str, source_file: str) -> IngestionMetadata:
        meta = IngestionMetadata(
            run_id=run_id,
            source_file=source_file,
            ingestion_timestamp=datetime.utcnow(),
            record_count=0,
            quarantine_count=0
        )
        validator = DataValidator(run_id=run_id, source_file=source_file)
        
        accepted_count = 0
        quarantined_count = 0
        
        for row_index, raw_dict in enumerate(parse_file(source_file), start=1):
            is_valid, result = validator.validate_observation(raw_dict, row_index)
            if is_valid:
                obs, prov = result
                try:
                    self.repo.insert_observation_record(obs, prov)
                    accepted_count += 1
                except ValueError as e:
                    reason = str(e)
                    qr = validator._create_quarantine(raw_dict, row_index, reason)
                    self.repo.insert_quarantine_record(qr)
                    quarantined_count += 1
            else:
                self.repo.insert_quarantine_record(result)
                quarantined_count += 1
                
        meta.record_count = accepted_count
        meta.quarantine_count = quarantined_count
        return meta
