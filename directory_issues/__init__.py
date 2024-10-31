from .issues.source_issues import SourceIssue
from .classes import SourcePayload
from collections import defaultdict
import datetime as dt 
from jinja2 import Environment, FileSystemLoader, select_autoescape

###Eventually manage this via pkg_resources
import os
template_dir = os.path.join(os.path.dirname(__file__), 'templates')

jinja_env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape()
)


class Source():
    
    def __init__(self, data: dict):
        self.source_data = SourcePayload(data)

        self.link = f"https://search.mediacloud.org/sources/{self.source_data.id}"
        
        #This will also contain a mechanism for searching against this source to get a volume over time value
        #which can also be used as a metric input

        self.issues = None

    def __repr__(self):
        return f"Source({self.source_data.name}, {self.source_data.homepage})"

    def find_issues(self, include_tags=None, exclude_tags=None):
        self.issues = SourceIssue.calculate_all(self.source_data, include_tags=include_tags, exclude_tags=exclude_tags)

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

        source_message = source_message_template.render(
            source=self.source_data, 
            run_date=datestr,
            link=self.link, 
            issues=self.grouped_issues)
        return source_message