import csv

import pandas as pd
import logging
from typing import Optional, Any, Dict, List
from directory_issues.scripts.client import MediaCloudClient

logger = logging.getLogger(__name__)


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
        self.states = {
            "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA", "Colorado": "CO",
            "Connecticut": "CT",
            "Delaware": "DE", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL",
            "Indiana": "IN",
            "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
            "Massachusetts": "MA",
            "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO", "Montana": "MT",
            "Nebraska": "NE", "Nevada": "NV",
            "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
            "North Dakota": "ND",
            "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI",
            "South Carolina": "SC", "South Dakota": "SD",
            "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
            "West Virginia": "WV", "Wisconsin": "WI",
            "Wyoming": "WY", "District of Columbia": "DC"
        }

        self.collection_lookup = {}  # Used to determine the collection_id of a given state collection e.g. [Massachusetts, United States - State & Local] -> [ US-MA ] -> collection_id ?
        self.states_code_lookup = {}  # Used to determine the state code for a given state name e.g. [Massachusetts] -> [US-MA]
        self.sources_lookup = {}  # Used to determine the collection ids of a given source e.g. [Source ID] -> Collection_ids ?

    def create_lookup_data(self):
        collections = self.client.directory_client.collection_list(name="United States")["results"]
        for collection in collections:
            name_part = collection["name"].split(
                ",")  # Split strings like Massachusetts, United States - State & Local to get state name
            if len(name_part) > 1 and (
                    "United States - State & Local" in name_part[1] or "United States -State & Local" in name_part[1]):
                state_code = f"US-{self.states[name_part[0]]}"
                if self.states[name_part[0]]:
                    self.collection_lookup[state_code] = collection["id"]
                    self.states_code_lookup[collection["id"]] = state_code

                    # Get sources under a collection and build the sources lookup dict
                    collection_sources = \
                    self.client.directory_client.source_list(collection_id=collection["id"], limit=collection["source_count"])[
                        "results"]
                    for source in collection_sources:
                        # The assumption is a source can appear in more than one collection
                        if source["id"] in self.sources_lookup:
                            self.sources_lookup[source["id"]].append(collection["id"])
                        else:
                            self.sources_lookup[source["id"]] = [collection["id"]]

    def write_output(self, file_name, data):
        with open(file_name, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['source_id', 'label', 'homepage','pub_state','correct_collection_id']),
            for item in data:
                writer.writerow([item['id'], item['label'], item['homepage'],item['pub_state'], self.collection_lookup.get(item['pub_state'])])

    def run_process(self):
        raise NotImplementedError("Subclasses must implement this method")
