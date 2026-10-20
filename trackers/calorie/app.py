
import csv
import math
import sqlite3
from datetime import date
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "calorie.db"
FOODS_CSV = BASE_DIR / "data" / "foods.csv"

VALID_MEALS = {"breakfast", "lunch", "dinner", "snack"}


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


def load_foods():
    """Read the local Indian food nutrition dataset."""
    with FOODS_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def find_food(food_id):
    """Find a dataset food using its ID."""
    for food in load_foods():
        if food["id"] == str(food_id):
            return food
    return None


def calculate_calories(weight, calories_per_100g):
    return round(weight * calories_per_100g / 100, 2)


def valid_date(value):
    try:
        return date.fromisoformat(value).isoformat() == value
    except (ValueError, TypeError):
        return False


@app.route("/api/calorie/foods", methods=["GET"])
def search_foods():
    query = request.args.get("q", "").strip().casefold()
    category = request.args.get("category", "").strip().casefold()

    try:
        limit = int(request.args.get("limit", 50))
    except ValueError:
        return jsonify({"error": "Limit must be a number"}), 400

    if not 1 <= limit <= 100:
        return jsonify({"error": "Limit must be between 1 and 100"}), 400

    try:
        foods = load_foods()
    except (OSError, csv.Error):
        app.logger.exception("Could not load food dataset")
        return jsonify({"error": "Food dataset is unavailable"}), 500

    matches = []
    for food in foods:
        if query and query not in food["name"].casefold() and query not in food["name_hindi"].casefold():
            continue
        if category and category not in food["category"].casefold():
            continue

        matches.append({
            "id": int(food["id"]),
            "name": food["name"],
            "name_hindi": food["name_hindi"],
            "category": food["category"],
            "calories_per_100g": float(food["energy_kcal"]),
            "protein_g": float(food["protein_g"]),
            "fat_g": float(food["fat_g"]),
            "carbs_g": float(food["carbs_g"]),
            "fiber_g": float(food["fiber_g"]),
            "source": food["source"],
        })

        if len(matches) >= limit:
            break

    return jsonify({"foods": matches, "count": len(matches)})


@app.route("/api/calorie/entries", methods=["POST"])
def add_food():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    food_id = data.get("food_id")
    food = None

    # Preferred method: look up calories from the local dataset.
    if food_id is not None:
        try:
            food_id = int(food_id)
        except (ValueError, TypeError):
            return jsonify({"error": "food_id must be an integer"}), 400

        food = find_food(food_id)
        if food is None:
            return jsonify({"error": "Food not found in dataset"}), 404

        food_name = food["name"]
        try:
            calories_per_100g = float(food["energy_kcal"])
        except (ValueError, TypeError):
            return jsonify({"error": "Food has invalid nutrition data"}), 500

    else:
        # Backward compatibility with the previous API format.
        food_name = str(data.get("food_name", "")).strip()
        try:
            calories_per_100g = float(data.get("calories_per_100g", -1))
        except (ValueError, TypeError):
            return jsonify({"error": "Calories must be a number"}), 400

    meal = str(data.get("meal", "")).strip().lower()

    try:
        weight = float(data.get("weight", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Weight must be a number"}), 400

    if not food_name:
        return jsonify({"error": "Food name is required"}), 400
    if not math.isfinite(weight) or weight <= 0:
        return jsonify({"error": "Weight must be a positive finite number"}), 400
    if not math.isfinite(calories_per_100g) or calories_per_100g < 0:
        return jsonify({"error": "Calories must be a non-negative finite number"}), 400
    if meal not in VALID_MEALS:
        return jsonify({"error": "Meal must be breakfast, lunch, dinner, or snack"}), 400

    entry_date = date.today().isoformat()
    calories = calculate_calories(weight, calories_per_100g)

    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO food_entries
            (food_name, weight, calories_per_100g, meal, entry_date)
            VALUES (?, ?, ?, ?, ?)
        """, (food_name, weight, calories_per_100g, meal, entry_date))
        entry_id = cursor.lastrowid

    return jsonify({
        "message": "Food added successfully",
        "id": entry_id,
        "food_name": food_name,
        "weight": weight,
        "meal": meal,
        "date": entry_date,
        "calories_per_100g": calories_per_100g,
        "calories": calories,
        "source": "dataset" if food is not None else "manual",
    }), 201


@app.route("/api/calorie/entries", methods=["GET"])
def get_food_entries():
    selected_date = request.args.get("date", date.today().isoformat())

    if not valid_date(selected_date):
        return jsonify({"error": "Date must be in YYYY-MM-DD format"}), 400

    with get_connection() as connection:
        entries = connection.execute("""
            SELECT id, food_name, weight, calories_per_100g, meal, entry_date
            FROM food_entries
            WHERE entry_date = ?
            ORDER BY id DESC
        """, (selected_date,)).fetchall()

    food_log = []
    total_calories = 0.0

    for entry in entries:
        calories = calculate_calories(
            entry["weight"], entry["calories_per_100g"]
        )
        total_calories += calories

        food_log.append({
            "id": entry["id"],
            "food_name": entry["food_name"],
            "weight": entry["weight"],
            "meal": entry["meal"],
            "date": entry["entry_date"],
            "calories_per_100g": entry["calories_per_100g"],
            "calories": calories,
        })

    return jsonify({
        "date": selected_date,
        "entries": food_log,
        "total_calories": round(total_calories, 2),
        "entry_count": len(food_log),
    })


@app.route("/api/calorie/entries/<int:entry_id>", methods=["PUT"])
def update_food(entry_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    with get_connection() as connection:
        existing = connection.execute(
            "SELECT * FROM food_entries WHERE id = ?", (entry_id,)
        ).fetchone()

        if existing is None:
            return jsonify({"error": "Food entry not found"}), 404

        food_name = existing["food_name"]
        calories_per_100g = existing["calories_per_100g"]

        if "food_id" in data:
            try:
                food_id = int(data["food_id"])
            except (ValueError, TypeError):
                return jsonify({"error": "food_id must be an integer"}), 400

            food = find_food(food_id)
            if food is None:
                return jsonify({"error": "Food not found in dataset"}), 404

            food_name = food["name"]
            calories_per_100g = float(food["energy_kcal"])

        try:
            weight = float(data.get("weight", existing["weight"]))
        except (ValueError, TypeError):
            return jsonify({"error": "Weight must be a number"}), 400

        meal = str(data.get("meal", existing["meal"])).strip().lower()

        if not math.isfinite(weight) or weight <= 0:
            return jsonify({"error": "Weight must be a positive finite number"}), 400
        if meal not in VALID_MEALS:
            return jsonify({"error": "Invalid meal type"}), 400

        connection.execute("""
            UPDATE food_entries
            SET food_name = ?, weight = ?, calories_per_100g = ?, meal = ?
            WHERE id = ?
        """, (food_name, weight, calories_per_100g, meal, entry_id))

    return jsonify({
        "message": "Food entry updated successfully",
        "id": entry_id,
        "food_name": food_name,
        "weight": weight,
        "meal": meal,
        "calories": calculate_calories(weight, calories_per_100g),
    })


@app.route("/api/calorie/entries/<int:entry_id>", methods=["DELETE"])
def delete_food(entry_id):
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM food_entries WHERE id = ?", (entry_id,)
        )

        if cursor.rowcount == 0:
            return jsonify({"error": "Food entry not found"}), 404

    return jsonify({"message": "Food entry deleted successfully", "id": entry_id})


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})


create_table()

if __name__ == "__main__":
    app.run(debug=True)
