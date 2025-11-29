const API_BASE = "/api/tasks";

const inputEl = document.getElementById("tasks-input");
const resultsEl = document.getElementById("results");
const errorEl = document.getElementById("error");
const strategyEl = document.getElementById("strategy");

const analyzeBtn = document.getElementById("analyze-btn");
const suggestBtn = document.getElementById("suggest-btn");

function showError(message) {
    errorEl.textContent = message || "";
}

function parseTasksFromInput() {
    const raw = inputEl.value.trim();
    if (!raw) {
        return [];
    }

    try {
        const data = JSON.parse(raw);
        if (Array.isArray(data)) {
            return data;
        }
        if (Array.isArray(data.tasks)) {
            return data.tasks;
        }
        showError("JSON must be an array of tasks or an object with a 'tasks' array.");
        return null;
    } catch (e) {
        showError("Invalid JSON: " + e.message);
        return null;
    }
}

function sortClientSide(tasks) {
    const strategy = strategyEl.value;
    if (strategy === "fast") {
        return [...tasks].sort((a, b) => {
            const ah = Number(a.estimated_hours ?? 0);
            const bh = Number(b.estimated_hours ?? 0);
            return ah - bh;
        });
    }
    if (strategy === "impact") {
        // High Impact: importance first, then score as tie-breaker
        return [...tasks].sort((a, b) => {
            const ai = Number(a.importance ?? 0);
            const bi = Number(b.importance ?? 0);
            if (ai !== bi) {
                return bi - ai; // higher importance first
            }
            const ascore = Number(a.score ?? 0);
            const bscore = Number(b.score ?? 0);
            return bscore - ascore;
        });
    }
    if (strategy === "deadline") {
        return [...tasks].sort((a, b) => {
            const ad = a.due_date || "9999-12-31";
            const bd = b.due_date || "9999-12-31";
            return ad.localeCompare(bd);
        });
    }
    // Smart Balance or anything else: rely on backend score (already sorted)
    // Backend already sorted by our composite score, but re-sort defensively.
    return [...tasks].sort((a, b) => {
        const ascore = Number(a.score ?? 0);
        const bscore = Number(b.score ?? 0);
        return bscore - ascore;
    });
}

function renderTasks(tasks) {
    resultsEl.innerHTML = "";
    if (!tasks || tasks.length === 0) {
        resultsEl.innerHTML = "<p>No tasks to show yet.</p>";
        return;
    }

    const sorted = sortClientSide(tasks);

    sorted.forEach((task) => {
        const card = document.createElement("div");
        card.className = "task-card";

        const header = document.createElement("div");
        header.className = "task-header";

        const title = document.createElement("div");
        title.className = "task-title";
        title.textContent = task.title || "Untitled Task";

        const score = document.createElement("div");
        score.textContent = task.score != null ? `Score: ${task.score.toFixed(1)}` : "";

        header.appendChild(title);
        header.appendChild(score);

        const meta = document.createElement("div");
        meta.className = "task-meta";

        const imp = Number(task.importance ?? 5);
        let badgeClass = "badge-medium";
        let badgeLabel = "Medium";
        if (imp >= 8) {
            badgeClass = "badge-high";
            badgeLabel = "High";
        } else if (imp <= 4) {
            badgeClass = "badge-low";
            badgeLabel = "Low";
        }

        const badge = document.createElement("span");
        badge.className = `badge ${badgeClass}`;
        badge.textContent = `${badgeLabel} Priority`;

        const dueText = task.due_date ? `Due: ${task.due_date}` : "Due: (not specified)";
        const hoursText = `Estimated: ${task.estimated_hours ?? "?"}h`;

        meta.appendChild(badge);
        meta.insertAdjacentText("beforeend", ` • ${dueText} • ${hoursText}`);

        const explanation = document.createElement("div");
        explanation.className = "task-explanation";
        if (task.explanation) {
            explanation.textContent = task.explanation;
        } else {
            explanation.textContent = "This task has been scored based on urgency, importance, effort, and dependencies.";
        }

        card.appendChild(header);
        card.appendChild(meta);
        card.appendChild(explanation);

        resultsEl.appendChild(card);
    });
}

async function callAnalyze() {
    showError("");
    const tasks = parseTasksFromInput();
    if (tasks === null) return;

    try {
        const res = await fetch(`${API_BASE}/analyze/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ tasks }),
        });

        if (!res.ok) {
            throw new Error(`Server error: ${res.status}`);
        }

        const data = await res.json();
        renderTasks(data.tasks || []);
    } catch (err) {
        showError("Failed to analyze tasks: " + err.message);
    }
}

async function callSuggest() {
    showError("");
    const tasks = parseTasksFromInput();

    try {
        const res = await fetch(`${API_BASE}/suggest/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ tasks: tasks || [] }),
        });

        if (!res.ok) {
            throw new Error(`Server error: ${res.status}`);
        }

        const data = await res.json();
        renderTasks(data.tasks || []);
    } catch (err) {
        showError("Failed to get suggestions: " + err.message);
    }
}

analyzeBtn.addEventListener("click", () => {
    callAnalyze();
});

suggestBtn.addEventListener("click", () => {
    callSuggest();
});
