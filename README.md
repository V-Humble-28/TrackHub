
# Tracker Hub 🚀

**Tracker Hub** is a Python-based project that brings multiple personal tracking tools together in one place. It is being developed module by module as part of a DevOps viva project.

The goal is to build a collection of simple, useful trackers while learning Python programming, Git, GitHub, branching, testing, and CI/CD.

## 📌 Project Overview

Tracker Hub will contain 10 different tracker modules. Each module will have its own features and will be developed incrementally.

### Current Modules

**1. Calorie Tracker**
- Add food items and their calorie values.
- View recorded food entries.
- Calculate total daily calorie intake.
- Save and retrieve food records.

**2. Expense Tracker**
- Record income and expenses.
- Organize transactions into categories.
- Calculate total expenses and remaining balance.
- Save and retrieve transaction records.

### Planned Modules

The remaining modules will be selected and implemented as the project develops.

## 🛠️ Technologies Used

- **Python** — application development.
- **Git** — version control.
- **GitHub** — remote repository and collaboration workflow.
- **JSON** — initial data storage.
- **pytest** — automated testing.
- **GitHub Actions** — continuous integration and automated test execution.

## 📂 Project Structure

```text
tracker-hub/
├── trackers/
│   ├── __init__.py
│   ├── calorie/
│   │   └── __init__.py
│   └── expense/
│       └── __init__.py
├── tests/
├── .gitignore
└── README.md
```

The structure will expand as features, tests, and additional trackers are implemented.

## 🚀 Getting Started

### Prerequisites

- Python 3 installed.
- Git installed.
- A GitHub account.

### Clone the Repository

```bash
git clone <your-github-repository-url>
cd tracker-hub
```

Replace `<your-github-repository-url>` with your actual GitHub repository URL.

### Run the Project

The application and its run instructions will be added as the tracker modules become functional.

## 🌿 Git Workflow & DevOps Standards

The project follows a strict **Feature-Branch Workflow** and **Atomic Commit Cadence** (see [CONTRIBUTING.md](CONTRIBUTING.md) for full engineering guidelines):

### 1. Branch Naming Taxonomy
* **Features**: `feature/<tracker-name>` (e.g. `feature/expense-tracker`)
* **Bug Fixes**: `fix/<tracker-or-bug>` (e.g. `fix/split-rounding`)
* **DevOps / CI**: `ci/<task>` (e.g. `ci/github-actions-tests`)
* **Documentation**: `docs/<description>`

### 2. Atomic Commit Cadence (4-Step Rule)
Each module is committed in small, reviewable increments following Conventional Commits:
1. `feat(<module>): add database schema and SQLite models`
2. `feat(<module>): implement core business logic and API endpoints`
3. `test(<module>): add automated unit and edge-case tests`
4. `feat(ui): connect frontend interface and styles`

Example:

```bash
git switch -c feature/expense-tracker
# Step 1: Implement schema & endpoints
git add trackers/expense/app.py
git commit -m "feat(expense): add persistent split bill and default payer endpoints"

# Step 2: Add test suite
git add tests/test_expense.py
git commit -m "test(expense): add automated test suite for expenses and bill splits"

# Step 3: Implement UI integration
git add expense.html expense.js tracker.css
git commit -m "feat(ui): add persistent expense tracking and bill splitting interface"
```

## 🧪 Testing

Automated tests will be added to verify that tracker features work correctly. GitHub Actions will later be configured to run the tests automatically when changes are pushed.

## 🎯 Project Objectives

- Build 10 useful tracker modules using Python.
- Practise writing readable and maintainable code.
- Learn Git branching, commits, pushing, and merging.
- Maintain a meaningful commit history with at least 15 commits.
- Learn automated testing and CI/CD fundamentals.
- Demonstrate practical DevOps concepts during the viva.

## 📚 Learning Outcomes

This project provides practical experience with Python fundamentals, file handling, modular programming, version control, testing, and continuous integration.

## 👨‍💻 Project Status

**In Development** — The project is being built incrementally, starting with the Calorie Tracker and Expense Tracker.

---


