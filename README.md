# TrackHub 🚀

**TrackHub** is a clean, simple, and modular personal productivity web application built with Python (Flask), SQLite, HTML, CSS, and JavaScript. It brings four everyday tracking tools together into one unified dashboard with a modern glassmorphic interface.

TrackHub is designed not just as a handy productivity tool, but also as a practical implementation of real-world **DevOps principles**: clean Git branching, automated testing, continuous integration (CI) pipelines, pre-commit quality checks, and standardized commit messages.

---

## 📱 The 4 Modules

TrackHub is split into four independent, self-contained tracker modules:

### 1. 🥗 Calorie Tracker (`trackers/calorie/`)
- **Food Search**: Search through a built-in Indian food nutrition dataset (`foods.csv`).
- **Smart Calorie Calculator**: Automatically calculates calories based on portion weight in grams.
- **Meal Logs**: Save meals under Breakfast, Lunch, Dinner, or Snack.
- **Daily Target**: See total calories eaten today compared to a 2,000 kcal target.

### 2. 💰 Expense Tracker (`trackers/expense/`)
- **Expense Logging**: Record spending with descriptions, amounts, and dates.
- **Categories**: Automatically groups spending into Food, Transport, Grocery, College, Entertainment, Subscriptions, and Other.
- **Equal Bill Splitting**: Split group bills equally between friends and see exact "who owes whom" settlement summaries.

### 3. 🔥 Habit Tracker (`trackers/habit/`)
- **Flexible Routines**: Create habits for Every Day, Weekdays (Mon–Fri), or Weekly (Once a week).
- **One-Click Check-In**: Check off habits as you finish them for the day.
- **Streak Engine**: Tracks your current streak and longest streak, smartly skipping days you were not expected to do the habit.
- **7-Day Progress Bar**: Visual bar chart showing daily consistency over the last week.

### 4. 📖 Study Tracker (`trackers/study/`)
- **Focus Time Journal**: Log study sessions in minutes by subject with custom color tags.
- **Daily Goal Meter**: Set a daily study goal (e.g. 120 minutes) and watch your progress bar fill up.
- **Subject Breakdown**: See which subjects you spent the most time on over the past 7 days.
- **Task & Exam Deadlines**: Track upcoming assignments and tests with clear due dates and completion checkboxes.

---

## 🔄 How the DevOps Lifecycle is Implemented

TrackHub follows a complete, industry-standard DevOps lifecycle from writing code to testing and merging:

```text
 1. PLAN & CODE         2. PRE-COMMIT CHECK       3. AUTOMATED CI (CLOUD)      4. CODE REVIEW & MERGE
┌────────────────┐      ┌──────────────────┐      ┌──────────────────────┐     ┌─────────────────────┐
│ Feature Branch │ ───▶ │ Pre-Commit Hooks │ ───▶ │ GitHub Actions CI    │ ──▶ │ Pull Request (PR)   │
│ & Commit Msg   │      │ (Syntax, .db,    │      │ (Ruff Linting +      │     │ Review and Merge    │
│ Template       │      │  Pytest Gate)    │      │  Pytest Suite)       │     │ into 'main'         │
└────────────────┘      └──────────────────┘      └──────────────────────┘     └─────────────────────┘
```

### 1. Feature-Branch Workflow
- Nobody commits directly to the `main` branch.
- Every new feature, bug fix, or improvement is created in its own short-lived branch:
  - Features: `feature/<tracker-name>` (e.g., `feature/calorie-tracker`)
  - Fixes: `fix/<issue-name>` (e.g., `fix/ci-lint-and-test-workflows`)
  - Chores: `chore/<task-name>` (e.g., `chore/devops-standards`)

### 2. Standardized Commit Messages (`.gitmessage`)
To keep Git history clean, readable, and easy to audit, commits follow the **Conventional Commits** standard using a predefined template (`.gitmessage`):
- `feat(...)`: Adding a new feature or endpoint.
- `fix(...)`: Fixing a bug or broken test.
- `test(...)`: Adding or updating test cases.
- `ci(...)`: Updating workflow files or CI pipelines.
- `refactor(...)`: Restructuring code without changing behavior.
- `chore(...)`: Routine housekeeping or dependency updates.

### 3. Git Pre-Commit Hooks (`.githooks/` & `.pre-commit-config.yaml`)
Before a commit can even be created on your local computer, automated pre-commit checks run to protect the repository:
- **Blocks database leaks**: Automatically stops SQLite database files (`*.db`) from being accidentally committed.
- **Checks Python syntax**: Runs `py_compile` to catch syntax errors immediately.
- **Runs local tests**: Automatically runs `pytest` so you never commit broken code.

