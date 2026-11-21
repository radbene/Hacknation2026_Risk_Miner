from riskminer.models.tables import *  # noqa: F401,F403
from riskminer.models.tables import Base, ReviewStatus, Tier  # noqa: F401

REVIEWABLE = {
    "project": "Project",
    "project_procedure": "ProjectProcedure",
    "contract": "Contract",
    "contract_change": "ContractChange",
    "fact": "Fact",
    "document": "Document",
    "risk_category": "RiskCategory",
    "lesson": "Lesson",
    "clause": "Clause",
    "event": "Event",
    "data_issue": "DataIssue",
    "analysis": "Analysis",
    "analysis_item": "AnalysisItem",
}
