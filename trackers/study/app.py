
from flask import Flask, request, jsonify
from pathlib import Path
from datetime import date, datetime, timedelta
import sqlite3

app = Flask(__name__)
DB = Path(__file__).resolve().parent / "study.db"


def connect():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db():
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            color TEXT NOT NULL DEFAULT '#64748b'
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            duration_minutes INTEGER NOT NULL CHECK(duration_minutes > 0),
            notes TEXT DEFAULT '',
            session_date TEXT NOT NULL,
            FOREIGN KEY(subject_id) REFERENCES subjects(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK(id = 1),
            daily_goal_minutes INTEGER NOT NULL DEFAULT 120
        );

        INSERT OR IGNORE INTO settings (id, daily_goal_minutes)
        VALUES (1, 120);

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            task_type TEXT NOT NULL CHECK(task_type IN ('assignment', 'exam')),
            subject_id INTEGER,
            due_date TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            notes TEXT DEFAULT '',
            FOREIGN KEY(subject_id) REFERENCES subjects(id)
                ON DELETE SET NULL
        );
        """)


def valid_date(value):
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None


@app.get("/api/study/health")
def health():
    return jsonify({"status": "ok", "app": "Study Tracker"})


# SUBJECTS

@app.get("/api/study/subjects")
def list_subjects():
    with connect() as con:
        rows = con.execute("""
            SELECT s.*,
            COALESCE(SUM(st.duration_minutes), 0) AS total_minutes
            FROM subjects s
            LEFT JOIN sessions st ON st.subject_id = s.id
            GROUP BY s.id
            ORDER BY s.name
        """).fetchall()
    return jsonify([dict(row) for row in rows])


@app.post("/api/study/subjects")
def add_subject():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    color = str(data.get("color", "#64748b")).strip()

    if not name:
        return jsonify({"error": "Subject name is required"}), 400

    try:
        with connect() as con:
            cur = con.execute(
                "INSERT INTO subjects (name, color) VALUES (?, ?)",
                (name, color)
            )
            subject_id = cur.lastrowid
    except sqlite3.IntegrityError:
        return jsonify({"error": "This subject already exists"}), 409

    return jsonify({
        "id": subject_id, "name": name, "color": color
    }), 201


@app.delete("/api/study/subjects/<int:subject_id>")
def delete_subject(subject_id):
    with connect() as con:
        cur = con.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
    if cur.rowcount == 0:
        return jsonify({"error": "Subject not found"}), 404
    return jsonify({"message": "Subject deleted"})


# STUDY SESSIONS

@app.get("/api/study/sessions")
def list_sessions():
    day = request.args.get("date")
    start = request.args.get("start")
    end = request.args.get("end")

    with connect() as con:
        if day:
            if not valid_date(day):
                return jsonify({"error": "Use date YYYY-MM-DD"}), 400
            rows = con.execute("""
                SELECT st.*, s.name AS subject_name
                FROM sessions st JOIN subjects s ON s.id = st.subject_id
                WHERE st.session_date = ?
                ORDER BY st.id DESC
            """, (day,)).fetchall()
        elif start or end:
            if not valid_date(start) or not valid_date(end) or start > end:
                return jsonify({"error": "Provide valid start and end dates"}), 400
            rows = con.execute("""
                SELECT st.*, s.name AS subject_name
                FROM sessions st JOIN subjects s ON s.id = st.subject_id
                WHERE st.session_date BETWEEN ? AND ?
                ORDER BY st.session_date DESC, st.id DESC
            """, (start, end)).fetchall()
        else:
            rows = con.execute("""
                SELECT st.*, s.name AS subject_name
                FROM sessions st JOIN subjects s ON s.id = st.subject_id
                ORDER BY st.session_date DESC, st.id DESC
            """).fetchall()

    return jsonify([dict(row) for row in rows])


@app.post("/api/study/sessions")
def add_session():
    data = request.get_json(silent=True) or {}

    try:
        subject_id = int(data.get("subject_id"))
        minutes = int(data.get("duration_minutes"))
    except (TypeError, ValueError):
        return jsonify({
            "error": "subject_id and duration_minutes must be integers"
        }), 400

    session_date = data.get("date") or date.today().isoformat()
    notes = str(data.get("notes", "")).strip()

    if minutes <= 0 or minutes > 1440:
        return jsonify({"error": "Duration must be 1–1440 minutes"}), 400
    if not valid_date(session_date):
        return jsonify({"error": "Date must be YYYY-MM-DD"}), 400

    with connect() as con:
        subject = con.execute(
            "SELECT id FROM subjects WHERE id = ?", (subject_id,)
        ).fetchone()
        if not subject:
            return jsonify({"error": "Subject not found"}), 404

        cur = con.execute("""
            INSERT INTO sessions
            (subject_id, duration_minutes, notes, session_date)
            VALUES (?, ?, ?, ?)
        """, (subject_id, minutes, notes, session_date))
        session_id = cur.lastrowid

    return jsonify({
        "id": session_id,
        "subject_id": subject_id,
        "duration_minutes": minutes,
        "date": session_date,
        "notes": notes
    }), 201


@app.delete("/api/study/sessions/<int:session_id>")
def delete_session(session_id):
    with connect() as con:
        cur = con.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    if cur.rowcount == 0:
        return jsonify({"error": "Session not found"}), 404
    return jsonify({"message": "Session deleted"})


# DAILY GOAL

@app.get("/api/study/goal")
def get_goal():
    with connect() as con:
        row = con.execute(
            "SELECT daily_goal_minutes FROM settings WHERE id = 1"
        ).fetchone()
    return jsonify({
        "daily_goal_minutes": row["daily_goal_minutes"]
    })


@app.put("/api/study/goal")
def update_goal():
    data = request.get_json(silent=True) or {}
    try:
        minutes = int(data.get("daily_goal_minutes"))
    except (TypeError, ValueError):
        return jsonify({"error": "Goal must be an integer number of minutes"}), 400

    if not 1 <= minutes <= 1440:
        return jsonify({"error": "Goal must be between 1 and 1440 minutes"}), 400

    with connect() as con:
        con.execute(
            "UPDATE settings SET daily_goal_minutes = ? WHERE id = 1",
            (minutes,)
        )
    return jsonify({"daily_goal_minutes": minutes})


# ASSIGNMENTS AND EXAMS

@app.get("/api/study/tasks")
def list_tasks():
    with connect() as con:
        rows = con.execute("""
            SELECT t.*, s.name AS subject_name
            FROM tasks t
            LEFT JOIN subjects s ON s.id = t.subject_id
            ORDER BY t.completed ASC, t.due_date ASC
        """).fetchall()
    return jsonify([dict(row) for row in rows])


@app.post("/api/study/tasks")
def add_task():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    task_type = data.get("type")
    due_date = data.get("due_date")
    notes = str(data.get("notes", "")).strip()
    subject_id = data.get("subject_id")

    if not title:
        return jsonify({"error": "Title is required"}), 400
    if task_type not in ("assignment", "exam"):
        return jsonify({"error": "Type must be assignment or exam"}), 400
    if not valid_date(due_date):
        return jsonify({"error": "Due date must be YYYY-MM-DD"}), 400

    if subject_id is not None:
        try:
            subject_id = int(subject_id)
        except (TypeError, ValueError):
            return jsonify({"error": "subject_id must be an integer"}), 400

    with connect() as con:
        if subject_id is not None:
            subject = con.execute(
                "SELECT id FROM subjects WHERE id = ?", (subject_id,)
            ).fetchone()
            if not subject:
                return jsonify({"error": "Subject not found"}), 404

        cur = con.execute("""
            INSERT INTO tasks
            (title, task_type, subject_id, due_date, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (title, task_type, subject_id, due_date, notes))
        task_id = cur.lastrowid

    return jsonify({
        "id": task_id, "title": title, "type": task_type,
        "subject_id": subject_id, "due_date": due_date,
        "completed": False, "notes": notes
    }), 201


