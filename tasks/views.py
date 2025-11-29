import json
from datetime import date
from typing import Any, Dict, List

from django.http import JsonResponse, HttpRequest, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from .scoring import calculate_task_score


def _normalize_task_payload(task: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure task has expected keys and types before scoring."""
    normalized: Dict[str, Any] = {
        "title": task.get("title", "Untitled Task"),
        "due_date": task.get("due_date"),
        "importance": task.get("importance", 5),
        "estimated_hours": task.get("estimated_hours", 1),
        "dependencies": task.get("dependencies", []),
    }
    return normalized


@csrf_exempt
def analyze_tasks(request: HttpRequest) -> JsonResponse:
    """Accepts a list of tasks and returns them sorted by score."""
    if request.method != "POST":
        return HttpResponseBadRequest("Only POST allowed")

    try:
        body = request.body.decode("utf-8") or "{}"
        data = json.loads(body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON body")

    tasks: List[Dict[str, Any]] = data if isinstance(data, list) else data.get("tasks", [])
    scored_tasks: List[Dict[str, Any]] = []

    for task in tasks:
        normalized = _normalize_task_payload(task)
        score = calculate_task_score(normalized)
        enriched = {**task, **normalized, "score": score}
        scored_tasks.append(enriched)

    scored_tasks.sort(key=lambda t: t["score"], reverse=True)

    return JsonResponse({"tasks": scored_tasks})


@csrf_exempt
def suggest_tasks(request: HttpRequest) -> JsonResponse:
    """Return top 3 tasks for "today" with explanations."""
    if request.method not in ("GET", "POST"):
        return HttpResponseBadRequest("Only GET/POST allowed")

    tasks_payload: List[Dict[str, Any]] = []

    if request.method == "POST" and request.body:
        try:
            body = request.body.decode("utf-8")
            data = json.loads(body)
            tasks_payload = data if isinstance(data, list) else data.get("tasks", [])
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON body")

    # Fallback: simple sample tasks if none provided
    if not tasks_payload:
        today = date.today().isoformat()
        tasks_payload = [
            {
                "title": "Finish assignment report",
                "due_date": today,
                "importance": 9,
                "estimated_hours": 3,
                "dependencies": [],
            },
            {
                "title": "Quick inbox cleanup",
                "due_date": today,
                "importance": 5,
                "estimated_hours": 1,
                "dependencies": [],
            },
            {
                "title": "Refactor old code module",
                "due_date": today,
                "importance": 6,
                "estimated_hours": 4,
                "dependencies": [1],
            },
        ]

    scored: List[Dict[str, Any]] = []
    for task in tasks_payload:
        normalized = _normalize_task_payload(task)
        score = calculate_task_score(normalized)
        explanation = _build_explanation(normalized, score)
        enriched = {**task, **normalized, "score": score, "explanation": explanation}
        scored.append(enriched)

    scored.sort(key=lambda t: t["score"], reverse=True)
    top_three = scored[:3]

    return JsonResponse({"tasks": top_three})


def _build_explanation(task: Dict[str, Any], score: float) -> str:
    """Human-friendly explanation for why a task got its score."""
    parts: List[str] = []

    due = task.get("due_date")
    importance = task.get("importance", 5)
    hours = task.get("estimated_hours", 1)
    dependencies = task.get("dependencies", []) or []

    if due:
        parts.append(f"Due date: {due}.")
    else:
        parts.append("No due date provided; treated as medium urgency.")

    parts.append(f"Importance {importance} (1-10 scale).")

    if hours <= 1:
        parts.append("Very quick to finish (<= 1 hour).")
    elif hours < 2:
        parts.append("Quick task (< 2 hours).")
    elif hours <= 4:
        parts.append("Moderate effort (2-4 hours).")
    else:
        parts.append("Larger task (> 4 hours).")

    if dependencies:
        parts.append("Has dependencies, so it may be blocked.")
    else:
        parts.append("No dependencies; can be started immediately.")

    parts.append(f"Final priority score: {score:.1f}.")

    return " ".join(parts)
