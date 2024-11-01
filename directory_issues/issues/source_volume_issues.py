from . import IssueBase
from typing import TypeVar, Tuple, Generic, Type, Dict, Callable, List, Any
import datetime as dt

from ..classes import SourceVolumePayload

class SourceVolumeIssue(IssueBase["SourceVolumePayload"]):
    _ISSUES: Dict[str, Type["SourceVolumePayload"]] = {}


"""
EX:
content falls
content spikes
recent volume is low
total volume is low

"""