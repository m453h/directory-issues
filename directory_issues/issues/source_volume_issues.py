from . import IssueBase
from typing import TypeVar, Tuple, Generic, Type, Dict, Callable, List, Any
import datetime as dt

from ..classes import SourceVolumePayload

class SourceVolumeIssue(IssueBase["SourceVolumePayload"]):
    _ISSUES: Dict[str, Type["SourceVolumePayload"]] = {}


@SourceVolumeIssue.register("recent-zero", tags=["generic"])
class RecentVolumeZero(SourceVolumeIssue):   

    def calculate(self, payload:SourceVolumePayload):
        if payload.recent_volume == 0:
            return True, {"name":payload.name}
        
        return False, None

    def render_template(self):
        return f"{self.result['name']}: System status is not 'working'"

"""
EX:
content falls
content spikes
recent volume is low
total volume is low

"""