@app.patch("/api/study/tasks/<int:task_id>")
def update_task(task_id):
    data = request.get_json(silent=True) or {}
    allowed = {"title", "due_date", "notes", "completed"}
    if not data or not set(data).issubset(allowed):
        return jsonify({"error": "Provide title, due_date, notes, or completed"}), 400

    updates = {}
    for key, value in data.items():
        if key == "title":
            value = str(value).strip()
            if not value:
                return jsonify({"error": "Title cannot be empty"}), 400
        elif key == "due_date":
            if not valid_date(value):
                return jsonify({"error": "Due date must be YYYY-MM-DD"}), 400
        elif key == "notes":
            value = str(value)
        elif key == "completed":
            if not isinstance(value, bool):
                return jsonify({"error": "completed must be true or false"}), 400
            value = int(value)
        updates[key] = value

    columns = {"title": "title", "due_date": "due_date",
               "notes": "notes", "completed": "completed"}
    assignments = ", ".join(f"{columns[k]} = ?" for k in updates)

    with connect() as con:
        cur = con.execute(
            f"UPDATE tasks SET {assignments} WHERE id = ?",
            (*updates.values(), task_id)
        )
    if cur.rowcount == 0:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"message": "Task updated", "id": task_id})


@app.delete("/api/study/tasks/<int:task_id>")
def delete_task(task_id):
    with connect() as con:
        cur = con.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    if cur.rowcount == 0:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"message": "Task deleted"})


