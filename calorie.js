const mealForm = document.querySelector("#meal-form");
const foodInput = document.querySelector("#food");
const foodResults = document.querySelector("#food-results");
const mealLog = document.querySelector("#meal-log");
const mealStatus = document.querySelector("#meal-status");
const consumed = document.querySelector("#consumed");
const remaining = document.querySelector("#remaining");
const logDate = document.querySelector("#log-date");
const selectedDateInput = document.querySelector("#selected-date");

let selectedFood = null;
let searchTimer;

function setStatus(message = "", isError = false) {
  mealStatus.textContent = message;
  mealStatus.classList.toggle("error", isError);
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
      "Cannot connect to server. Please ensure the app server is running at http://localhost:5001."
    );
  }
  let data;
  try {
    data = await response.json();
  } catch (err) {
    throw new Error(`Server returned status ${response.status}`);
  }
  if (!response.ok) throw new Error((data && data.error) || "Something went wrong.");
  return data;
}

function renderFoodResults(foods) {
  foodResults.replaceChildren();
  foods.forEach((food) => {
    const option = document.createElement("button");
    option.type = "button";
    option.className = "food-option";
    const name = document.createElement("span");
    const detail = document.createElement("small");
    name.textContent = food.name;
    detail.textContent = `${food.calories_per_100g} kcal / 100g`;
    option.append(name, detail);
    option.addEventListener("click", () => {
      selectedFood = food;
      foodInput.value = food.name;
      foodResults.replaceChildren();
      setStatus(`${food.name} selected.`);
    });
    foodResults.append(option);
  });
}

async function searchFoods() {
  const query = foodInput.value.trim();
  selectedFood = null;
  if (query.length < 2) {
    foodResults.replaceChildren();
    return;
  }

  try {
    const data = await request(`/api/calorie/foods?q=${encodeURIComponent(query)}&limit=6`);
    renderFoodResults(data.foods);
  } catch (error) {
    setStatus(error.message, true);
  }
}

function mealIcon(meal) {
  return { breakfast: "☀", lunch: "◒", dinner: "☾", snack: "✦" }[meal] || "•";
}

function renderEntries(data) {
  const total = Math.round(data.total_calories);
  consumed.textContent = `${total.toLocaleString()} kcal`;
  remaining.textContent = `${Math.max(0, 2000 - total).toLocaleString()} kcal`;
  logDate.textContent = new Intl.DateTimeFormat("en-IN", { dateStyle: "full" }).format(new Date(`${data.date}T00:00:00`));
  mealLog.replaceChildren();

  if (!data.entries.length) {
    const empty = document.createElement("p");
    empty.className = "status";
    empty.textContent = "No meals logged yet. Add your first meal above.";
    mealLog.append(empty);
    return;
  }

  data.entries.forEach((entry) => {
    const item = document.createElement("div");
    item.className = "list-item";
    const icon = document.createElement("span");
    icon.className = "list-icon";
    icon.textContent = mealIcon(entry.meal);
    const details = document.createElement("div");
    const name = document.createElement("strong");
    const meta = document.createElement("small");
    name.textContent = entry.food_name;
    meta.textContent = `${entry.meal} · ${entry.weight} g`;
    details.append(name, meta);
    const value = document.createElement("span");
    value.className = "list-value";
    value.textContent = `${Math.round(entry.calories)} kcal`;
    const remove = document.createElement("button");
    remove.className = "delete-button";
    remove.type = "button";
    remove.setAttribute("aria-label", `Delete ${entry.food_name}`);
    remove.textContent = "×";
    remove.addEventListener("click", async () => {
      try {
        await request(`/api/calorie/entries/${entry.id}`, { method: "DELETE" });
        setStatus("Meal removed.");
        loadEntries(currentDate());
      } catch (error) {
        setStatus(error.message, true);
      }
    });
    item.append(icon, details, value, remove);
    mealLog.append(item);
  });
}

function currentDate() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  const localIso = `${year}-${month}-${day}`;
  return (selectedDateInput && selectedDateInput.value) || localIso;
}

async function loadEntries(dateValue) {
  const dateParam = dateValue || currentDate();
  try {
    const data = await request(`/api/calorie/entries?date=${encodeURIComponent(dateParam)}`);
    renderEntries(data);
  } catch (error) {
    logDate.textContent = error.message.includes("Cannot connect")
      ? "Cannot connect to server. Ensure it is running at http://localhost:5001"
      : "Could not load meals for selected date.";
  }
}

foodInput.addEventListener("input", () => {
  window.clearTimeout(searchTimer);
  searchTimer = window.setTimeout(searchFoods, 250);
});

if (selectedDateInput) {
  selectedDateInput.value = currentDate();
  selectedDateInput.addEventListener("change", () => {
    loadEntries(selectedDateInput.value);
  });
}

mealForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!selectedFood) {
    const query = foodInput.value.trim();
    if (query) {
      try {
        const data = await request(`/api/calorie/foods?q=${encodeURIComponent(query)}&limit=1`);
        if (data.foods && data.foods.length > 0) {
          selectedFood = data.foods[0];
          foodInput.value = selectedFood.name;
        } else {
          setStatus(`No food matching "${query}" found. Try another search term.`, true);
          return;
        }
      } catch (err) {
        setStatus("Could not search food dataset.", true);
        return;
      }
    } else {
      setStatus("Please search and select a food first.", true);
      return;
    }
  }

  const button = mealForm.querySelector("button");
  button.disabled = true;
  try {
    const activeDate = currentDate();
    const result = await request("/api/calorie/entries", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        food_id: selectedFood.id,
        weight: document.querySelector("#weight").value,
        meal: document.querySelector("#meal").value.toLowerCase(),
        date: activeDate,
      }),
    });
    setStatus(`${result.food_name} added to log.`);
    mealForm.reset();
    selectedFood = null;
    foodResults.replaceChildren();
    if (selectedDateInput) selectedDateInput.value = activeDate;
    await loadEntries(activeDate);
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    button.disabled = false;
  }
});

loadEntries();
