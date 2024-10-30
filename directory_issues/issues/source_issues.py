from issues import IssueBase
from typing import TypeVar, Tuple, Generic, Type, Dict, Callable, List, Any
import datetime as dt
from jinja2 import Environment, FileSystemLoader, select_autoescape
from collections import defaultdict
from ..classes import Source


###Eventually manage this via pkg_resources
import os
template_dir = os.path.join(os.path.dirname(__file__), 'templates')

jinja_env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape()
)


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