# DASHBOARD: TODAY + LAST SEVEN DAYS

@app.get("/api/study/dashboard")
def dashboard():
    today = date.today()
    week_start = today - timedelta(days=6)

    with connect() as con:
        goal_row = con.execute(
            "SELECT daily_goal_minutes FROM settings WHERE id = 1"
        ).fetchone()
        goal = goal_row["daily_goal_minutes"]

        today_minutes = con.execute("""
            SELECT COALESCE(SUM(duration_minutes), 0)
            FROM sessions WHERE session_date = ?
        """, (today.isoformat(),)).fetchone()[0]

        daily_rows = con.execute("""
            SELECT session_date, SUM(duration_minutes) AS minutes
            FROM sessions
            WHERE session_date BETWEEN ? AND ?
            GROUP BY session_date ORDER BY session_date
        """, (week_start.isoformat(), today.isoformat())).fetchall()

        subject_rows = con.execute("""
            SELECT s.id, s.name,
                   COALESCE(SUM(st.duration_minutes), 0) AS minutes
            FROM subjects s
            LEFT JOIN sessions st ON st.subject_id = s.id
            AND st.session_date BETWEEN ? AND ?
            GROUP BY s.id ORDER BY minutes DESC
        """, (week_start.isoformat(), today.isoformat())).fetchall()

        upcoming = con.execute("""
            SELECT t.*, s.name AS subject_name
            FROM tasks t LEFT JOIN subjects s ON s.id = t.subject_id
            WHERE t.completed = 0 AND t.due_date >= ?
            ORDER BY t.due_date LIMIT 5
        """, (today.isoformat(),)).fetchall()

    daily_map = {row["session_date"]: row["minutes"] for row in daily_rows}
    weekly = [
        {
            "date": (week_start + timedelta(days=i)).isoformat(),
            "minutes": daily_map.get(
                (week_start + timedelta(days=i)).isoformat(), 0
            )
        }
        for i in range(7)
    ]

    return jsonify({
        "today": today.isoformat(),
        "today_minutes": today_minutes,
        "daily_goal_minutes": goal,
        "goal_percent": min(100, round(today_minutes / goal * 100)),
        "weekly_total_minutes": sum(day["minutes"] for day in weekly),
        "weekly_progress": weekly,
        "subject_breakdown": [dict(row) for row in subject_rows],
        "upcoming_tasks": [dict(row) for row in upcoming]
    })


init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5002)
