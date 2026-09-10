import os
import csv
from datetime import date
from typer.testing import CliRunner
import pytest

from vaults.cli import app
from vaults.utils import RATES_FILE

runner = CliRunner()


# -----------------------------
# Helpers
# -----------------------------
@pytest.fixture
def temp_rates(tmp_path, monkeypatch):
    rates_file = tmp_path / "rates.csv"

    # Patch utils (where the real file paths live)
    monkeypatch.setattr("vaults.utils.RATES_FILE", str(rates_file))

    # Patch vaults.rates (because it imported RATES_FILE directly)
    monkeypatch.setattr("vaults.rates.RATES_FILE", str(rates_file))

    return rates_file


@pytest.fixture
def mock_utils(monkeypatch):
    """Patch ensure_all so it doesn't touch the real filesystem."""
    monkeypatch.setattr("vaults.utils.ensure_all", lambda: None)


# -----------------------------
# rates list
# -----------------------------
def test_rates_list_no_rates(temp_rates, mock_utils):
    # Empty file → load_rates() returns []
    with open(temp_rates, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["start", "end", "apy"])

    result = runner.invoke(app, ["rates", "list"])

    assert "No rates defined." in result.output
    assert result.exit_code == 0


def test_rates_list_with_rates(temp_rates, mock_utils):
    with open(temp_rates, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["start", "end", "apy"])
        writer.writerow(["2024-01-01", "2024-06-01", "0.0500"])
        writer.writerow(["2024-06-02", "", "0.0700"])

    result = runner.invoke(app, ["rates", "list"])

    assert "Rate history:" in result.output
    assert "2024-01-01 -> 2024-06-01 : 0.0500" in result.output
    assert "2024-06-02 -> present : 0.0700" in result.output


# -----------------------------
# rates add
# -----------------------------
def test_rates_add_updates_previous(temp_rates, mock_utils):
    # Existing rate starting Jan 1
    with open(temp_rates, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["start", "end", "apy"])
        writer.writerow(["2024-01-01", "", "0.0500"])

    result = runner.invoke(app, ["rates", "add", "--start", "2024-06-01", "--apy", "0.0700"])

    assert "Added rate: 2024-06-01 -> present @ 0.0700" in result.output
    assert "Previous rate period updated automatically." in result.output

    # Validate CSV output
    with open(temp_rates) as f:
        rows = list(csv.reader(f))

    assert rows[1] == ["2024-01-01", "2024-05-31", "0.05"]
    assert rows[2] == ["2024-06-01", "", "0.07"]


# -----------------------------
# rates calibrate
# -----------------------------
def test_rates_calibrate(temp_rates, mock_utils, monkeypatch):
    # Patch parse_date into rates module
    import vaults.utils as utils
    monkeypatch.setattr("vaults.rates.parse_date", utils.parse_date, raising=False)

    # Patch vaults.rates functions
    monkeypatch.setattr("vaults.rates.load_vaults", lambda: {"A": 1000})
    monkeypatch.setattr("vaults.rates.load_transactions", lambda: [])

    # Patch interest calculation
    def fake_interest(vaults, tx, rates, end_date):
        apy = rates[0]["apy"]
        return {"A": apy * 1000}

    monkeypatch.setattr("vaults.interest.calculate_interest", fake_interest)

    # Run CLI
    result = runner.invoke(app, ["rates", "calibrate", "--target", "50", "--month", "2024-01"])

    assert "Calibrated APY for 2024-01:" in result.output

    with open(temp_rates) as f:
        rows = list(csv.reader(f))

    assert rows[0] == ["start", "end", "apy"]
    assert rows[1][0] == "2024-01-01"
    assert rows[1][1] == "2024-01-31"
    assert float(rows[1][2]) > 0
    assert rows[2] == ["2026-05-01", "", "0.0310"]
