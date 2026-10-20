# TrackHub Engineering & DevOps Contribution Guidelines

To maintain code quality, reliable releases, and an audit-ready Git history, all contributors must adhere to these branching and commit standards.

---

## 🌿 1. Branch Naming Taxonomy

All work must occur on dedicated, short-lived branches created from `main`. Direct pushes to `main` are strictly prohibited.

| Branch Type | Format | Example | Description |
| :--- | :--- | :--- | :--- |
| **Feature** | `feature/<tracker-or-component>` | `feature/expense-tracker` | A complete functional module or capability |
| **Bug Fix** | `fix/<tracker-or-bug>` | `fix/expense-date-parsing` | Bug fix or patch |
| **CI / DevOps** | `ci/<tool-or-task>` | `ci/github-actions-tests` | Workflows, Docker, pipelines |
| **Refactoring** | `refactor/<scope>` | `refactor/modular-api-gateway` | Code changes without external behavior changes |
| **Documentation** | `docs/<description>` | `docs/contributing-guidelines` | README, API docs, architecture specs |
| **Chore** | `chore/<task>` | `chore/update-dependencies` | Dependency updates, repo housekeeping |

```bash
# Example: creating a standardized branch
git switch -c feature/expense-tracker
```

---

## 🧩 2. Atomic Commit Cadence (4-Step Rule)

Avoid large monolithic commits ("mega-commits"). Every tracker module must be developed and committed in 4 discrete, logical increments:

```text
Step 1: Data & Models   ──> feat(<module>): add database schema and SQLite tables
Step 2: API & Logic     ──> feat(<module>): implement business logic and API endpoints
Step 3: Test Suite      ──> test(<module>): add unit and edge-case tests
Step 4: UI & Interface  ──> feat(ui): connect frontend interface, styling, and assets
```

### Commit Message Structure
We follow the **Conventional Commits** specification:

```text
<type>(<scope>): <short imperative description>

[optional body explaining rationale and context]
```

* Allowed types: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`, `ci`.
* Scope: tracker name (e.g., `calorie`, `expense`, `habit`, `study`, `ui`, `gateway`).
* Summary line: Max 72 characters, lowercase imperative (e.g. `add persistent split bill endpoints`).

---

## 🔁 3. Pull Request (PR) Workflow

1. Ensure the test suite passes locally before creating a PR:
   ```bash
   .venv/bin/pytest
   ```
2. Push your feature branch:
   ```bash
   git push -u origin feature/<branch-name>
   ```
3. Open a Pull Request on GitHub targeting `main`.
4. Verify all automated checks pass.
5. Merge using standard merge or squash commit as determined by team policy.
6. Delete the remote feature branch after merging to keep the repository clean.
