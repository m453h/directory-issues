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

    def __repr__(self):
        return f'SourceVolume({self.total_volume} stories)'


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


