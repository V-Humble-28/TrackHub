const habitForm = document.querySelector("#habit-form");
const habitStatus = document.querySelector("#habit-status");
const habitList = document.querySelector("#habit-list");
const statCompleted = document.querySelector("#stat-completed");
const statPercent = document.querySelector("#stat-percent");
const statStreak = document.querySelector("#stat-streak");
const weeklyChart = document.querySelector("#weekly-chart");
const todayDateBadge = document.querySelector("#today-date-badge");

function localTodayDate() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

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

function formatDayLabel(isoDateStr) {
  const parts = isoDateStr.split("-");
  const d = new Date(parts[0], parts[1] - 1, parts[2]);
  return d.toLocaleDateString("en-US", { weekday: "short" });
}

function renderWeeklyChart(weekly) {
  if (!weeklyChart) return;
  weeklyChart.replaceChildren();
  if (!weekly || !weekly.length) return;

  const maxVal = Math.max(...weekly.map((w) => w.completed), 1);

  weekly.forEach((dayItem) => {
    const col = document.createElement("div");
    col.className = "weekly-col";

    const bar = document.createElement("div");
    bar.className = "weekly-bar";
    const heightPercent = Math.max(8, Math.round((dayItem.completed / maxVal) * 100));
    bar.style.height = `${heightPercent}%`;
    bar.title = `${dayItem.date}: ${dayItem.completed} completed`;

    const label = document.createElement("span");
    label.className = "weekly-label";
    label.textContent = formatDayLabel(dayItem.date);

    col.append(bar, label);
    weeklyChart.appendChild(col);
  });
}

function renderHabits(habits, dashboardData) {
  if (dashboardData) {
    statCompleted.textContent = `${dashboardData.completed_today} / ${dashboardData.expected_today}`;
    statPercent.textContent = `${dashboardData.today_percent}%`;
  }

  const bestStreak = habits.length
    ? Math.max(...habits.map((h) => h.longest_streak || 0))
    : 0;
  statStreak.textContent = `${bestStreak} ${bestStreak === 1 ? "day" : "days"}`;

  habitList.replaceChildren();

  if (!habits.length) {
    const empty = document.createElement("p");
    empty.style.color = "var(--ink-soft)";
    empty.style.fontSize = "0.92rem";
    empty.style.padding = "16px 0";
    empty.textContent = "No habits created yet. Add your first habit on the left!";
    habitList.appendChild(empty);
    return;
  }

  habits.forEach((habit) => {
    const item = document.createElement("article");
    item.className = "list-item";

    const checkBtn = document.createElement("button");
    checkBtn.type = "button";
    checkBtn.className = `check-button ${habit.completed_today ? "completed" : ""}`;
    checkBtn.textContent = habit.completed_today ? "✓" : "";
    checkBtn.title = habit.completed_today ? "Mark undone" : "Mark completed for today";
    checkBtn.setAttribute("aria-label", `Mark ${habit.name} complete`);
    checkBtn.addEventListener("click", () => toggleHabit(habit.id, habit.completed_today));

    const content = document.createElement("div");
    content.style.flex = "1";
    content.style.minWidth = "0";

    const titleRow = document.createElement("div");
    titleRow.style.display = "flex";
    titleRow.style.alignItems = "center";
    titleRow.style.gap = "8px";
    titleRow.style.flexWrap = "wrap";

    const strong = document.createElement("strong");
    strong.textContent = habit.name;

    const freqBadge = document.createElement("span");
    freqBadge.className = "badge";
    freqBadge.textContent = habit.frequency;

    titleRow.append(strong, freqBadge);

    const desc = document.createElement("small");
    desc.textContent = habit.description || "Daily consistency goal";

    const statsRow = document.createElement("div");
    statsRow.style.display = "flex";
    statsRow.style.gap = "6px";
    statsRow.style.marginTop = "6px";
    statsRow.style.flexWrap = "wrap";

    const streakBadge = document.createElement("span");
    streakBadge.className = "badge badge-streak";
    streakBadge.textContent = `🔥 ${habit.current_streak}d streak (best: ${habit.longest_streak}d)`;

    const weekBadge = document.createElement("span");
    weekBadge.className = "badge";
    weekBadge.textContent = `${habit.weekly_completed}/${habit.weekly_expected} this week (${habit.weekly_percent}%)`;

    statsRow.append(streakBadge, weekBadge);
    content.append(titleRow, desc, statsRow);

    const deleteBtn = document.createElement("button");
    deleteBtn.type = "button";
    deleteBtn.className = "delete-button";
    deleteBtn.innerHTML = "&times;";
    deleteBtn.title = "Delete habit";
    deleteBtn.setAttribute("aria-label", `Delete habit ${habit.name}`);
    deleteBtn.addEventListener("click", () => deleteHabit(habit.id, habit.name));

    item.append(checkBtn, content, deleteBtn);
    habitList.appendChild(item);
  });
}

async function loadData() {
  try {
    const [dashboardData, habits] = await Promise.all([
      request("/api/habit/dashboard"),
      request("/api/habit/habits"),
    ]);

    renderWeeklyChart(dashboardData.weekly_completions);
    renderHabits(habits, dashboardData);
  } catch (err) {
    setStatus(habitStatus, err.message, true);
  }
}

async function toggleHabit(habitId, isDone) {
  const today = localTodayDate();
  try {
    if (isDone) {
      await request(`/api/habit/habits/${habitId}/complete?date=${today}`, {
        method: "DELETE",
      });
      setStatus(habitStatus, "Habit completion undone.");
    } else {
      await request(`/api/habit/habits/${habitId}/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ date: today }),
      });
      setStatus(habitStatus, "Habit checked off! Great job!");
    }
    await loadData();
  } catch (err) {
    setStatus(habitStatus, err.message, true);
  }
}

async function deleteHabit(habitId, habitName) {
  if (!confirm(`Are you sure you want to delete "${habitName}"?`)) return;
  try {
    await request(`/api/habit/habits/${habitId}`, { method: "DELETE" });
    setStatus(habitStatus, `Deleted "${habitName}".`);
    await loadData();
  } catch (err) {
    setStatus(habitStatus, err.message, true);
  }
}

if (habitForm) {
  habitForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.querySelector("#habit-name").value.trim();
    const description = document.querySelector("#habit-desc").value.trim();
    const frequency = document.querySelector("#habit-frequency").value;

    if (!name) return;
    setStatus(habitStatus, "Saving habit…");

    try {
      await request("/api/habit/habits", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, description, frequency }),
      });
      habitForm.reset();
      setStatus(habitStatus, `Habit "${name}" created!`);
      await loadData();
    } catch (err) {
      setStatus(habitStatus, err.message, true);
    }
  });
}

if (todayDateBadge) {
  const now = new Date();
  todayDateBadge.textContent = now.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

loadData();
