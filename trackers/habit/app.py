
from flask import Flask, request, jsonify
from pathlib import Path
from datetime import date, timedelta
import sqlite3

app = Flask(__name__)
DB = Path(__file__).resolve().parent / "habit.db"


def connect():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT '',
            frequency TEXT NOT NULL DEFAULT 'daily'
                CHECK(frequency IN ('daily', 'weekdays', 'weekly')),
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            completed_date TEXT NOT NULL,
            FOREIGN KEY(habit_id) REFERENCES habits(id)
                ON DELETE CASCADE,
            UNIQUE(habit_id, completed_date)
        );
        """)


def parse_date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def completion_dates(con, habit_id):
    rows = con.execute(
        "SELECT completed_date FROM completions WHERE habit_id = ?",
        (habit_id,)
    ).fetchall()
    return {date.fromisoformat(row["completed_date"]) for row in rows}


def is_expected_day(day, frequency):
    if frequency == "weekdays":
        return day.weekday() < 5
    if frequency == "weekly":
        return day.weekday() == 0
    return True


def calculate_streaks(done_dates, frequency, today):
    # Current streak counts backward from today, or yesterday
    # if today's habit has not been completed yet.
    cursor = today
    if today not in done_dates:
        cursor = today - timedelta(days=1)

    current = 0
    while cursor >= min(done_dates, default=cursor):
        if is_expected_day(cursor, frequency):
            if cursor in done_dates:
                current += 1
            else:
                break
        cursor -= timedelta(days=1)

    longest = 0
    streak = 0
    if done_dates:
        start = min(done_dates)
        end = max(done_dates)
        cursor = start
        while cursor <= end:
            if is_expected_day(cursor, frequency):
                if cursor in done_dates:
                    streak += 1
                    longest = max(longest, streak)
                else:
                    streak = 0
            cursor += timedelta(days=1)

    return current, longest


def habit_stats(con, habit, today):
    done = completion_dates(con, habit["id"])
    current, longest = calculate_streaks(done, habit["frequency"], today)

    week_start = today - timedelta(days=6)
    week_days = [
        week_start + timedelta(days=i) for i in range(7)
    ]
    expected = [
        day for day in week_days
        if is_expected_day(day, habit["frequency"])
    ]
    weekly_done = sum(day in done for day in expected)

    return {
        "current_streak": current,
        "longest_streak": longest,
        "completed_today": today in done,
        "weekly_completed": weekly_done,
        "weekly_expected": len(expected),
        "weekly_percent": round(weekly_done / len(expected) * 100)
            if expected else 0
    }


@app.get("/api/habit/health")
def health():
    return jsonify({"status": "ok", "app": "Habit Tracker"})


@app.get("/api/habit/habits")
def list_habits():
    today = date.today()
    with connect() as con:
        habits = con.execute(
            "SELECT * FROM habits ORDER BY id"
        ).fetchall()
        result = []
        for habit in habits:
            item = dict(habit)
            item.update(habit_stats(con, habit, today))
            result.append(item)
    return jsonify(result)


@app.post("/api/habit/habits")
def create_habit():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    description = str(data.get("description", "")).strip()
    frequency = data.get("frequency", "daily")

    if not name:
        return jsonify({"error": "Habit name is required"}), 400
    if frequency not in {"daily", "weekdays", "weekly"}:
        return jsonify({
            "error": "frequency must be daily, weekdays, or weekly"
        }), 400

    try:
        with connect() as con:
            cur = con.execute("""
                INSERT INTO habits (name, description, frequency, created_at)
                VALUES (?, ?, ?, ?)
            """, (name, description, frequency, date.today().isoformat()))
            habit_id = cur.lastrowid
    except sqlite3.IntegrityError:
        return jsonify({"error": "A habit with this name already exists"}), 409

    return jsonify({
        "id": habit_id,
        "name": name,
        "description": description,
        "frequency": frequency,
        "created_at": date.today().isoformat()
    }), 201


@app.patch("/api/habit/habits/<int:habit_id>")
def update_habit(habit_id):
    data = request.get_json(silent=True) or {}
    allowed = {"name", "description", "frequency"}

    if not data or not set(data).issubset(allowed):
        return jsonify({
            "error": "Provide name, description, or frequency"
        }), 400

    updates = {}
    for key, value in data.items():
        if key == "name":
            value = str(value).strip()
            if not value:
                return jsonify({"error": "Name cannot be empty"}), 400
        if key == "description":
            value = str(value).strip()
        if key == "frequency" and value not in {
            "daily", "weekdays", "weekly"
        }:
            return jsonify({"error": "Invalid frequency"}), 400
        updates[key] = value

    columns = {"name": "name", "description": "description",
               "frequency": "frequency"}
    assignments = ", ".join(f"{columns[k]} = ?" for k in updates)

    try:
        with connect() as con:
            cur = con.execute(
                f"UPDATE habits SET {assignments} WHERE id = ?",
                (*updates.values(), habit_id)
            )
    except sqlite3.IntegrityError:
        return jsonify({"error": "A habit with this name already exists"}), 409

    if cur.rowcount == 0:
        return jsonify({"error": "Habit not found"}), 404
    return jsonify({"message": "Habit updated", "id": habit_id})


@app.delete("/api/habit/habits/<int:habit_id>")
def delete_habit(habit_id):
    with connect() as con:
        con.execute("PRAGMA foreign_keys = ON")
        cur = con.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
    if cur.rowcount == 0:
        return jsonify({"error": "Habit not found"}), 404
    return jsonify({"message": "Habit deleted"})


@app.post("/api/habit/habits/<int:habit_id>/complete")
def complete_habit(habit_id):
    data = request.get_json(silent=True) or {}
    completed_date = data.get("date") or date.today().isoformat()

    if not parse_date(completed_date):
        return jsonify({"error": "Date must be YYYY-MM-DD"}), 400

    with connect() as con:
        habit = con.execute(
            "SELECT id FROM habits WHERE id = ?", (habit_id,)
        ).fetchone()
        if not habit:
            return jsonify({"error": "Habit not found"}), 404
        try:
            con.execute("""
                INSERT INTO completions (habit_id, completed_date)
                VALUES (?, ?)
            """, (habit_id, completed_date))
        except sqlite3.IntegrityError:
            return jsonify({
                "message": "Habit already completed for this date",
                "habit_id": habit_id,
                "date": completed_date
            }), 200

    return jsonify({
        "message": "Habit marked complete",
        "habit_id": habit_id,
        "date": completed_date
    }), 201


@app.delete("/api/habit/habits/<int:habit_id>/complete")
def undo_completion(habit_id):
    completed_date = request.args.get("date") or date.today().isoformat()
    if not parse_date(completed_date):
        return jsonify({"error": "Date must be YYYY-MM-DD"}), 400

    with connect() as con:
        cur = con.execute("""
            DELETE FROM completions
            WHERE habit_id = ? AND completed_date = ?
        """, (habit_id, completed_date))

    if cur.rowcount == 0:
        return jsonify({"error": "Completion not found"}), 404
    return jsonify({"message": "Completion removed", "date": completed_date})


@app.get("/api/habit/dashboard")
def dashboard():
    today = date.today()
    week_start = today - timedelta(days=6)

    with connect() as con:
        habits = con.execute(
            "SELECT * FROM habits ORDER BY id"
        ).fetchall()

        weekly = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            total = con.execute("""
                SELECT COUNT(*) FROM completions
                WHERE completed_date = ?
            """, (day.isoformat(),)).fetchone()[0]
            weekly.append({
                "date": day.isoformat(),
                "completed": total
            })

        today_done = con.execute("""
            SELECT COUNT(*) FROM completions WHERE completed_date = ?
        """, (today.isoformat(),)).fetchone()[0]

        stats = [
            {"id": habit["id"], "name": habit["name"],
             **habit_stats(con, habit, today)}
            for habit in habits
        ]

    expected_today = sum(
        is_expected_day(today, habit["frequency"]) for habit in habits
    )
    completed_today = sum(
        item["completed_today"] and is_expected_day(
            today, next(h["frequency"] for h in habits if h["id"] == item["id"])
        )
        for item in stats
    )

    return jsonify({
        "date": today.isoformat(),
        "total_habits": len(habits),
        "completed_today": completed_today,
        "expected_today": expected_today,
        "today_percent": round(completed_today / expected_today * 100)
            if expected_today else 0,
        "weekly_completions": weekly,
        "habits": stats
    })


init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5003)
