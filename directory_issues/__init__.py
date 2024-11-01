from .issues.source_issues import SourceIssue
from .classes import SourcePayload, SourceVolumePayload, CollectionPayload
from collections import defaultdict
import datetime as dt 
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic_settings import BaseSettings
import mediacloud.api as mc_api

###Eventually manage this via pkg_resources
import os
template_dir = os.path.join(os.path.dirname(__file__), 'templates')

jinja_env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape()
)

class Config(BaseSettings):
    mc_api_token:str|None=None
    #No collections should have more than this many sources
    # so just set it high so we don't have to worry about paging. 
    mc_api_limit:int=10000 

config = Config()

class Source():
    """
    Issue detection and reporting logic for a single source. 
    """
    
    @classmethod
    def from_id(cls, source_id:int, skip_volume:bool = False):
        mc_client = mc_api.DirectoryApi(config.mc_api_token)
        source = mc_client.source(source_id)
        return Source(source, skip_volume=skip_volume)

    def __init__(self, data: dict, skip_volume: bool = True):
        #NB- we have no mediacloud directory .get_source(id)- 
        self.source_data = SourcePayload(data)
        if(not skip_volume):
            self.source_volume = self.get_source_volume()
        else:
            self.source_volume = None

        #This will also contain a mechanism for searching against this source to get a volume over time value
        #which can also be used as a metric input- probably against a source_volume_payload?

        self.source_issues = None

    def __repr__(self):
        return f"Source({self.source_data.name}, {self.source_data.homepage})"


    def get_source_volume(self):
        mc_client = mc_api.SearchApi(config.mc_api_token)
        volumes = {}
        today = dt.date.today()
        month_ago = dt.date.today() - dt.timedelta(days=30)
        
        recent = mc_client.story_count("*", month_ago, today, source_ids=[self.source_data.id])
        volumes["recent_volume"] = recent["total"]

        recent_hist = mc_client.story_count_over_time("*", month_ago, today, source_ids=[self.source_data.id])
        volumes["recent_histogram"] = recent_hist

        years_ago = dt.date.today() - dt.timedelta(days=365 * 10)
        total_count = mc_client.story_count("*", years_ago, today, source_ids=[self.source_data.id])
        volumes["total_volume"] = total_count["total"]
        return SourceVolumePayload(volumes)



    def find_issues(self, include_tags=None, exclude_tags=None):
        self.source_issues = SourceIssue.calculate_all(self.source_data, include_tags=include_tags, exclude_tags=exclude_tags)


    def render_template(self):
        if not self.source_issues:
            self.find_issues()

        grouped_issues = defaultdict(list)

        for issue in self.source_issues:
            primary_tag = issue['tags'][0] if issue['tags'] else 'no_tag'
            grouped_issues[primary_tag].append(issue['template'])
        
        link = f"https://search.mediacloud.org/sources/{self.source_data.id}"

        datestr = dt.datetime.now().strftime("%I:%M%p on %B %d, %Y")

        source_message_template = jinja_env.get_template("source_issues_message.j2")

        source_message = source_message_template.render(
            source=self.source_data, 
            run_date=datestr,
            link=link, 
            issues=grouped_issues)

        return source_message


class Collection():

    @classmethod
    def from_id(cls, collection_id:int):
        mc_client = mc_api.DirectoryApi(config.mc_api_token)
        collection = mc_client.collection(collection_id)
        return Collection(collection)

    def __init__(self, data:dict):
        
        self.collection_data = CollectionPayload(data)

        self.mc_client = mc_api.DirectoryApi(config.mc_api_token)
        
        sources = self.mc_client.source_list(collection_id=self.collection_data.id, limit=config.mc_api_limit)

        self.sources = [Source(s) for s in sources["results"]]

    def find_all_issues(self, include_tags=None, exclude_tags=None):
        for source in self.sources:
            source.find_issues(include_tags, exclude_tags)

    def render_source_templates(self):
        templates = []
        for source in self.sources:
            t = source.render_template()
            templates.append(t)

        return templates

    def render_template(self):
        return f"Collection({self.collection_data.name})"
        