### 4. Continuous Integration (CI) with GitHub Actions (`.github/workflows/`)
Every time code is pushed or a Pull Request is opened, GitHub Actions automatically runs automated jobs in the cloud on an Ubuntu server:
- **Linting Pipeline (`lint.yml`)**: Uses **Ruff** to check Python code formatting, sort imports, and detect unused variables.
- **Testing Pipeline (`test.yml`)**: Sets up Python, installs dependencies, and runs the entire **Pytest** test suite to ensure all unit tests pass before anything can be merged into `main`.
- **Manual Trigger Support**: Both workflows support `workflow_dispatch`, meaning you can also trigger them manually with a click in the GitHub Actions tab.

### 5. Pull Requests & Zero-Downtime Merging
Changes are reviewed through GitHub Pull Requests. Once the CI pipeline confirms that all tests and lint checks have green checkmarks, the branch is safely merged into `main`.

---

## 🛠️ Architecture & Technologies

TrackHub uses a clean **API Gateway** pattern:

- **Unified API Gateway (`app.py`)**: A single Flask server running on port `5001`. It dynamically connects all four tracker apps, serves the frontend pages, handles CORS (cross-origin sharing), and protects against path traversal security risks.
- **Decoupled SQLite Databases**: Each tracker has its own SQLite database (`calorie.db`, `expenses.db`, `habit.db`, `study.db`). This means each tracker is completely independent and simultaneous writes never block each other.
- **Zero-Dependency Frontend**: The user interface is built with plain HTML5, CSS3 (modern glassmorphism), and vanilla JavaScript. There is no heavy framework (no Node.js or React build step needed), making the app fast and lightweight.

---

## 📂 Project Structure

```text
TrackHub/
├── index.html                       # Main dashboard landing page
├── tracker.css                      # Unified glassmorphic styling
├── title-animation.js               # Multilingual animated header
├── app.py                           # Unified Flask API gateway & asset server
├── requirements.txt                 # Project dependencies (Flask, pytest, ruff)
├── pytest.ini                       # Pytest configuration file
├── .gitignore                       # Ignored files (databases, virtualenv, caches)
├── .gitmessage                      # Standard commit message template
├── .pre-commit-config.yaml          # Pre-commit hook configuration
├── .githooks/                       # Local Git pre-commit script
│   └── pre-commit
├── .github/                         # Cloud CI pipelines
│   └── workflows/
│       ├── lint.yml                 # Ruff linting workflow
│       └── test.yml                 # Pytest automated testing workflow
├── tests/                           # Automated test suites
│   ├── test_calorie.py              # Calorie API & nutrition math tests
│   ├── test_expense.py              # Expense & bill splitting tests
│   ├── test_habit.py                # Habit streak & completion tests
│   ├── test_study.py                # Study focus & task tests
│   └── test_unified_app.py          # Gateway routing & asset tests
└── trackers/                        # Micro-service tracker directories
    ├── calorie/
    │   ├── app.py                   # Calorie backend API
    │   ├── calorie.html             # Calorie frontend page
    │   ├── calorie.js               # Calorie frontend logic
    │   └── data/foods.csv           # Indian food nutrition dataset
    ├── expense/
    │   ├── app.py                   # Expense backend API
    │   ├── expense.html             # Expense frontend page
    │   └── expense.js               # Expense frontend logic
    ├── habit/
    │   ├── app.py                   # Habit backend API
    │   ├── habit.html               # Habit frontend page
    │   └── habit.js                 # Habit frontend logic
    └── study/
        ├── app.py                   # Study backend API
        ├── study.html               # Study frontend page
        └── study.js                 # Study frontend logic
```

---

## 📦 Dependencies

All dependencies are listed in `requirements.txt`:
- **Flask**: Lightweight web framework used for the API Gateway and backend services.
- **pytest**: Automated testing framework used to test all APIs and route logic.
- **ruff**: Ultra-fast Python linter used to check code quality and formatting.
- **SQLite3**: Lightweight file-based relational database (built into Python standard library, zero setup needed).

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9 or newer installed.
- Git installed.

### 1. Clone the Repository
```bash
git clone https://github.com/V-Humble-28/TrackHub.git
cd TrackHub
```

### 2. Set Up Virtual Environment
```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Enable Local Git Pre-Commit Hooks (Optional but Recommended)
```bash
git config core.hooksPath .githooks
```

### 5. Run the Application
```bash
python app.py
```
Open your browser and navigate to:
👉 **`http://127.0.0.1:5001`**

---

## 🧪 Running Automated Tests

To run the automated test suite locally:

```bash
pytest
```

To run tests with detailed output:
```bash
pytest -v
```

All tests execute in less than a second, verifying that all backend APIs, calculations, and gateway routes are working properly.
