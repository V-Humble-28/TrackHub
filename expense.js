const expenseForm = document.querySelector("#expense-form");
const expenseStatus = document.querySelector("#expense-status");
const categoryList = document.querySelector("#category-list");
const expenseList = document.querySelector("#expense-list");
const monthTotal = document.querySelector("#month-total");
const transactionCount = document.querySelector("#transaction-count");
const splitForm = document.querySelector("#split-form");
const splitStatus = document.querySelector("#split-status");
const settlementResult = document.querySelector("#settlement-result");
const settlementTotal = document.querySelector("#settlement-total");
const splitList = document.querySelector("#split-list");
const monthEyebrow = document.querySelector("#month-eyebrow");
const expenseDateInput = document.querySelector("#expense-date");

function localTodayDate() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function localCurrentMonth() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}`;
}

if (expenseDateInput) {
  expenseDateInput.value = localTodayDate();
}

if (monthEyebrow) {
  const currentMonthName = new Intl.DateTimeFormat("en-US", { month: "long" }).format(new Date());
  monthEyebrow.textContent = `${currentMonthName.toUpperCase()} SPENDING`;
}

function rupees(amount) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(amount);
}

function setStatus(target, message = "", isError = false) {
  target.textContent = message;
  target.classList.toggle("error", isError);
}

const API_BASE = window.location.protocol === "file:" ? "http://127.0.0.1:5001" : "";

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

function renderExpenses(data) {
  monthTotal.textContent = rupees(data.total);
  transactionCount.textContent = data.expenses.length;
  categoryList.replaceChildren();
  expenseList.replaceChildren();
  const largest = Math.max(...Object.values(data.category_totals), 1);

  Object.entries(data.category_totals).forEach(([category, total]) => {
    const row = document.createElement("div");
    row.className = "category";
    const label = document.createElement("span");
    const meter = document.createElement("div");
    const fill = document.createElement("i");
    const amount = document.createElement("span");
    label.textContent = category;
    fill.style.width = `${(total / largest) * 100}%`;
    amount.textContent = rupees(total);
    meter.className = "meter";
    meter.append(fill);
    row.append(label, meter, amount);
    categoryList.append(row);
  });

  if (!data.expenses.length) {
    const empty = document.createElement("p");
    empty.className = "status";
    empty.textContent = "No expenses this month yet.";
    expenseList.append(empty);
    return;
  }

  data.expenses.forEach((expense) => {
    const item = document.createElement("div");
    item.className = "list-item";
    const icon = document.createElement("span");
    const details = document.createElement("div");
    const title = document.createElement("strong");
    const meta = document.createElement("small");
    const value = document.createElement("span");
    const remove = document.createElement("button");
    icon.className = "list-icon";
    icon.textContent = "₹";
    title.textContent = expense.description;
    meta.textContent = `${expense.category} · paid by ${expense.paid_by}`;
    value.className = "list-value";
    value.textContent = rupees(expense.amount);
    remove.className = "delete-button";
    remove.type = "button";
    remove.textContent = "×";
    remove.setAttribute("aria-label", `Delete ${expense.description}`);
    remove.addEventListener("click", async () => {
      try {
        await request(`/api/expense/entries/${expense.id}`, { method: "DELETE" });
        setStatus(expenseStatus, "Expense removed.");
        loadExpenses();
      } catch (error) {
        setStatus(expenseStatus, error.message, true);
      }
    });
    details.append(title, meta);
    item.append(icon, details, value, remove);
    expenseList.append(item);
  });
}

async function loadExpenses() {
  const month = localCurrentMonth();
  try {
    renderExpenses(await request(`/api/expense/entries?month=${month}`));
  } catch (error) {
    setStatus(expenseStatus, error.message, true);
  }
}

expenseForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = expenseForm.querySelector("button");
  const description = document.querySelector("#description").value.trim();
  const amount = document.querySelector("#amount").value;
  const category = document.querySelector("#category").value.toLowerCase();
  const paidBy = document.querySelector("#paid-by").value.trim() || "You";
  const expenseDate = (expenseDateInput && expenseDateInput.value) || localTodayDate();

  if (!description) {
    setStatus(expenseStatus, "Please enter a description for the expense.", true);
    return;
  }

  button.disabled = true;
  try {
    const result = await request("/api/expense/entries", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        description,
        amount,
        category,
        paid_by: paidBy,
        date: expenseDate,
      }),
    });
    setStatus(expenseStatus, `Saved "${result.description}" (${rupees(result.amount)}).`);
    expenseForm.reset();
    if (expenseDateInput) expenseDateInput.value = localTodayDate();
    await loadExpenses();
  } catch (error) {
    setStatus(expenseStatus, error.message, true);
  } finally {
    button.disabled = false;
  }
});

function renderSplits(data) {
  settlementTotal.textContent = rupees(data.total_to_settle || 0);
  if (!splitList) return;
  splitList.replaceChildren();

  if (!data.bills || !data.bills.length) {
    const empty = document.createElement("p");
    empty.className = "status";
    empty.textContent = "No split bills saved yet.";
    splitList.append(empty);
    return;
  }

  data.bills.forEach((bill) => {
    const card = document.createElement("div");
    card.className = "split-card";

    const header = document.createElement("div");
    header.className = "split-card-header";

    const title = document.createElement("h3");
    title.textContent = `${bill.title} · ${rupees(bill.total)}`;

    const remove = document.createElement("button");
    remove.className = "delete-button";
    remove.type = "button";
    remove.setAttribute("aria-label", `Delete ${bill.title}`);
    remove.textContent = "×";
    remove.addEventListener("click", async () => {
      try {
        await request(`/api/expense/splits/${bill.id}`, { method: "DELETE" });
        setStatus(splitStatus, `Bill "${bill.title}" removed.`);
        loadSplits();
      } catch (error) {
        setStatus(splitStatus, error.message, true);
      }
    });

    header.append(title, remove);

    const desc = document.createElement("p");
    const settlementsText = bill.settlement.length
      ? bill.settlement.map((s) => `${s.person} owes ${s.to} ${rupees(s.owes)}`).join(" · ")
      : "Everyone is settled.";
    desc.textContent = `Paid by ${bill.paid_by} · ${settlementsText}`;

    card.append(header, desc);
    splitList.append(card);
  });
}

async function loadSplits() {
  try {
    const data = await request("/api/expense/splits");
    renderSplits(data);
  } catch (error) {
    setStatus(splitStatus, error.message, true);
  }
}

splitForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = splitForm.querySelector("button");
  const paidBy = document.querySelector("#split-paid-by").value.trim();
  let participants = document.querySelector("#participants").value
    .split(",")
    .map((person) => person.trim())
    .filter(Boolean);

  if (paidBy && !participants.some((p) => p.toLowerCase() === paidBy.toLowerCase())) {
    participants.unshift(paidBy);
  }

  button.disabled = true;
  try {
    const result = await request("/api/expense/splits", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: document.querySelector("#split-title").value.trim(),
        amount: document.querySelector("#split-amount").value,
        paid_by: paidBy,
        participants,
        mode: "equal",
      }),
    });
    setStatus(splitStatus, `Bill split "${result.title}" created.`);
    splitForm.reset();
    settlementResult.textContent = "";
    loadSplits();
  } catch (error) {
    setStatus(splitStatus, error.message, true);
  } finally {
    button.disabled = false;
  }
});

loadExpenses();
loadSplits();
