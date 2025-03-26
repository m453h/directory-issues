import argparse
import os
import mediacloud.api
import logging
from directory_issues.scripts.sources.base import CollectionsBase, MediaCloudClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CollectionsPartisanship(CollectionsBase):

    def __init__(self, mc_client: MediaCloudClient, ids: list):
        super().__init__(mc_client)
        self.directory_api = mediacloud.api.DirectoryApi(os.getenv("MC_API_KEY"))
        self.collection_ids = ids

    def set_lookup_data(self):
        logger.info("Setting up lookup data")
        self.collection_lookup = {}
        for collection_id in collection_ids:
            collection = self.client.directory_client.collection(collection_id)
            self.collection_lookup[collection_id] = collection['name']

    def run_process(self):
        self.set_lookup_data()
        sources_tracker = {}
        for collection_id in self.collection_ids:
            sources = self.get_sources_in_collection(collection_id)
            for source in sources:
                logger.info("Adding source with [%s] to sources_tracker", source["id"])
                if sources_tracker.get(source["id"]):
                    sources_tracker[source["id"]]['collection_ids'].append(collection_id)
                else:
                    sources_tracker[source["id"]] = { 'collection_ids': [collection_id], 'source': source}
        
        data = [["source_id", "label", 'homepage', 'collection_ids', 'collection_names']]
        for item, value in sources_tracker.items():
            if len(value.get("collection_ids")) > 1:
                logger.info("Adding source [%s] to output list", source["id"])
                collection_ids = value.get("collection_ids")
                collection_names = []
                
                # Get the names of the collections
                for collection_id in collection_ids:
                    collection_names.append(self.collection_lookup.get(collection_id))

                data.append([
                    value.get("source").get("id"), 
                    value.get("source").get("name"), 
                    value.get("source").get("homepage"), 
                    ';'.join(collection_ids), 
                    ';'.join(collection_names)])
       
        logger.info("Writting output file...")
        self.write_output("sources_in_multi_partisanship_collections.csv", data)

    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A script to list sources that appear in more than one of tweet-based partisanship collections.")
    parser.add_argument(
        '--collection_ids',
        type=str,
        default="231013063,231013089,231013108,231013109,231013110",
        help="A comma-separated list of collection IDs to check "
    )
    args = parser.parse_args()
    collection_ids = args.collection_ids.split(",")

    client = MediaCloudClient()
    app = CollectionsPartisanship(client, collection_ids)
    app.run_process()
