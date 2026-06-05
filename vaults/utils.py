import csv
import os
from datetime import date, datetime
from pathlib import Path
from typing import List

# ==============================
# CONFIG
# ==============================
DATA_DIR = Path.home() / ".vault"
VAULTS_FILE = DATA_DIR / "vaults.csv"
TRANSACTIONS_FILE = DATA_DIR / "transactions.csv"
RATES_FILE = DATA_DIR / "rates.csv"
POSTINGS_FILE = DATA_DIR / "posting.csv"

START_DATE = "2026-04-01"


# ==============================
# INIT HELPERS
# ==============================
def ensure_data_directory():
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)


def ensure_vaults_file():
    if not os.path.exists(VAULTS_FILE):
        with open(VAULTS_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["name"])


def ensure_transactions_file():
    if not os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["vault", "date", "amount"])


def ensure_rates_file():
    if not os.path.exists(RATES_FILE):
        with open(RATES_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["start", "end", "apy"])


def ensure_postings_file():
    if not os.path.exists(POSTINGS_FILE):
        with open(POSTINGS_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["original", "posted"])
            # You will add:
            # 2026-04-21,2026-04-23
            # 2026-04-22,2026-04-24


def ensure_all():
    ensure_data_directory()
    ensure_vaults_file()
    ensure_transactions_file()
    ensure_rates_file()
    ensure_postings_file()


def parse_date(s: str) -> date:
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Invalid date format: {s}")


# ==============================
# LOADERS
# ==============================
def load_vaults() -> List[str]:
    ensure_vaults_file()
    vaults: List[str] = []
    with open(VAULTS_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            vaults.append(row["name"])
    return vaults


def save_vaults(vaults: List[str]) -> None:
    with open(VAULTS_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name"])
        for v in vaults:
            writer.writerow([v])


def load_postings():
    ensure_postings_file()
    postings = []
    with open(POSTINGS_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            orig = row["original"].strip()
            posted = row["posted"].strip()
            if orig and posted:
                postings.append(
                    {
                        "initiated": parse_date(orig),
                        "posted": parse_date(posted),
                    }
                )
    return postings


def load_transactions():
    ensure_transactions_file()
    postings = load_postings()
    tx = []

    with open(TRANSACTIONS_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            orig_date_str = row["date"]

            # If posting.csv overrides this date, use the posted date
            if orig_date_str in postings:
                effective_date = parse_date(postings[orig_date_str])
            else:
                effective_date = parse_date(orig_date_str)

            tx.append(
                {
                    "vault": row["vault"],
                    "date": effective_date,
                    "amount": float(row["amount"]),
                }
            )
    return tx


def load_rates():
    ensure_rates_file()
    rates = []
    with open(RATES_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rates.append(
                {
                    "start": parse_date(row["start"]),
                    "end": parse_date(row["end"]) if row["end"] else None,
                    "apy": float(row["apy"]),
                }
            )
    return rates
