import csv
import json
import os
from datetime import datetime, timezone, timedelta

import pandas as pd
import logging
from typing import Optional, Any, Dict, List
from directory_issues.scripts.client import MediaCloudClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

CACHE_DIR = '/tmp/directory_issues'
HOURS_TO_CACHE = 5 # Hours


class SourcesBase:
    def __init__(self, client: MediaCloudClient):
        self.client = client
        self.result_column = "result"

    def process_sources(
            self,
            platform: Optional[str] = None,
            batch_size: int = 100,
            file_name: Optional[str] = None,
    ):
        sources_generator = self.client.get_sources(
            platform=platform, batch_size=batch_size
        )

        total_sources = None
        processed_sources = 0

        for batch_number, sources in enumerate(sources_generator, start=1):
            if total_sources is None:
                response = self.client.directory_client.source_list(
                    platform=platform, limit=1
                )
                total_sources = response.get("count", 0)
                logger.info(f"Total sources to process: {total_sources}")

            batch_results = self._process_source_batch(sources)
            self._save_batch_results_to_csv(
                batch_results, batch_number, file_name or "sources"
            )
            processed_sources += len(sources)
            logger.info(f"Processed {processed_sources}/{total_sources} sources")

            if processed_sources >= total_sources:
                break

    def _process_source_batch(self, sources: List[str]) -> List[dict]:
        """
        Process a batch of sources and collect results.
        """
        batch_results = []
        for source in sources:
            try:
                result = self.analyze_source(source)
                if result is not None:
                    batch_results.append({"source": source, self.result_column: result})
            except Exception as e:
                logger.exception(e)

        return batch_results

    def _save_batch_results_to_csv(
            self,
            batch_results: List[dict],
            batch_number: int,
            file_name: str,
    ):
        """
        Save batch results to a CSV file with error handling.
        """
        if not batch_results:
            return

        try:
            batch_df = pd.DataFrame(batch_results)
            batch_df.to_csv(
                f"{file_name}_results_batch_{batch_number}.csv", index=False
            )
        except Exception as e:
            logger.exception(e)

    def analyze_source(self, domain: str):
        raise NotImplementedError("Subclasses must implement this method.")


class CollectionsBase:
    def __init__(self, client: MediaCloudClient):
        self.client = client
        self.collection_lookup = {}  # Used to determine the collection_id of a given state collection e.g. [Massachusetts, United States - State & Local] -> [ US-MA ] -> collection_id ?
  
    def get_sources_in_collection(self, collection_id, limit=1000):
        offset = 0
        cache_file = f"{CACHE_DIR}/collection-{collection_id}.json"
        cached_sources = None
        cache_valid = False
        cache_duration = timedelta(hours=HOURS_TO_CACHE)

        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache_content = json.load(f)
                    if isinstance(cache_content, dict) and "timestamp" in cache_content and "data" in cache_content:
                        timestamp_str = cache_content["timestamp"]
                        cached_time = datetime.fromisoformat(timestamp_str)
                        now = datetime.now()
                        if now < (cached_time + cache_duration):
                            logger.info("Cache is fresh (fetched at %s). Using cache.", cached_time)
                            cached_sources = cache_content["data"]
                            cache_valid = True
                        else:
                            logger.info("Cache is stale (fetched at %s). Fetching new data.", cached_time)
            except (json.JSONDecodeError, IOError, ValueError):
                logger.exception("Error reading or parsing cache file:. Fetching new data.")

        if cache_valid and cached_sources is not None:
            logger.info("Fetched a total of [%s] cached sources", len(cached_sources))
            return cached_sources
        else:
            sources = []
            while True:
                logger.info("Fetching sources, offset [%s]", offset)
                if collection_id is None:
                    response = self.client.directory_client.source_list(offset=offset, limit=limit)
                else:
                    response = self.client.directory_client.source_list(collection_id=collection_id, offset=offset,
                                                                        limit=limit)
                sources += response["results"]
                if response["next"] is None:
                    break
                offset += len(response["results"])

            logger.info("Fetched a total of [%s] sources", len(sources))

            fetch_time = datetime.now()
            cache_content_to_save = {
                "timestamp": fetch_time.isoformat(),
                "data": sources
            }

            os.makedirs(CACHE_DIR, exist_ok=True)

            try:
                with open(cache_file, 'w') as f:
                    json.dump(cache_content_to_save, f, indent=4)
                logger.info("Data fetched successfully and saved to cache file: %s",cache_file)
            except IOError:
                logger.exception("Error writing to cache file")

            return sources

    def write_output(self, file_name, data):
        with open(file_name, mode='w', newline='') as file:
            writer = csv.writer(file)
            for item in data:
                writer.writerow(item)

    def create_lookup_data(self):
        raise NotImplementedError("Subclasses must implement this method")
   
    def run_process(self):
        raise NotImplementedError("Subclasses must implement this method")
