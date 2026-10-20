const sessionForm = document.querySelector("#session-form");
const sessionStatus = document.querySelector("#session-status");
const sessionSubject = document.querySelector("#session-subject");
const sessionDuration = document.querySelector("#session-duration");
const sessionDate = document.querySelector("#session-date");
const sessionNotes = document.querySelector("#session-notes");
const sessionList = document.querySelector("#session-list");
const subjectBreakdown = document.querySelector("#subject-breakdown");

const statTodayMinutes = document.querySelector("#stat-today-minutes");
const statDailyGoal = document.querySelector("#stat-daily-goal");
const statGoalPercent = document.querySelector("#stat-goal-percent");

const toggleNewSubjectBtn = document.querySelector("#toggle-new-subject");
const newSubjectBox = document.querySelector("#new-subject-box");
const newSubjectName = document.querySelector("#new-subject-name");
const newSubjectColor = document.querySelector("#new-subject-color");
const saveSubjectBtn = document.querySelector("#save-subject-btn");
const cancelSubjectBtn = document.querySelector("#cancel-subject-btn");

const editGoalBtn = document.querySelector("#edit-goal-btn");
const goalForm = document.querySelector("#goal-form");
const goalInput = document.querySelector("#goal-input");

const taskForm = document.querySelector("#task-form");
const taskStatus = document.querySelector("#task-status");
const taskTitle = document.querySelector("#task-title");
const taskType = document.querySelector("#task-type");
const taskSubject = document.querySelector("#task-subject");
const taskDueDate = document.querySelector("#task-due-date");
const taskList = document.querySelector("#task-list");
const taskCountBadge = document.querySelector("#task-count-badge");

function localTodayDate() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

if (sessionDate) sessionDate.value = localTodayDate();
if (taskDueDate) taskDueDate.value = localTodayDate();

const API_BASE =
  window.location.protocol === "file:" || (window.location.port && window.location.port !== "5001")
    ? "http://127.0.0.1:5001"
    : "";

async function request(url, options = {}) {
  const fullUrl = url.startsWith("http") ? url : `${API_BASE}${url}`;
  let response;
  try {
    response = await fetch(fullUrl, options);
  } catch (err) {
    throw new Error(
      "Cannot connect to server. Please ensure the app server is running (e.g. at http://localhost:5001)."
    );
  }
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Something went wrong.");
  return data;
}

function setStatus(target, message = "", isError = false) {
  if (!target) return;
  target.textContent = message;
  target.classList.toggle("error", isError);
}

function formatMinutes(mins) {
  if (mins < 60) return `${mins}m`;
  const hours = Math.floor(mins / 60);
  const remaining = mins % 60;
  return remaining > 0 ? `${hours}h ${remaining}m` : `${hours}h`;
}

let subjectsCache = [];

function populateSubjectSelects(subjects) {
  subjectsCache = subjects;
  const currentSessionVal = sessionSubject.value;
  const currentTaskVal = taskSubject.value;

  sessionSubject.replaceChildren();
  const defaultOption = document.createElement("option");
  defaultOption.value = "";
  defaultOption.disabled = true;
  defaultOption.selected = true;
  defaultOption.textContent = subjects.length ? "Select a subject…" : "No subjects yet — click '+ New subject'";
  sessionSubject.appendChild(defaultOption);

  taskSubject.replaceChildren();
  const generalOption = document.createElement("option");
  generalOption.value = "";
  generalOption.textContent = "General / None";
  taskSubject.appendChild(generalOption);

  subjects.forEach((subj) => {
    const opt1 = document.createElement("option");
    opt1.value = subj.id;
    opt1.textContent = subj.name;
    sessionSubject.appendChild(opt1);

    const opt2 = document.createElement("option");
    opt2.value = subj.id;
    opt2.textContent = subj.name;
    taskSubject.appendChild(opt2);
  });

  if (currentSessionVal && subjects.some((s) => s.id == currentSessionVal)) {
    sessionSubject.value = currentSessionVal;
  }
  if (currentTaskVal && subjects.some((s) => s.id == currentTaskVal)) {
    taskSubject.value = currentTaskVal;
  }
}

function renderBreakdown(breakdown) {
  subjectBreakdown.replaceChildren();
  if (!breakdown || !breakdown.length) {
    const empty = document.createElement("p");
    empty.style.color = "var(--ink-soft)";
    empty.style.fontSize = "0.9rem";
    empty.textContent = "No focus sessions logged this week.";
    subjectBreakdown.appendChild(empty);
    return;
  }

  const maxMinutes = Math.max(...breakdown.map((b) => b.minutes), 1);

  breakdown.forEach((item) => {
    const matchedSubject = subjectsCache.find((s) => s.id === item.id) || {};
    const color = matchedSubject.color || "var(--orange)";

    const cat = document.createElement("div");
    cat.className = "category";

    const label = document.createElement("span");
    label.textContent = item.name;

    const meter = document.createElement("div");
    meter.className = "meter";

    const fill = document.createElement("i");
    const percent = Math.min(100, Math.round((item.minutes / maxMinutes) * 100));
    fill.style.width = `${percent}%`;
    fill.style.backgroundColor = color;
    meter.appendChild(fill);

    const count = document.createElement("span");
    count.textContent = formatMinutes(item.minutes);

    cat.append(label, meter, count);
    subjectBreakdown.appendChild(cat);
  });
}

