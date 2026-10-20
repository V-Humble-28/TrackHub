import pytest

from trackers.expense.app import app, connect


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_expenses.db"
    monkeypatch.setattr("trackers.expense.app.DB", test_db)

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

    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_expense_health(client):
    response = client.get("/api/expense/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_add_expense(client):
    response = client.post(
        "/api/expense/entries",
        json={
            "description": "Lunch with friends",
            "amount": 450,
            "category": "food",
            "paid_by": "Vinu",
        },
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["description"] == "Lunch with friends"
    assert data["amount"] == 450.0
    assert data["category"] == "food"


def test_add_expense_validation(client):
    # Invalid category
    res = client.post(
        "/api/expense/entries",
        json={"description": "Test", "amount": 100, "category": "invalid_cat", "paid_by": "Me"},
    )
    assert res.status_code == 400

    # Negative amount
    res = client.post(
        "/api/expense/entries",
        json={"description": "Test", "amount": -10, "category": "food", "paid_by": "Me"},
    )
    assert res.status_code == 400

    # Missing description
    res = client.post(
        "/api/expense/entries",
        json={"description": "", "amount": 50, "category": "food"},
    )
    assert res.status_code == 400

    # Default paid_by to 'You' when omitted
    res = client.post(
        "/api/expense/entries",
        json={"description": "Snack", "amount": 50, "category": "food"},
    )
    assert res.status_code == 201
    assert res.get_json()["paid_by"] == "You"


def test_list_and_delete_expense(client):
    res = client.post(
        "/api/expense/entries",
        json={"description": "Metro pass", "amount": 200, "category": "transport", "paid_by": "Vinu"},
    )
    entry_id = res.get_json()["id"]

    list_res = client.get("/api/expense/entries")
    assert list_res.status_code == 200
    data = list_res.get_json()
    assert len(data["expenses"]) == 1
    assert data["total"] == 200.0
    assert data["category_totals"]["transport"] == 200.0

    del_res = client.delete(f"/api/expense/entries/{entry_id}")
    assert del_res.status_code == 200

    list_after = client.get("/api/expense/entries").get_json()
    assert len(list_after["expenses"]) == 0


def test_create_and_list_split_bill(client):
    # Create an equal split bill
    res = client.post(
        "/api/expense/splits",
        json={
            "title": "Team Dinner",
            "amount": 1500,
            "paid_by": "Vinu",
            "participants": ["Vinu", "Arjun", "Mira"],
            "mode": "equal",
        },
    )
    assert res.status_code == 201
    data = res.get_json()
    bill_id = data["bill_id"]
    assert data["total"] == 1500.0
    assert len(data["settlement"]) == 2
    assert all(item["owes"] == 500.0 for item in data["settlement"])

    # Test listing splits (persistent endpoint)
    splits_res = client.get("/api/expense/splits")
    assert splits_res.status_code == 200
    splits_data = splits_res.get_json()
    assert len(splits_data["bills"]) == 1
    assert splits_data["total_to_settle"] == 1000.0

    # Test deleting split bill
    del_res = client.delete(f"/api/expense/splits/{bill_id}")
    assert del_res.status_code == 200

    splits_after = client.get("/api/expense/splits").get_json()
    assert len(splits_after["bills"]) == 0
    assert splits_after["total_to_settle"] == 0.0
