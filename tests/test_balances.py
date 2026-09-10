from datetime import date
from vaults.balances import compute_starting_balance, get_daily_balances


def test_compute_starting_balance_no_transactions():
    tx = []
    assert compute_starting_balance(tx, date(2026, 1, 10)) == 0


def test_compute_starting_balance_only_before_start():
    tx = [
        {"vault": "A", "date": date(2026, 1, 1), "amount": 100},
        {"vault": "A", "date": date(2026, 1, 5), "amount": -20},
        {"vault": "A", "date": date(2026, 1, 10), "amount": 999},  # ignored
    ]
    assert compute_starting_balance(tx, date(2026, 1, 10)) == 80


def test_compute_starting_balance_multiple_vaults():
    tx = [
        {"vault": "A", "date": date(2026, 1, 1), "amount": 50},
        {"vault": "B", "date": date(2026, 1, 1), "amount": 999},
    ]
    # No vault filtering — both count
    assert compute_starting_balance(tx, date(2026, 1, 10)) == 1049


def test_get_daily_balances_no_transactions():
    vaults = ["A"]
    tx = []
    start = date(2026, 1, 1)
    end = date(2026, 1, 3)

    daily = get_daily_balances(vaults, tx, start, end)
    assert daily["A"][date(2026, 1, 1)] == 0
    assert daily["A"][date(2026, 1, 2)] == 0
    assert daily["A"][date(2026, 1, 3)] == 0


def test_get_daily_balances_with_transactions():
    vaults = ["A"]
    tx = [
        {"vault": "A", "date": date(2026, 1, 1), "amount": 100},
        {"vault": "A", "date": date(2026, 1, 2), "amount": -30},
        {"vault": "A", "date": date(2026, 1, 3), "amount": 10},
    ]
    start = date(2026, 1, 1)
    end = date(2026, 1, 3)

    daily = get_daily_balances(vaults, tx, start, end)
    assert daily["A"][date(2026, 1, 1)] == 100
    assert daily["A"][date(2026, 1, 2)] == 70
    assert daily["A"][date(2026, 1, 3)] == 80


def test_get_daily_balances_multiple_vaults():
    vaults = ["A", "B"]
    tx = [
        {"vault": "A", "date": date(2026, 1, 1), "amount": 50},
        {"vault": "B", "date": date(2026, 1, 2), "amount": 200},
    ]
    start = date(2026, 1, 1)
    end = date(2026, 1, 3)

    daily = get_daily_balances(vaults, tx, start, end)

    assert daily["A"][date(2026, 1, 1)] == 50
    assert daily["A"][date(2026, 1, 2)] == 50
    assert daily["A"][date(2026, 1, 3)] == 50

    assert daily["B"][date(2026, 1, 1)] == 0
    assert daily["B"][date(2026, 1, 2)] == 200
    assert daily["B"][date(2026, 1, 3)] == 200


def test_get_daily_balances_transactions_before_start():
    vaults = ["A"]
    tx = [
        {"vault": "A", "date": date(2025, 12, 31), "amount": 100},
        {"vault": "A", "date": date(2026, 1, 2), "amount": 50},
    ]
    start = date(2026, 1, 1)
    end = date(2026, 1, 3)

    daily = get_daily_balances(vaults, tx, start, end)

    assert daily["A"][date(2026, 1, 1)] == 100
    assert daily["A"][date(2026, 1, 2)] == 150
    assert daily["A"][date(2026, 1, 3)] == 150
