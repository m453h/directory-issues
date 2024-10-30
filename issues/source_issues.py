from issues import IssueBase
from typing import TypeVar, Tuple, Generic, Type, Dict, Callable, List, Any
import datetime as dt
from jinja2 import Environment, FileSystemLoader, select_autoescape
from collections import defaultdict


###Eventually manage this via pkg_resources
import os
template_dir = os.path.join(os.path.dirname(__file__), 'templates')

jinja_env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape()
)

class Source():
    
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

        self.link = f"https://search.mediacloud.org/sources/{self.id}"
        
        #This will also contain a mechanism for searching against this source to get a volume over time value
        #which can also be used as a metric input

        self.issues = None

    def __repr__(self):
        return f"Source({self.name}, {self.homepage})"

    def find_issues(self, include_tags=None, exclude_tags=None):
        self.issues = SourceIssue.calculate_all(self, include_tags=include_tags, exclude_tags=exclude_tags)

        grouped_issues = defaultdict(list)
        for issue in self.issues:
            primary_tag = issue['tags'][0] if issue['tags'] else 'no_tag'
            grouped_issues[primary_tag].append(issue['template'])
        self.grouped_issues = grouped_issues

    def render_template(self):
        if not self.issues:
            self.find_issues()

        datestr = dt.datetime.now().strftime("%I:%M%p on %B %d, %Y")

        source_message_template = jinja_env.get_template("source_issues_message.j2")

        source_message = source_message_template.render(source=self, run_date=datestr)
        return source_message


class SourceIssue(IssueBase["Source"]):
    _ISSUES: Dict[str, Type["Source"]] = {}


@SourceIssue.register("USS-*-Prefix", tags=["url_search_string"])
class USSPrefix(SourceIssue):   

    def calculate(self, payload:Source):
        if payload.url_search_string[0] == '*':
            return True, None
        
        return False, None

    def render_template(self):
        return "url_search_string starts with '*'. Remove this prefix wildcard. "


@SourceIssue.register("USS-HTTP-Prefix", tags=["url_search_string"])
class HTTPPrefix(SourceIssue):

    def calculate(self, payload):
        if payload.url_search_string.startswith("https"):
            return True, {"scheme": 'https'}

        if payload.url_search_string.startswith("http"):
            return True, {"scheme": 'http'}

        return False, None

    def render_template(self):
        return f"url_search_string starts with {self.result['scheme']}. Remove the prefix http scheme."


@SourceIssue.register("USS-*-Postfix", tags=["url_search_string"])
class USSPostfix(SourceIssue):

    def calculate(self, payload):
        if payload.url_search_string[-1] != "*":
            return True, None
        return False, None

    def render_template(self):
        return "url_search_string does not end in '*'. Add a postfix wildcard."


@SourceIssue.register("Empty-USS", tags=["url_search_string"])
class EmptyUSS(SourceIssue):

    def calculate(self, payload):
        
        if payload.url_search_string == "":
            return True, None

        return False, None

    def render_template(self):
        return "url_search_string is an empty string."


@SourceIssue.register("bad-name", tags=["name"])
class BadName(SourceIssue):

    def calculate(self, payload):
        if " " in payload.name or "." not in payload.name:
            return True, {'name': payload.name}

        return False, None

    def render_template(self):
        return f"Source name ({self.result['name']}) is not a valid canonical domain"





