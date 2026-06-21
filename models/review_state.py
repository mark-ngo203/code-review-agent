from pydantic import BaseModel
from typing import Optional, List

from models.context_model import ContextModel
from models.finding_model import FindingModel 

class ReviewState(BaseModel):
    # Inputs
    code_snippet: str
    
    # Agent Outputs
    context: Optional[ContextModel] = None
    security_findings: List[FindingModel] = [] # Abstracted findings since they're similar, but can seperate them. 
    performance_findings: List[FindingModel] = []
    
    # Final Synthesized Output
    final_report: str = ""