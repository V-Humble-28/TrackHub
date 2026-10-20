
from flask import Flask, request, jsonify
import sqlite3
from pathlib import Path
from datetime import date

app = Flask(__name__)

DATABASE = Path(__file__).with_name("calorie.db")


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_table():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS food_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                food_name TEXT NOT NULL,
                weight REAL NOT NULL,
                calories_per_100g REAL NOT NULL,
                meal TEXT NOT NULL,
                entry_date TEXT NOT NULL
            )
        """)


@app.route("/api/calorie/entries", methods=["POST"])
def add_food():
    data = request.get_json(silent=True) or {}

    food_name = str(data.get("food_name", "")).strip()
    meal = str(data.get("meal", "")).strip().lower()

    try:
        weight = float(data.get("weight", 0))
        calories_per_100g = float(data.get("calories_per_100g", -1))
    except (ValueError, TypeError):
        return jsonify({"error": "Weight and calories must be numbers"}), 400

    if not food_name:
        return jsonify({"error": "Food name is required"}), 400

    if weight <= 0 or calories_per_100g < 0:
        return jsonify({"error": "Invalid weight or calorie value"}), 400

    if meal not in ["breakfast", "lunch", "dinner", "snack"]:
        return jsonify({"error": "Invalid meal type"}), 400

    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO food_entries
            (food_name, weight, calories_per_100g, meal, entry_date)
            VALUES (?, ?, ?, ?, ?)
        """, (food_name, weight, calories_per_100g, meal, date.today().isoformat()))

        entry_id = cursor.lastrowid

    calories = round(weight * calories_per_100g / 100, 2)

    return jsonify({
        "message": "Food added successfully",
        "id": entry_id,
        "food_name": food_name,
        "weight": weight,
        "meal": meal,
        "calories": calories
    }), 201


@app.route("/api/calorie/entries", methods=["GET"])
def get_food_entries():
    selected_date = request.args.get("date", date.today().isoformat())

    with get_connection() as connection:
        entries = connection.execute("""
            SELECT id, food_name, weight, calories_per_100g, meal
            FROM food_entries
            WHERE entry_date = ?
            ORDER BY id DESC
        """, (selected_date,)).fetchall()

    food_log = []
    total_calories = 0

    for entry in entries:
        calories = round(entry["weight"] * entry["calories_per_100g"] / 100, 2)
        total_calories += calories

        food_log.append({
            "id": entry["id"],
            "food_name": entry["food_name"],
            "weight": entry["weight"],
            "meal": entry["meal"],
            "calories": calories
        })

    return jsonify({
        "date": selected_date,
        "entries": food_log,
        "total_calories": round(total_calories, 2)
    })


create_table()

if __name__ == "__main__":
    app.run(debug=True)
