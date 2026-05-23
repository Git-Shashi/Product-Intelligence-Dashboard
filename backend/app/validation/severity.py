from app.db.models import Severity

SEVERITY_PENALTY = {
    Severity.HIGH: 20,
    Severity.MEDIUM: 10,
    Severity.LOW: 3,
}


def compute_quality_score(issue_severities: list[Severity]) -> int:
    """Start at 100, subtract penalties per issue, floor at 0."""
    score = 100
    for sev in issue_severities:
        score -= SEVERITY_PENALTY.get(sev, 0)
    return max(0, score)
