
from flask import Flask, request, jsonify
import sqlite3
from pathlib import Path
from datetime import date

app = Flask(__name__)

DB = Path(__file__).resolve().parent / "expenses.db"

CATEGORIES = {
    "college", "food", "grocery", "entertainment",
    "subscriptions", "transport", "other"
}


def connect():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def create_tables():
    with connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                paid_by TEXT NOT NULL,
                expense_date TEXT NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                total REAL NOT NULL,
                paid_by TEXT NOT NULL,
                mode TEXT NOT NULL,
                bill_date TEXT NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS bill_shares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_id INTEGER NOT NULL,
                person TEXT NOT NULL,
                amount REAL NOT NULL,
                FOREIGN KEY (bill_id) REFERENCES bills(id)
            )
        """)


@app.get("/api/expense/health")
def health():
    return jsonify({"status": "ok", "app": "Expense Tracker"})


@app.post("/api/expense/entries")
def add_expense():
    data = request.get_json(silent=True) or {}

    description = str(data.get("description", "")).strip()
    paid_by = str(data.get("paid_by", "")).strip() or "You"
    category = str(data.get("category", "")).strip().lower()

    try:
        amount = round(float(data.get("amount", 0)), 2)
    except (TypeError, ValueError):
        return jsonify({"error": "Amount must be a number"}), 400

    if not description:
        return jsonify({"error": "Description is required"}), 400
    if amount <= 0:
        return jsonify({"error": "Amount must be greater than zero"}), 400
    if category not in CATEGORIES:
        return jsonify({"error": "Invalid category", "allowed": sorted(CATEGORIES)}), 400

    expense_date = str(data.get("date") or date.today().isoformat())

    try:
        date.fromisoformat(expense_date)
    except ValueError:
        return jsonify({"error": "Date must be YYYY-MM-DD"}), 400

    with connect() as con:
        cur = con.execute("""
            INSERT INTO expenses
            (description, amount, category, paid_by, expense_date)
            VALUES (?, ?, ?, ?, ?)
        """, (description, amount, category, paid_by, expense_date))
        expense_id = cur.lastrowid

    return jsonify({
        "message": "Expense added",
        "id": expense_id,
        "description": description,
        "amount": amount,
        "category": category,
        "paid_by": paid_by,
        "date": expense_date
    }), 201


@app.get("/api/expense/entries")
def list_expenses():
    month = request.args.get("month")
    day = request.args.get("date")

    if day:
        try:
            date.fromisoformat(day)
        except ValueError:
            return jsonify({"error": "Date must be YYYY-MM-DD"}), 400
        condition, value = "expense_date = ?", day
    elif month:
        try:
            date.fromisoformat(month + "-01")
        except ValueError:
            return jsonify({"error": "Month must be YYYY-MM"}), 400
        condition, value = "expense_date LIKE ?", month + "%"
    else:
        condition, value = "1 = 1", None

    with connect() as con:
        if value is None:
            rows = con.execute(
                "SELECT * FROM expenses ORDER BY expense_date DESC, id DESC"
            ).fetchall()
        else:
            rows = con.execute(
                f"SELECT * FROM expenses WHERE {condition} "
                "ORDER BY expense_date DESC, id DESC", (value,)
            ).fetchall()

    expenses = [dict(row) for row in rows]
    totals = {}
    for item in expenses:
        totals[item["category"]] = round(
            totals.get(item["category"], 0) + item["amount"], 2
        )

    return jsonify({
        "expenses": expenses,
        "total": round(sum(item["amount"] for item in expenses), 2),
        "category_totals": totals
    })


@app.delete("/api/expense/entries/<int:expense_id>")
def delete_expense(expense_id):
    with connect() as con:
        cur = con.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    if cur.rowcount == 0:
        return jsonify({"error": "Expense not found"}), 404
    return jsonify({"message": "Expense deleted"})


@app.post("/api/expense/splits")
def create_split():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    mode = data.get("mode")
    paid_by = str(data.get("paid_by", "")).strip()
    participants = data.get("participants")

    if not title or mode not in {"equal", "itemized"}:
        return jsonify({"error": "Provide title and mode equal/itemized"}), 400
    if not isinstance(participants, list) or not participants:
        return jsonify({"error": "participants must be a non-empty list"}), 400

    participants = list(dict.fromkeys(
        str(person).strip() for person in participants if str(person).strip()
    ))
    if paid_by and paid_by not in participants:
        participants.insert(0, paid_by)
    if not participants:
        return jsonify({"error": "paid_by must be one of the participants"}), 400

    shares = {person: 0 for person in participants}

    if mode == "equal":
        try:
            total = round(float(data.get("amount", 0)), 2)
        except (TypeError, ValueError):
            return jsonify({"error": "amount must be a number"}), 400
        if total <= 0:
            return jsonify({"error": "amount must be greater than zero"}), 400

        cents = round(total * 100)
        base, remainder = divmod(cents, len(participants))
        for index, person in enumerate(participants):
            shares[person] = (base + (1 if index < remainder else 0)) / 100

    else:
        items = data.get("items")
        if not isinstance(items, list) or not items:
            return jsonify({"error": "Itemized mode requires items"}), 400

        total_cents = 0
        for item in items:
            if not isinstance(item, dict):
                return jsonify({"error": "Each item must be an object"}), 400
            person = str(item.get("person", "")).strip()
            name = str(item.get("name", "")).strip()
            try:
                cents = round(float(item.get("amount", 0)) * 100)
            except (TypeError, ValueError):
                return jsonify({"error": "Each item needs a numeric amount"}), 400

            if person not in shares or not name or cents <= 0:
                return jsonify({
                    "error": "Each item needs a name, positive amount, and participant"
                }), 400
            shares[person] += cents / 100
            total_cents += cents

        total = total_cents / 100

    with connect() as con:
        cur = con.execute("""
            INSERT INTO bills (title, total, paid_by, mode, bill_date)
            VALUES (?, ?, ?, ?, ?)
        """, (title, total, paid_by, mode, date.today().isoformat()))
        bill_id = cur.lastrowid

        for person, amount in shares.items():
            con.execute("""
                INSERT INTO bill_shares (bill_id, person, amount)
                VALUES (?, ?, ?)
            """, (bill_id, person, amount))

    settlement = [
        {"person": person, "owes": amount, "to": paid_by}
        for person, amount in shares.items()
        if person != paid_by and amount > 0
    ]

    return jsonify({
        "bill_id": bill_id,
        "title": title,
        "mode": mode,
        "total": round(total, 2),
        "paid_by": paid_by,
        "shares": shares,
        "settlement": settlement
    }), 201


@app.get("/api/expense/splits")
def list_splits():
    with connect() as con:
        bills = con.execute(
            "SELECT * FROM bills ORDER BY bill_date DESC, id DESC"
        ).fetchall()

        bill_list = []
        total_to_settle = 0.0

        for b in bills:
            shares_rows = con.execute(
                "SELECT person, amount FROM bill_shares WHERE bill_id = ?",
                (b["id"],)
            ).fetchall()
            shares = {row["person"]: row["amount"] for row in shares_rows}
            settlement = [
                {"person": person, "owes": amount, "to": b["paid_by"]}
                for person, amount in shares.items()
                if person != b["paid_by"] and amount > 0
            ]
            bill_settle_sum = sum(s["owes"] for s in settlement)
            total_to_settle += bill_settle_sum

            bill_list.append({
                "id": b["id"],
                "title": b["title"],
                "total": b["total"],
                "paid_by": b["paid_by"],
                "mode": b["mode"],
                "bill_date": b["bill_date"],
                "shares": shares,
                "settlement": settlement,
                "settle_total": round(bill_settle_sum, 2),
            })

    return jsonify({
        "bills": bill_list,
        "total_to_settle": round(total_to_settle, 2),
    })


@app.get("/api/expense/splits/<int:bill_id>")
def get_split(bill_id):
    with connect() as con:
        bill = con.execute(
            "SELECT * FROM bills WHERE id = ?", (bill_id,)
        ).fetchone()
        rows = con.execute(
            "SELECT person, amount FROM bill_shares WHERE bill_id = ?",
            (bill_id,)
        ).fetchall()

    if bill is None:
        return jsonify({"error": "Bill not found"}), 404

    return jsonify({
        "bill": dict(bill),
        "shares": [dict(row) for row in rows]
    })


@app.delete("/api/expense/splits/<int:bill_id>")
def delete_split(bill_id):
    with connect() as con:
        con.execute("DELETE FROM bill_shares WHERE bill_id = ?", (bill_id,))
        cur = con.execute("DELETE FROM bills WHERE id = ?", (bill_id,))
    if cur.rowcount == 0:
        return jsonify({"error": "Bill not found"}), 404
    return jsonify({"message": "Bill deleted", "id": bill_id})


create_tables()

if __name__ == "__main__":
    app.run(debug=True, port=5001)
