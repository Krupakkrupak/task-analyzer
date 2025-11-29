# Smart Task Analyzer

A mini Django application that helps prioritize tasks using a custom scoring algorithm based on **urgency**, **importance**, **effort**, and **dependencies**.

## Project Structure

```text
task-analyzer/
├── backend/                  # Django project
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── tasks/                    # App with API + scoring logic
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py
│   ├── scoring.py
│   ├── views.py
│   ├── urls.py
│   └── migrations/ (auto-created after first migrate)
├── frontend/                 # Static frontend
│   ├── index.html
│   ├── styles.css
│   └── script.js
├── manage.py
├── db.sqlite3 (created after migrate)
└── requirements.txt
```

## Scoring Algorithm Overview

Implemented in `tasks/scoring.py` as `calculate_task_score(task_data)`.

The score is built from:

- **Urgency (due date)**
  - Overdue: `+100`
  - Due today or tomorrow: `+70`
  - Due within 3 days: `+50`
  - Due within 7 days: `+30`
  - Later than 7 days: `+10`
  - Missing/invalid date: `+20` (medium urgency)

- **Importance (1–10)**
  - Default: `5` if missing or invalid
  - Clamped between 1 and 10
  - Score contribution: `importance * 5`

- **Effort (estimated_hours)**
  - `<= 1h`: `+15` (very quick win)
  - `< 2h`: `+10`
  - `2–4h`: `+5`
  - `> 4h`: `+0`

- **Dependencies**
  - If the task has any dependencies: `-10` (slightly deprioritized because it may be blocked)

**Why urgency > effort?**

For most real-world workflows, **missing a deadline** is more costly than spending a bit more time on a task. So urgency and importance dominate the score, while effort is used as a tie-breaker that favors quick wins.

## API Endpoints

All APIs are under `http://127.0.0.1:8000/api/tasks/`.

- `POST /api/tasks/analyze/`
  - Body: either `[{...}, {...}]` or `{ "tasks": [{...}] }`
  - Returns: `{ "tasks": [ { original + score }, ... ] }` sorted by descending score.

- `GET` or `POST /api/tasks/suggest/`
  - If POST, accepts same body as `/analyze/`.
  - If no tasks are provided, returns sample tasks.
  - Returns: top 3 tasks with a human-readable `explanation` field.

Each task can contain:

```json
{
  "title": "Write report",
  "due_date": "2025-12-01",   // string or date
  "importance": 8,             // 1-10
  "estimated_hours": 3,
  "dependencies": [1, 2]
}
```

Missing fields are handled gracefully (defaults are applied).

## Frontend Usage

Open `frontend/index.html` directly in your browser (or serve it via a simple static server).

- Left side: paste tasks JSON and choose a **Sorting Strategy**.
- Click **Analyze** to call `/api/tasks/analyze/`.
- Click **Suggest for Today** to call `/api/tasks/suggest/`.
- Right side: view color-coded task cards with scores and explanations.

## Running the Project (Setup Instructions)

1. **Create and activate virtual environment** (recommended):

```bash
python -m venv venv
# Windows
venv\\Scripts\\activate
# macOS / Linux
source venv/bin/activate
```

2. **Install dependencies**:

```bash
pip install -r requirements.txt
```

3. **Run migrations**:

```bash
python manage.py migrate
```

4. **Start the development server**:

```bash
python manage.py runserver
```

The backend will be available at: `http://127.0.0.1:8000/`.

5. **Open the UI**:

With the server running, open your browser at `http://127.0.0.1:8000/`. Paste tasks as JSON in the left panel, choose a sorting strategy, and click **Analyze** or **Suggest for Today** to see prioritized tasks on the right.

## Detailed Algorithm Explanation

The Smart Task Analyzer assigns each task a numerical score representing its priority. The goal is to help a user quickly decide **what to do next** by combining four core factors: urgency, importance, effort, and dependencies. A higher score means a higher priority.

**1. Urgency (due date)**  
The `due_date` is parsed into a `date` object (accepting common string formats). I compare it with today to compute `days_until_due`. Overdue tasks get the largest boost (`+100`) because they are already late. Tasks due today or tomorrow are treated as very urgent (`+70`), followed by tasks due within three days (`+50`), then within a week (`+30`), and finally tasks with a distant deadline (`+10`). If a task has no valid `due_date`, it receives a medium urgency bonus (`+20`) instead of being ignored. This ensures tasks with missing dates are not lost but do not overshadow clearly urgent work.

