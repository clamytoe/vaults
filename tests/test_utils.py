import csv
import os
from datetime import date
import pytest

import vaults.utils as utils


# -----------------------------------
# Fixtures: redirect DATA_DIR safely
# -----------------------------------
@pytest.fixture
def temp_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "DATA_DIR", tmp_path)
    monkeypatch.setattr(utils, "VAULTS_FILE", tmp_path / "vaults.csv")
    monkeypatch.setattr(utils, "TRANSACTIONS_FILE", tmp_path / "transactions.csv")
    monkeypatch.setattr(utils, "RATES_FILE", tmp_path / "rates.csv")
    monkeypatch.setattr(utils, "POSTINGS_FILE", tmp_path / "posting.csv")
    return tmp_path


# -----------------------------------
# ensure_* tests
# -----------------------------------
def test_ensure_data_directory(temp_data_dir):
    utils.ensure_data_directory()
    assert temp_data_dir.exists()


def test_ensure_vaults_file(temp_data_dir):
    utils.ensure_vaults_file()
    assert utils.VAULTS_FILE.exists()

    with open(utils.VAULTS_FILE) as f:
        header = f.readline().strip()
    assert header == "name"


def test_ensure_transactions_file(temp_data_dir):
    utils.ensure_transactions_file()
    assert utils.TRANSACTIONS_FILE.exists()

    with open(utils.TRANSACTIONS_FILE) as f:
        header = f.readline().strip().split(",")
    assert header == utils.HEADER


def test_ensure_rates_file(temp_data_dir):
    utils.ensure_rates_file()
    assert utils.RATES_FILE.exists()

    with open(utils.RATES_FILE) as f:
        header = f.readline().strip().split(",")
    assert header == ["start", "end", "apy"]


def test_ensure_postings_file(temp_data_dir):
    utils.ensure_postings_file()
    assert utils.POSTINGS_FILE.exists()

    with open(utils.POSTINGS_FILE) as f:
        header = f.readline().strip().split(",")
    assert header == ["original", "posted"]


def test_ensure_all_creates_everything(temp_data_dir):
    utils.ensure_all()

    assert utils.VAULTS_FILE.exists()
    assert utils.TRANSACTIONS_FILE.exists()
    assert utils.RATES_FILE.exists()
    assert utils.POSTINGS_FILE.exists()


# -----------------------------------
# parse_date
# -----------------------------------
def test_parse_date_iso():
    d = utils.parse_date("2024-01-01")
    assert d == date(2024, 1, 1)


def test_parse_date_compact():
    d = utils.parse_date("20240101")
    assert d == date(2024, 1, 1)


def test_parse_date_invalid():
    with pytest.raises(ValueError):
        utils.parse_date("not-a-date")


# -----------------------------------
# load_vaults / save_vaults
# -----------------------------------
def test_load_vaults_empty(temp_data_dir):
    utils.ensure_vaults_file()
    assert utils.load_vaults() == []


def test_save_and_load_vaults(temp_data_dir):
    utils.save_vaults(["A", "B", "C"])
    vaults = utils.load_vaults()
    assert vaults == ["A", "B", "C"]


# -----------------------------------
# load_postings
# -----------------------------------
def test_load_postings(temp_data_dir):
    utils.ensure_postings_file()

    with open(utils.POSTINGS_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["original", "posted"])
        writer.writerow(["2024-01-01", "2024-01-03"])
        writer.writerow(["2024-01-02", "2024-01-05"])

    postings = utils.load_postings()

    assert len(postings) == 2
    assert postings["2024-01-01"] == date(2024, 1, 3)
    assert postings["2024-01-02"] == date(2024, 1, 5)


# -----------------------------------
# load_transactions
# -----------------------------------
def test_load_transactions_basic(temp_data_dir):
    utils.ensure_transactions_file()
    utils.ensure_postings_file()

    # No postings override
    with open(utils.TRANSACTIONS_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(utils.HEADER)
        writer.writerow(["2024-01-01", "A", "100", "Deposit"])

    tx = utils.load_transactions()
    assert len(tx) == 1
    assert tx[0]["vault"] == "A"
    assert tx[0]["date"] == date(2024, 1, 1)
    assert tx[0]["amount"] == 100.0
    assert tx[0]["note"] == "Deposit"


def test_load_transactions_with_posting_override(temp_data_dir):
    utils.ensure_transactions_file()

    # Create postings override
    with open(utils.POSTINGS_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["original", "posted"])
        writer.writerow(["2024-01-01", "2024-01-03"])

    # Transaction with original date
    with open(utils.TRANSACTIONS_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(utils.HEADER)
        writer.writerow(["2024-01-01", "A", "50", "Override test"])

    tx = utils.load_transactions()
    assert tx[0]["date"] == date(2024, 1, 3)  # overridden


# -----------------------------------
# load_rates
# -----------------------------------
def test_load_rates(temp_data_dir):
    utils.ensure_rates_file()

    with open(utils.RATES_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["start", "end", "apy"])
        writer.writerow(["2024-01-01", "2024-06-01", "0.05"])
        writer.writerow(["2024-06-02", "", "0.07"])

    rates = utils.load_rates()

    assert len(rates) == 2
    assert rates[0]["start"] == date(2024, 1, 1)
    assert rates[0]["end"] == date(2024, 6, 1)
    assert rates[0]["apy"] == 0.05

    assert rates[1]["end"] is None
    assert rates[1]["apy"] == 0.07
