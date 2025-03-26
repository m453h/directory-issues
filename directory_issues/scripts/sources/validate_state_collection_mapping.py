import os
import mediacloud.api
from directory_issues.scripts.sources.base import CollectionsBase, MediaCloudClient

LIMIT = 100000

class Collections(CollectionsBase):

    def __init__(self, mc_client: MediaCloudClient):
        super().__init__(mc_client)
        self.directory_api = mediacloud.api.DirectoryApi(os.getenv("MC_API_KEY"))

    def run_process(self):
        self.create_lookup_data()

        # Get all sources
        sources = []
        offset = 0 
        while True:
            response = self.client.directory_client.source_list(limit=LIMIT, offset=offset) # Adjust limit to reduce number of iterations
            sources += response["results"]
            if response["next"] is None:
                break
            offset += len(response["results"])

        # Check if all US sources with a `pub_state` are in the right collection
        sources_in_wrong_collection = []
        sources_not_in_any_collection = []
        for source in sources:
            if source["pub_state"]and source["pub_country"] == "USA" :
                if source["id"] in self.sources_lookup:
                    collection_ids = self.sources_lookup[source["id"]]
                    for collection_id in collection_ids:
                        state_code = self.states_code_lookup[collection_id]
                        if not state_code:
                            sources_in_wrong_collection.append(source)
                else:
                    sources_not_in_any_collection.append(source)
        
        self.write_output("sources_in_wrong_collection.csv", sources_in_wrong_collection)
        self.write_output("sources_not_in_any_collection.csv", sources_not_in_any_collection)
        print(len(sources_not_in_any_collection))
    

if __name__ == "__main__":
    client = MediaCloudClient()
    collections = Collections(client) 
    collections.run_process()
