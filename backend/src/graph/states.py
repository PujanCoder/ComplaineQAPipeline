import operator
from typing import Annotated, Any, List, Optional , Dict, TypedDict

class ComplainceIssues(TypedDict):
    catergory: str
    description: str
    severity: str
    timestamp: str


class VideoAuditState(TypedDict):
    video_url: str
    video_id: str


    local_file_path: Optional[str]
    video_metadata: Dict[str, Any]
    transcript: Optional[str]
    ocr_text: List[str]


    compliance_issues: Annotated[List[ComplainceIssues], "List of compliance issues found in the video"]


    final_status : str
    final_report: str



    errors: Annotated[List[str], "List of errors encountered during processing"]
    