from datetime import date
from typer.testing import CliRunner
from vaults.cli import app as root_app
from vaults.summary import normalize_end_date, print_summary, summarize_month

import vaults.summary as s
import vaults.utils as u
import vaults.balances as b
import vaults.interest as i

runner = CliRunner()


class FakeDate(date):
    @classmethod
    def today(cls):
        return date(2026, 1, 1)


def test_normalize_end_date_full_date():
    assert normalize_end_date("2026-01-15") == date(2026, 1, 15)


def test_normalize_end_date_year_month():
    assert normalize_end_date("2026-02") == date(2026, 2, 28)


def test_normalize_end_date_invalid():
    try:
        normalize_end_date("invalid")
    except ValueError as e:
        assert "invalid" in str(e).lower()


def test_print_summary_executes(capsys):
    summary_data = {
        "A": {
            "start": 100,
            "end": 200,
            "deposits": 100,
            "withdrawals": 0,
            "interest": 5,
        }
    }
    end_date = date(2026, 1, 31)

    print_summary(summary_data, end_date)
    output = capsys.readouterr().out

    assert "Vault Summary" in output
    assert "A" in output
    assert "GRAND TOTAL" in output


def test_summary_cli_executes(monkeypatch):
    # Patch date.today() used inside summary_cli
    monkeypatch.setattr(s, "date", FakeDate)

    # Patch utils
    monkeypatch.setattr(u, "ensure_all", lambda: None)
    monkeypatch.setattr(u, "load_vaults", lambda: ["A"])
    monkeypatch.setattr(u, "load_rates", lambda: {"A": 0.05})
    monkeypatch.setattr(
        u,
        "load_transactions",
        lambda: [{"vault": "A", "date": date(2026, 1, 1), "amount": 100}],
    )

    # Patch balances + interest
    monkeypatch.setattr(
        b, "get_daily_balances", lambda *args: {"A": {date(2026, 1, 1): 100}}
    )
    monkeypatch.setattr(
        i, "get_daily_interest", lambda *args: {"A": {date(2026, 1, 1): 1}}
    )

    # Patch summarize_month
    monkeypatch.setattr(
        s,
        "summarize_month",
        lambda *args: {
            "A": {
                "start": 100,
                "end": 100,
                "deposits": 100,
                "withdrawals": 0,
                "interest": 1,
            }
        },
    )

    # Invoke the REAL CLI app
    result = runner.invoke(root_app, ["summary"])

    assert result.exit_code == 0
    assert "Vault Summary" in result.output


def test_summary_empty_month():
    start = date(2026, 1, 1)
    end = date(2026, 1, 31)

    daily_balances = {"A": {start: 0, end: 0}}
    daily_interest = {"A": {}}
    transactions = []
    vaults = ["A"]

    summary = summarize_month(
        daily_balances, daily_interest, transactions, vaults, start, end
    )

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

    summary = summarize_month(
        daily_balances, daily_interest, transactions, vaults, start, end
    )

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

    summary = summarize_month(
        daily_balances, daily_interest, transactions, vaults, start, end
    )

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

    summary = summarize_month(
        daily_balances, daily_interest, transactions, vaults, start, end
    )

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
