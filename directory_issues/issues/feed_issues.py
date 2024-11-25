from . import IssueBase
from typing import TypeVar, Tuple, Generic, Type, Dict, Callable, List, Any
import datetime as dt

from ..classes import FeedPayload


class FeedIssue(IssueBase["FeedPayload"]):
    _ISSUES: Dict[str, Type["FeedPayload"]] = {}


@FeedIssue.register("not-working", tags=["generic"])
class NotWorking(FeedIssue):   

    def calculate(self, payload:FeedPayload):
        if payload.system_status != "Working":
            return True, {"name":payload.name}
        
        return False, None

    def render_template(self):
        return f"{self.result['name']}: System status is not 'working'"

