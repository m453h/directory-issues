import datetime as dt
from typing import Optional
from directory_issues.scripts.sources.base import SourcesBase, MediaCloudClient


class SourcesPublicationDate(SourcesBase):
    def __init__(self, client):
        super().__init__(client)
        self.result_column = "first_publication_date"

    def analyze_source(
        self, domain: str, min_story_count: int = 100
    ) -> Optional[dt.datetime]:
        """Analyze a single source to get its first publication date."""
        query = f"canonical_domain:{domain}"
        start_date = dt.datetime(2000, 1, 1)
        end_date = dt.datetime.now()

        results = self.client.provider._overview_query(query, start_date, end_date)

        if results["total"] <= min_story_count or self.client.provider._is_no_results(
            results
        ):
            return None

        publication_dates = [
            dt.datetime.fromisoformat(match["publication_date"])
            for match in results["matches"]
        ]
        return min(publication_dates, default=None)


if __name__ == "__main__":
    client = MediaCloudClient()
    pub_date_analyzer = SourcesPublicationDate(client)
    pub_results = pub_date_analyzer.process_sources(
        platform="online_news", batch_size=10000, file_name="publication_date"
    )
