from datetime import date
from vaults.summary import summarize_month


def test_summary_empty_month():
    start = date(2026, 1, 1)
    end = date(2026, 1, 31)

    daily_balances = {"A": {start: 0, end: 0}}
    daily_interest = {"A": {}}
    transactions = []
    vaults = ["A"]

    summary = summarize_month(daily_balances, daily_interest, transactions, vaults, start, end)

    assert summary["A"]["start"] == 0
    assert summary["A"]["end"] == 0
    assert summary["A"]["deposits"] == 0
    assert summary["A"]["withdrawals"] == 0
    assert summary["A"]["interest"] == 0


def test_summary_with_balances_and_interest():
    start = date(2026, 1, 1)
    end = date(2026, 1, 3)

    daily_balances = {
        "A": {
            start: 100,
            date(2026, 1, 2): 150,
            end: 200,
        }
    }
    daily_interest = {
        "A": {
            start: 1.0,
            date(2026, 1, 2): 1.5,
            end: 2.0,
        }
    }
    transactions = []
    vaults = ["A"]

    summary = summarize_month(daily_balances, daily_interest, transactions, vaults, start, end)

    assert summary["A"]["start"] == 100
    assert summary["A"]["end"] == 200
    assert summary["A"]["interest"] == 4.5
    assert summary["A"]["deposits"] == 0
    assert summary["A"]["withdrawals"] == 0


def test_summary_with_deposits_and_withdrawals():
    start = date(2026, 1, 1)
    end = date(2026, 1, 3)

    daily_balances = {
        "A": {
            start: 100,
            date(2026, 1, 2): 200,
            end: 150,
        }
    }
    daily_interest = {"A": {}}

    transactions = [
        {"vault": "A", "date": date(2026, 1, 2), "amount": 100},
        {"vault": "A", "date": date(2026, 1, 3), "amount": -50},
    ]

    vaults = ["A"]

    summary = summarize_month(daily_balances, daily_interest, transactions, vaults, start, end)

    assert summary["A"]["start"] == 100
    assert summary["A"]["end"] == 150
    assert summary["A"]["deposits"] == 100
    assert summary["A"]["withdrawals"] == 50
    assert summary["A"]["interest"] == 0


def test_summary_multiple_vaults():
    start = date(2026, 1, 1)
    end = date(2026, 1, 2)

    daily_balances = {
        "A": {start: 100, end: 200},
        "B": {start: 300, end: 250},
    }
    daily_interest = {
        "A": {start: 1, end: 2},
        "B": {start: 3, end: 4},
    }
    transactions = [
        {"vault": "A", "date": end, "amount": 100},
        {"vault": "B", "date": end, "amount": -50},
    ]
    vaults = ["A", "B"]

    summary = summarize_month(daily_balances, daily_interest, transactions, vaults, start, end)

    assert summary["A"]["start"] == 100
    assert summary["A"]["end"] == 200
    assert summary["A"]["deposits"] == 100
    assert summary["A"]["withdrawals"] == 0
    assert summary["A"]["interest"] == 3

    assert summary["B"]["start"] == 300
    assert summary["B"]["end"] == 250
    assert summary["B"]["deposits"] == 0
    assert summary["B"]["withdrawals"] == 50
    assert summary["B"]["interest"] == 7