**2. Importance (1–10 scale)**  
The `importance` field is expected on a 1–10 scale. Invalid or missing values are coerced to a default of 5 and clamped into the range [1, 10]. The contribution to the score is `importance * 5`, which makes importance one of the dominant factors. This models the idea that highly impactful work should usually win over low-impact busywork, even if deadlines are similar.

**3. Effort (estimated_hours)**  
Effort is used to favor "quick wins". Tasks with very low `estimated_hours` (≤ 1 hour) get the biggest bonus (`+15`), followed by tasks under two hours (`+10`), and then moderate tasks up to four hours (`+5`). Large tasks (> 4 hours) do not receive an effort bonus. This encourages picking off small, valuable tasks when possible, while still allowing big, important tasks to rank high due to urgency and importance.

**4. Dependencies**  
Finally, tasks with non-empty `dependencies` arrays receive a small penalty (`-10`). This represents that blocked work is slightly less attractive than tasks that can be started immediately. The penalty is small compared to urgency and importance, so a very critical blocked task can still appear near the top.

Overall, urgency and importance dominate the score, effort nudges quick wins upward, and dependencies gently push blocked work down. This produces a "smart balance" between not missing deadlines, focusing on impact, and taking advantage of quick, easy tasks.

## Design Decisions

- **Backend-focused scoring, frontend sorting**  
  The main intelligence lives in the backend (`calculate_task_score`). The frontend applies alternative sorting strategies (Fastest Wins, High Impact, Deadline Driven, Smart Balance) on the same scored list. This keeps the core logic testable in Python while allowing UX flexibility without changing the API.

- **Simple JSON APIs instead of full CRUD**  
  The assignment goal is analysis, not full task management. I chose two POST endpoints (`/analyze/` and `/suggest/`) that accept an in-memory list of tasks as JSON. This keeps the API demo-friendly and avoids extra forms or authentication.

- **Graceful handling of messy data**  
  Instead of failing when `due_date` or `importance` is missing, the algorithm applies sensible defaults (medium urgency, importance 5). This reflects real-world inputs and prevents one bad field from breaking the whole request.

- **Plain HTML/CSS/JS frontend**  
  The frontend is implemented using HTML5, CSS3, and vanilla JavaScript, served by Django as a template. This matches the assignment requirements and avoids framework overhead while still providing a clean two-column UI and interactive analysis.

## Time Breakdown (Approximate)

- **Project setup (Django project, app, wiring)**: ~20–30 minutes  
- **Data model and scoring algorithm**: ~40–50 minutes  
- **API endpoints and URL routing**: ~30 minutes  
- **Frontend UI (layout, styling, basic interactivity)**: ~45–60 minutes  
- **Sorting strategies / critical thinking element**: ~20–30 minutes  
- **Testing, debugging, and edge cases**: ~30 minutes  
- **Documentation and README polishing**: ~20–30 minutes

## Bonus Challenges

- ✅ Implemented multiple **sorting strategies** in the UI:
  - Fastest Wins (low effort first)
  - High Impact (importance first)
  - Deadline Driven (closest due date first)
  - Smart Balance (combined score from urgency + importance + effort + dependencies)

- ✅ Graceful handling of **edge cases**:
  - Very old due dates (e.g. 1990)
  - Missing importance or due date
  - Blocked tasks with dependencies

- ☐ Advanced UI framework (React/Angular) – intentionally kept to vanilla JS as requested.  
- ☐ Authentication or multi-user accounts.

## Future Improvements

- **Personalized weights per user**  
  Learn from which tasks the user actually completes first and adjust the weighting of urgency vs importance vs effort to better match their behavior.

- **Project-level views and what-if scenarios**  
  Group tasks into projects and answer questions like "What should I do if I only have 2 hours today?" by selecting an optimal subset of tasks.

- **Calendar / external tool integration**  
  Integrate with a calendar or task system (e.g. Google Calendar, Jira) to import real deadlines and keep urgency up to date.

- **Richer explanations and visualizations**  
  Show a breakdown of the score (bars for urgency, importance, effort, dependencies) and present more detailed textual explanations.

- **Persistence and user accounts**  
  Store tasks in the database and add simple authentication so users can return to their prioritized list instead of pasting JSON each time.
#   t a s k - a n a l y z e r  
 