import pandas as pd
import logging
from typing import Optional, Any, Dict, List
from ..client import MediaCloudClient

logger = logging.getLogger(__name__)


class SourcesBase:
    def __init__(self, client: MediaCloudClient):
        self.client = client
        self.provider = client.provider

    def process_sources(
        self,
        platform: Optional[str] = None,
        batch_size: int = 1000,
        file_name: str = None,
    ):
        sources = self.client.get_all_sources(platform=platform, batch_size=batch_size)
        batch_number = 1
        batch_results = []

        for idx, source in enumerate(sources, start=1):
            result = self.analyze_source(source)
            if result is not None:
                batch_results.append({"source": source, self.result_column: result})

            # Save the current batch to a CSV file when batch size is reached
            if idx % self.batch_size == 0 or idx == len(sources):
                self._save_batch_results_to_csv(batch_results, batch_number, file_name)
                batch_results = []
                batch_number += 1

    def _save_batch_results_to_csv(
        self, batch_results: List[dict], batch_number: int, file_name: str = ""
    ):
        batch_df = pd.DataFrame(batch_results)
        filename = f"{file_name}_results_batch_{batch_number}.csv"
        batch_df.to_csv(filename, index=False)
        logger.info(f"Saved language results batch {batch_number} to {filename}")

    def analyze_source(self, domain: str):
        raise NotImplementedError("Subclasses must implement this method.")
