import os
import mediacloud.api
import logging
from directory_issues.scripts.sources.base import CollectionsBase, MediaCloudClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

LIMIT = 100000


class CollectionStates(CollectionsBase):

    def __init__(self, mc_client: MediaCloudClient):
        super().__init__(mc_client)
        self.directory_api = mediacloud.api.DirectoryApi(os.getenv("MC_API_KEY"))
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
        self.states_code_lookup = {}  # Used to determine the state code for a given state name e.g. [Massachusetts] -> [US-MA]
        self.sources_lookup = {}  # Used to determine the collection ids of a given source e.g. [Source ID] -> Collection_ids ?
    
    def set_lookup_data(self):
        logger.info("Setting up lookup data")
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
                    collection_sources = self.get_sources_in_collection(collection["id"], LIMIT)

                    for source in collection_sources:
                        # The assumption is a source can appear in more than one collection
                        if source["id"] in self.sources_lookup:
                            self.sources_lookup[source["id"]].append(collection["id"])
                        else:
                            self.sources_lookup[source["id"]] = [collection["id"]]

    def run_process(self):
        self.set_lookup_data()

        # Get all sources
        logger.info("Fetchin all sources...")
        sources = self.get_sources_in_collection(None, LIMIT)

        # Check if all US sources with a `pub_state` are in the right collection
        headers = ['source_id', 'label', 'homepage', 'pub_state','stories_per_week', 'current_collection_id', 'correct_collection_id']
        sources_in_wrong_collection = [headers.copy()]
        sources_not_in_any_collection = [headers.copy()]
        for source in sources:
            if source["pub_state"]and source["pub_country"] == "USA" :
                if source["id"] in self.sources_lookup:
                    collection_ids = self.sources_lookup[source["id"]]
                    for collection_id in collection_ids:
                        state_code = self.states_code_lookup[collection_id]
                        if not state_code:
                            logger.info("Adding source with [%s] to sources_in_wrong_collection list", source["id"])
                            sources_in_wrong_collection.append([source['id'], source['label'], source['homepage'], source['pub_state'],
                                 source['stories_per_week'], self.collection_lookup.get(source['pub_state'], collection_id)])
                else:
                    logger.info("Adding source with [%s] to sources_not_in_any_collection list", source["id"])
                    sources_not_in_any_collection.append([source['id'], source['label'], source['homepage'], source['pub_state'],
                                 source['stories_per_week'], self.collection_lookup.get(source['pub_state']), ''])
        
        self.write_output("sources_in_wrong_collection.csv", sources_in_wrong_collection)
        self.write_output("sources_not_in_any_collection.csv", sources_not_in_any_collection)


if __name__ == "__main__":
    client = MediaCloudClient()
    app = CollectionStates(client) 
    app.run_process()
    sources = app.get_sources_in_collection(None,100000)
