from issues import IssueBase
from typing import TypeVar, Tuple, Generic, Type, Dict, Callable, List, Any


class StringIssue(IssueBase[str]):
    _ISSUES: Dict[str, Type["StringIssue"]] = {}


@StringIssue.register("long_str")
class StringLengthIssue(StringIssue):
    def calculate(self, payload: str) -> Tuple[bool, Any]:
        return len(payload) > 10, {"value":payload}

    def render_template(self):
        return f"{self.result['value']} is too long"

@StringIssue.register("short_str")
class StringShortIssue(StringIssue):
    def calculate(self, payload: str) -> Tuple[bool, Any]:
        return len(payload) < 10, {"value": payload}

    def render_template(self):
        return f"{self.result['value']} is too short"

@StringIssue.register("dup_letter", tags=["letter"])
class DupLetterIssue(StringIssue):
    def calculate(self, payload:str):
        duplicate = (len(set(payload)) != len(payload))
        return duplicate, {"value": payload}

    def render_template(self):
        return f"{self.result['value']} contains duplicate letters"

@StringIssue.register("no_a", tags=["letter"])
class NoAIssue(StringIssue):
    def calculate(self, payload:str):
        match = "A" not in payload
        return match, {"value": payload}

    def render_template(self):
        return f"{self.result['value']} does not contain the letter 'a'"






class IntIssue(IssueBase[int]):
    _ISSUES: Dict[str, Type["IntIssue"]] = {}

@IntIssue.register("is_even")
class IntEvenIssue(IntIssue):
    def calculate(self, payload: int) -> Tuple[bool, Any]:
        return payload%2 == 0, {"value":payload}

    def render_template(self):
        return f"{self.result['value']} is even"


@IntIssue.register("broken_issue", tags=["breaking"])
class BreakingIssue(IntIssue):
    def calculate(self, payload:int):
        raise RuntimeError("Intentional Error")

    def render_template(self):
        return "A broken issue"