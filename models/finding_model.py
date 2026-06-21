from pydantic import BaseModel, Field
from typing import Optional

class FindingModel(BaseModel): # Following standard bug report template
    severity: str = Field(description="LOW, MEDIUM, HIGH, CRITICAL")
    issue_type: str = Field(description="The specific bottleneck or vulnerability.")
    description: str = Field(description="Detailed explanation of what should be expected and the flaw.")
    # steps: str = Field(description="Steps on how to reach this issue.")
    action: str = Field(description="Actionable code fix.")
    line_number: Optional[int] = Field(default=None, description="Line number if applicable.")