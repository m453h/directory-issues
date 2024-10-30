import logging
from typing import TypeVar, Tuple, Generic, Type, Dict, Callable, List, Any

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Define type variables for different payloads
T = TypeVar('T', bound=Any) 

class IssueBase(Generic[T]):
    """
    For centralizing the issue aggregation logic for each class of issue
    """
    _ISSUES: Dict[str, Type['IssueBase']] = {}
    issue_name = "Base Issue"

    @classmethod
    def register(cls, issue_name: str, tags:List[str]=None) -> Callable:
        """Class decorator to register issues
        """
        if tags is None:
            tags = []

        def decorator(issue_cls: Type['IssueBase']) -> Type['IssueBase']:
            issue_cls._tags = tags
            issue_cls.issue_name = issue_name
            cls._ISSUES[issue_name] = issue_cls
            return issue_cls
        return decorator

    def calculate(self, payload: T) -> Tuple[bool, Any]:
        """Override this method in subclasses to perform issue calculation."""
        raise NotImplementedError("Subclasses must implement this method.")

    def render_template(self) -> str:
        return f"Default {self._name} result" 

    @classmethod
    def calculate_all(
        cls, 
        payload: Any, 
        include_tags: List[str] = None,
        exclude_tags: List[str] = None 
    ) -> Dict[str, Any]:
        """
        Calculate all issues matching include_tags and not matching exclude_tags
        """
        results = []
        for issue_name, issue_cls in cls._ISSUES.items():
            issue_tags = issue_cls._tags

            # Check for inclusion: If include_tags is None, include all metrics.
            if include_tags is not None and not any(tag in include_tags for tag in issue_tags):
                continue  
            
            # Check for exclusion: If exclude_tags are provided, skip if any tag matches.
            if exclude_tags is not None and any(tag in exclude_tags for tag in issue_tags):
                continue  
                
            try:
                issue_instance = issue_cls()  # Instantiate the issue
                is_issue, result_data = issue_instance.calculate(payload)
                issue_instance.result = result_data  # Store the result on the instance
                if is_issue:
                    # Append issue info with rendered template if the issue is present
                    results.append({
                        "issue_name": issue_name,
                        "template": issue_instance.render_template(),
                        "tags": issue_cls._tags
                    })
            except Exception as e:
                logger.error(f"Error calculating issue {issue_name} for payload {payload}: {str(e)}", exc_info=True)
                results.append({
                    "issue_name": issue_name,
                    "tags": issue_cls._tags,
                    "error": True,
                    "error_message": str(e),  # Include the error message in the result
                    "template": f"An error occurred while calculating '{issue_name}'"
                })
        return results

