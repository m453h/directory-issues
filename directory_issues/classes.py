import datetime as dt

class SourcePayload():
    """
    Data type for a Source
    """
    
    def __init__(self, data: dict):
        self.id: int = data.get("id")
        self.name: str = data.get("name")
        self.url_search_string: str = data.get("url_search_string")
        self.label: str = data.get("label")
        self.homepage: str = data.get("homepage")
        self.notes: Optional[str] = data.get("notes")
        self.platform: str = data.get("platform")
        self.stories_per_week: int = data.get("stories_per_week")
        self.first_story: Optional[str] = data.get("first_story")
        self.created_at: datetime = dt.datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        self.modified_at: datetime = dt.datetime.fromisoformat(data["modified_at"].replace("Z", "+00:00"))
        self.pub_country: str = data.get("pub_country")
        self.pub_state: str = data.get("pub_state")
        self.primary_language: Optional[str] = data.get("primary_language")
        self.media_type: str = data.get("media_type")
        self.collection_count: int = data.get("collection_count")

        self.issues = None

    def __repr__(self):
        return f"SourcePayload({self.name})"

class SourceVolumePayload():
    """
    Data type for a source volume summary. count-over-time and count
    """
    def __init__(self, data: dict):
        self.recent_volume = data.get("recent_volume")
        self.recent_histogram = data.get("recent_histogram")
        self.total_volume = data.get("total_volume")

        self.issues = None

    def __repr__(self):
        return f'SourceVolume({self.total_volume} stories)'


class FeedPayload():
    """
    Data type for a feed
    """
    def __init__(self, data: dict):
        self.id = data.get("id")
        self.url = data.get("url")
        self.admin_rss_enabled = data.get("admin_rss_enabled")
        self.source = data.get("source")
        self.name = data.get("name")
        self.rss_title = data.get("rss_title")

        self.active = data.get("active")
        self.system_status = data.get("system_status")
        self.system_enabled = data.get("system_enabled")

        self.last_fetch_attempt = data.get("last_fetch_attempt")
        self.last_fetch_success = data.get("last_fetch_success")
        self.last_fetch_hash = data.get("last_fetch_hash")
        self.last_fetch_failured = data.get("last_fetch_failures")

        self.next_fetch_attempt = data.get("next_fetch_attempt")
        self.last_new_stories = data.get("last_new_stories")
        self.created_at = data.get("created_at")

        self.http_etag = data.get("http_etag")
        self.http_last_modified = data.get("http_last_modified")

        self.queued = data.get("queued")

        self.update_minutes = data.get("update_minutes")
        self.http_304 = data.get("http_304")
        self.poll_minutes = data.get("poll_minutes")

        self.issues = None

    def __repr__(self):
        return f"Feed({self.id}:{self.name})"




class CollectionPayload():
    """
    Data type for a Collection
    """
    def __init__(self, data:dict):
        self.id = data.get('id')
        self.name = data.get('name')
        self.notes = data.get('notes')
        self.platform = data.get('platform')
        self.source_count = data.get('source_count')
        self.public = data.get('public')
        self.featured = data.get('featured')
        self.managed = data.get('managed')

    def __repr__(self):
        return f"CollectionPayload({self.name})"


