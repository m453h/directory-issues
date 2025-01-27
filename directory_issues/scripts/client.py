import os
import logging
import pandas as pd
import mediacloud.api as mc_api
from dotenv import load_dotenv
from typing import Generator, Optional, List
from mc_providers import provider_for, PLATFORM_ONLINE_NEWS, PLATFORM_SOURCE_MEDIA_CLOUD


logger = logging.getLogger(__name__)


class MediaCloudClient:
    def __init__(self):
        load_dotenv()
        self.base_url = os.getenv("MC_ELASTICSEARCH_BASE_URL")
        self.api_token = os.getenv("MC_API_TOKEN")

        if not self.base_url:
            raise ValueError(
                "MC_ELASTICSEARCH_BASE_URL environment variable is required"
            )
        if not self.api_token:
            raise ValueError("MC_API_TOKEN environment variable is required")

        self.directory_client = mc_api.DirectoryApi(self.api_token)
        self.provider = self._initialize_provider()

    def _initialize_provider(self):
        return provider_for(
            PLATFORM_ONLINE_NEWS, PLATFORM_SOURCE_MEDIA_CLOUD, base_url=self.base_url
        )

    def get_sources(
        self, platform: Optional[str] = None, batch_size: int = 100, offset: int = 0
    ) -> Generator[List[str], None, None]:
        try:
            response = self.directory_client.source_list(
                platform=platform, limit=batch_size, offset=offset
            )
            sources = [source["name"] for source in response.get("results", [])]
            yield sources

            offset += batch_size
            print(f"Fetched batch of {len(sources)} sources. Total offset: {offset}")

        except Exception as e:
            print(f"Error fetching sources: {str(e)}")
            raise
