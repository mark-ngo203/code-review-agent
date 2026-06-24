from models.context_model import ContextModel
from models.finding_model import FindingModel

MOCK_CONTEXT = ContextModel(
    summary="Mock: fetches user financial data from a database.",
    data_classification="Financial",
    risk_profile="HIGH",
    dependencies=["financial_db"],
)

MOCK_SECURITY_FINDINGS = [
    FindingModel(
        severity="CRITICAL",
        issue_type="SQL Injection",
        description="Mock finding: user_id interpolated into SQL.",
        action="Use parameterized queries.",
        line_number=4,
    ),
]

MOCK_PERFORMANCE_FINDINGS = [
    FindingModel(
        severity="HIGH",
        issue_type="N+1 Queries",
        description="Mock finding: one query per transaction in a loop.",
        action="Fetch transactions in a single JOIN query.",
        line_number=12,
    ),
]
