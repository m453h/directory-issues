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

class SourceVolumePayload():
    """
    Data type for a source volume summary- count-over-time and count
    """
    def __init__(self, data):
        pass


class CollectionPayload():
    """
    Data type for a Collection
    """
    def __init__(self, data:dict):
        pass

