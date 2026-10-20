"""Single local server for the Track Hub interface and tracker APIs."""

from pathlib import Path

from flask import Flask, abort, send_from_directory

from trackers.calorie.app import app as calorie_app
from trackers.expense.app import app as expense_app

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

ASSETS = {
    "index.html",
    "calorie.html",
    "expense.html",
    "tracker.css",
    "title-animation.js",
    "calorie.js",
    "expense.js",
}


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
    return send_from_directory(BASE_DIR, "calorie.html")


@app.get("/expense")
def expense_page():
    return send_from_directory(BASE_DIR, "expense.html")


@app.get("/<path:asset>")
def frontend_asset(asset):
    if asset not in ASSETS:
        abort(404)
    return send_from_directory(BASE_DIR, asset)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
