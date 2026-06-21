from pydantic import BaseModel, Field
from typing import List

class ContextModel(BaseModel):
    summary: str = Field(description="High-level summary of the code's purpose.")
    data_classification: str = Field(description="Categorize the data: 'Personally Identifiable Information (PII)', 'Financial', 'Public', or 'Telemetry'.")
    risk_profile: str = Field(description="Overall risk level: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'.")
    dependencies: List[str] = Field(description="External libraries or DB interactions.")