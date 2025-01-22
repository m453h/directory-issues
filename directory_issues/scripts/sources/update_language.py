import logging
import datetime as dt
import pandas as pd
from typing import Optional, List
from directory_issues.scripts.sources.base import SourcesBase, MediaCloudClient

logger = logging.getLogger(__name__)


class SourceLanguage(SourcesBase):
    result_column = "primary_language"

    def analyze_source(self, domain: str, min_story_count: int = 100) -> Optional[str]:
        """
        Analyze a single source to get its primary language.

        Args:
            domain (str): Domain to analyze.
            min_story_count (int): Minimum number of stories to consider the source valid.

        Returns:
            Optional[str]: The primary language of the source or None if not enough data.
        """
        query = f"canonical_domain:{domain}"
        start_date = dt.datetime.now() - dt.timedelta(days=365)
        end_date = dt.datetime.now()

        results = self.provider._overview_query(query, start_date, end_date)

        if results["total"] <= min_story_count or self.provider._is_no_results(results):
            return None

        languages = [match["language"] for match in results["matches"]]
        return max(set(languages), key=languages.count)


if __name__ == "__main__":
    client = MediaCloudClient()

    lang_analyzer = SourceLanguage(client)
    lang_results = lang_analyzer.process_sources(
        platform="online_news", batch_size=100, file_name="language"
    )
