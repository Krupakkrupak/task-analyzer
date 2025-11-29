from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict


def _parse_due_date(value: Any) -> date | None:
    """Safely parse different due_date formats into a date object."""
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return None


def calculate_task_score(task_data: Dict[str, Any]) -> float:
    """Calculate a priority score for a task.

    Higher score = Higher priority.
    Handles missing fields and past-due dates gracefully.
    """
    score = 0.0

    today = date.today()
    due_date = _parse_due_date(task_data.get("due_date"))

    # 1. Urgency Calculation
    if due_date is None:
        # Unknown due date: treat as medium urgency
        score += 20
    else:
        days_until_due = (due_date - today).days
        if days_until_due < 0:
            # OVERDUE! Huge priority boost
            score += 100
        elif days_until_due <= 1:
            score += 70
        elif days_until_due <= 3:
            score += 50
        elif days_until_due <= 7:
            score += 30
        else:
            score += 10

    # 2. Importance Weighting (default to 5 if missing)
    importance = task_data.get("importance")
    try:
        importance_val = int(importance) if importance is not None else 5
    except (TypeError, ValueError):
        importance_val = 5
    importance_val = max(1, min(10, importance_val))
    score += importance_val * 5

    # 3. Effort (Quick wins logic)
    hours = task_data.get("estimated_hours")
    try:
        hours_val = float(hours) if hours is not None else 1.0
    except (TypeError, ValueError):
        hours_val = 1.0

    if hours_val <= 1:
        score += 15
    elif hours_val < 2:
        score += 10
    elif hours_val <= 4:
        score += 5

    # 4. Dependencies (penalize tasks that are blocked)
    dependencies = task_data.get("dependencies") or []
    if isinstance(dependencies, (list, tuple)) and len(dependencies) > 0:
        score -= 10

    return score