function renderSessions(sessions) {
  sessionList.replaceChildren();
  if (!sessions || !sessions.length) {
    const empty = document.createElement("p");
    empty.style.color = "var(--ink-soft)";
    empty.style.fontSize = "0.9rem";
    empty.textContent = "No recent study sessions logged.";
    sessionList.appendChild(empty);
    return;
  }

  sessions.slice(0, 10).forEach((s) => {
    const item = document.createElement("article");
    item.className = "list-item";

    const matchedSubject = subjectsCache.find((sub) => sub.id === s.subject_id);
    const color = matchedSubject ? matchedSubject.color : "#d97757";

    const icon = document.createElement("div");
    icon.className = "list-icon";
    icon.style.backgroundColor = `${color}25`;
    icon.style.color = color;
    icon.textContent = "📖";

    const info = document.createElement("div");
    info.style.flex = "1";
    info.style.minWidth = "0";

    const title = document.createElement("strong");
    title.textContent = s.subject_name || "Study session";

    const note = document.createElement("small");
    note.textContent = `${s.session_date}${s.notes ? ` • ${s.notes}` : ""}`;

    info.append(title, note);

    const val = document.createElement("span");
    val.className = "list-value";
    val.textContent = formatMinutes(s.duration_minutes);

    const deleteBtn = document.createElement("button");
    deleteBtn.className = "delete-button";
    deleteBtn.innerHTML = "&times;";
    deleteBtn.title = "Delete session";
    deleteBtn.addEventListener("click", async () => {
      if (!confirm("Delete this study session?")) return;
      try {
        await request(`/api/study/sessions/${s.id}`, { method: "DELETE" });
        setStatus(sessionStatus, "Session deleted.");
        await loadData();
      } catch (err) {
        setStatus(sessionStatus, err.message, true);
      }
    });

    item.append(icon, info, val, deleteBtn);
    sessionList.appendChild(item);
  });
}

