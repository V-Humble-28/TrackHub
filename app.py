"""Single local server for the Track Hub interface and tracker APIs."""

from pathlib import Path

from flask import Flask, abort, send_from_directory

from trackers.calorie.app import app as calorie_app
from trackers.expense.app import app as expense_app
from trackers.habit.app import app as habit_app
from trackers.study.app import app as study_app

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)


def register_tracker_routes(source_app, namespace):
    """Expose an existing tracker Flask app through this unified server."""
    for rule in source_app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue

        methods = rule.methods.difference({"HEAD", "OPTIONS"})
        app.add_url_rule(
            rule.rule,
            endpoint=f"{namespace}.{rule.endpoint}",
            view_func=source_app.view_functions[rule.endpoint],
            methods=methods,
        )


register_tracker_routes(calorie_app, "calorie")
register_tracker_routes(expense_app, "expense")
register_tracker_routes(habit_app, "habit")
register_tracker_routes(study_app, "study")

TRACKER_NAMES = ("calorie", "expense", "habit", "study")


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return response


@app.route("/", defaults={"path": ""}, methods=["OPTIONS"])
@app.route("/<path:path>", methods=["OPTIONS"])
def handle_options(path):
    response = app.make_default_options_response()
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return response


@app.get("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/calorie")
def calorie_page():
    return send_from_directory(BASE_DIR / "trackers" / "calorie", "calorie.html")


@app.get("/expense")
def expense_page():
    return send_from_directory(BASE_DIR / "trackers" / "expense", "expense.html")


@app.get("/habit")
def habit_page():
    return send_from_directory(BASE_DIR / "trackers" / "habit", "habit.html")


@app.get("/study")
def study_page():
    return send_from_directory(BASE_DIR / "trackers" / "study", "study.html")


@app.get("/<path:asset>")
def frontend_asset(asset):
    # Direct path under repository root (e.g. trackers/calorie/calorie.html, tracker.css)
    target = (BASE_DIR / asset).resolve()
    if target.is_file() and target.is_relative_to(BASE_DIR):
        return send_from_directory(target.parent, target.name)

    # Top-level fallback alias (e.g. /calorie.html or /calorie.js)
    for tracker in TRACKER_NAMES:
        alias_target = (BASE_DIR / "trackers" / tracker / asset).resolve()
        if alias_target.is_file() and alias_target.is_relative_to(BASE_DIR):
            return send_from_directory(alias_target.parent, alias_target.name)

    abort(404)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