function renderTasks(tasks) {
  taskList.replaceChildren();
  const pendingCount = tasks.filter((t) => !t.completed).length;
  taskCountBadge.textContent = `${pendingCount} pending`;

  if (!tasks || !tasks.length) {
    const empty = document.createElement("p");
    empty.style.color = "var(--ink-soft)";
    empty.style.fontSize = "0.9rem";
    empty.textContent = "No tasks or exams logged yet.";
    taskList.appendChild(empty);
    return;
  }

  tasks.forEach((t) => {
    const item = document.createElement("article");
    item.className = "list-item";

    const checkBtn = document.createElement("button");
    checkBtn.type = "button";
    checkBtn.className = `check-button ${t.completed ? "completed" : ""}`;
    checkBtn.textContent = t.completed ? "✓" : "";
    checkBtn.title = t.completed ? "Mark incomplete" : "Mark completed";
    checkBtn.addEventListener("click", async () => {
      try {
        await request(`/api/study/tasks/${t.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ completed: !t.completed }),
        });
        await loadData();
      } catch (err) {
        setStatus(taskStatus, err.message, true);
      }
    });

    const info = document.createElement("div");
    info.style.flex = "1";
    info.style.minWidth = "0";

    const titleRow = document.createElement("div");
    titleRow.style.display = "flex";
    titleRow.style.alignItems = "center";
    titleRow.style.gap = "8px";
    titleRow.style.flexWrap = "wrap";

    const strong = document.createElement("strong");
    strong.textContent = t.title;
    if (t.completed) {
      strong.style.textDecoration = "line-through";
      strong.style.color = "var(--ink-soft)";
    }

    const typeBadge = document.createElement("span");
    typeBadge.className = `badge ${t.task_type === "exam" ? "badge-streak" : ""}`;
    typeBadge.textContent = t.task_type.toUpperCase();

    titleRow.append(strong, typeBadge);

    if (t.subject_name) {
      const subjBadge = document.createElement("span");
      subjBadge.className = "badge";
      subjBadge.textContent = t.subject_name;
      titleRow.appendChild(subjBadge);
    }

    const sub = document.createElement("small");
    sub.textContent = `Due ${t.due_date}${t.notes ? ` • ${t.notes}` : ""}`;

    info.append(titleRow, sub);

    const deleteBtn = document.createElement("button");
    deleteBtn.className = "delete-button";
    deleteBtn.innerHTML = "&times;";
    deleteBtn.title = "Delete task";
    deleteBtn.addEventListener("click", async () => {
      if (!confirm(`Delete task "${t.title}"?`)) return;
      try {
        await request(`/api/study/tasks/${t.id}`, { method: "DELETE" });
        await loadData();
      } catch (err) {
        setStatus(taskStatus, err.message, true);
      }
    });

    item.append(checkBtn, info, deleteBtn);
    taskList.appendChild(item);
  });
}

async function loadData() {
  try {
    const [dashboardData, subjects, sessions, tasks] = await Promise.all([
      request("/api/study/dashboard"),
      request("/api/study/subjects"),
      request("/api/study/sessions"),
      request("/api/study/tasks"),
    ]);

    statTodayMinutes.textContent = formatMinutes(dashboardData.today_minutes);
    statDailyGoal.textContent = formatMinutes(dashboardData.daily_goal_minutes);
    statGoalPercent.textContent = `${dashboardData.goal_percent}%`;
    goalInput.value = dashboardData.daily_goal_minutes;

    populateSubjectSelects(subjects);
    renderBreakdown(dashboardData.subject_breakdown);
    renderSessions(sessions);
    renderTasks(tasks);
  } catch (err) {
    setStatus(sessionStatus, err.message, true);
  }
}

// Session Form Submit
if (sessionForm) {
  sessionForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const subjectId = sessionSubject.value;
    const duration = parseInt(sessionDuration.value, 10);
    const date = sessionDate.value;
    const notes = sessionNotes.value.trim();

    if (!subjectId) {
      setStatus(sessionStatus, "Please select or add a subject first.", true);
      return;
    }

    setStatus(sessionStatus, "Logging session…");
    try {
      await request("/api/study/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subject_id: subjectId,
          duration_minutes: duration,
          date,
          notes,
        }),
      });
      sessionDuration.value = "";
      sessionNotes.value = "";
      setStatus(sessionStatus, "Focus session saved!");
      await loadData();
    } catch (err) {
      setStatus(sessionStatus, err.message, true);
    }
  });
}

// Add Subject Box Toggle & Save
if (toggleNewSubjectBtn) {
  toggleNewSubjectBtn.addEventListener("click", () => {
    newSubjectBox.style.display =
      newSubjectBox.style.display === "none" ? "block" : "none";
    if (newSubjectBox.style.display === "block") {
      newSubjectName.focus();
    }
  });
}

if (cancelSubjectBtn) {
  cancelSubjectBtn.addEventListener("click", () => {
    newSubjectBox.style.display = "none";
    newSubjectName.value = "";
  });
}

if (saveSubjectBtn) {
  saveSubjectBtn.addEventListener("click", async () => {
    const name = newSubjectName.value.trim();
    const color = newSubjectColor.value;
    if (!name) return;

    setStatus(sessionStatus, "Creating subject…");
    try {
      const created = await request("/api/study/subjects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, color }),
      });
      newSubjectBox.style.display = "none";
      newSubjectName.value = "";
      setStatus(sessionStatus, `Subject "${name}" added!`);
      await loadData();
      sessionSubject.value = created.id;
    } catch (err) {
      setStatus(sessionStatus, err.message, true);
    }
  });
}

// Goal Edit Toggle & Save
if (editGoalBtn) {
  editGoalBtn.addEventListener("click", () => {
    const isHidden = goalForm.style.display === "none";
    goalForm.style.display = isHidden ? "block" : "none";
    editGoalBtn.textContent = isHidden ? "Hide" : "Change";
    if (isHidden) goalInput.focus();
  });
}

if (goalForm) {
  goalForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const minutes = parseInt(goalInput.value, 10);
    if (!minutes || minutes <= 0) return;

    try {
      await request("/api/study/goal", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ daily_goal_minutes: minutes }),
      });
      goalForm.style.display = "none";
      editGoalBtn.textContent = "Change";
      setStatus(sessionStatus, `Daily goal updated to ${formatMinutes(minutes)}.`);
      await loadData();
    } catch (err) {
      setStatus(sessionStatus, err.message, true);
    }
  });
}

// Task Form Submit
if (taskForm) {
  taskForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = taskTitle.value.trim();
    const type = taskType.value;
    const subjectId = taskSubject.value ? parseInt(taskSubject.value, 10) : null;
    const dueDate = taskDueDate.value;

    if (!title || !dueDate) return;

    setStatus(taskStatus, "Adding deadline…");
    try {
      await request("/api/study/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          type,
          subject_id: subjectId,
          due_date: dueDate,
        }),
      });
      taskTitle.value = "";
      setStatus(taskStatus, `Deadline "${title}" added!`);
      await loadData();
    } catch (err) {
      setStatus(taskStatus, err.message, true);
    }
  });
}

loadData();
