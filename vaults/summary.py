from datetime import date, datetime
from typing import Optional

import calendar
import typer

from vaults.balances import get_daily_balances
from vaults.colors import BLUE, BOLD, CYAN, GREEN, RESET
from vaults.interest import get_daily_interest
from vaults.utils import (
    START_DATE,
    ensure_all,
    load_rates,
    load_transactions,
    load_vaults,
    parse_date,
)


# ==============================
# SUMMARY COMMAND
# ==============================
def summary(
    end: Optional[str] = typer.Option(None, help="End date YYYY-MM-DD"),
):
    ensure_all()

    vaults = load_vaults()
    if not vaults:
        typer.echo("No vaults defined.")
        raise typer.Exit()

    rates = load_rates()
    if not rates:
        typer.echo("No APY rates defined. Use `vault rates add` to create one.")
        raise typer.Exit()

    transactions = load_transactions()
    last_transaction_date = max(t["date"] for t in transactions)

    if end:
        end_date = normalize_end_date(end)
    else:
        end_date = date.today()

    # Ensure end date is not after the last transaction date
    if end_date > last_transaction_date:
        end_date = last_transaction_date

    # Determine start date from transactions
    if transactions:
        start_date = min(t["date"] for t in transactions)
    else:
        start_date = parse_date(START_DATE)

    daily_balances = get_daily_balances(vaults, transactions, start_date, end_date)
    daily_interest = get_daily_interest(daily_balances, rates, start_date, end_date)
    summary_data = summarize_month(
        daily_balances, daily_interest, transactions, vaults, start_date, end_date
    )

    print_summary(summary_data, end_date)


def summarize_month(
    daily_balances, daily_interest, transactions, vaults, start_date, end_date
):
    summary = {}

    tx_by_vault = {v: [] for v in vaults}
    for t in transactions:
        if t["vault"] in tx_by_vault:
            tx_by_vault[t["vault"]].append(t)

    try:
        for v in vaults:
            start = daily_balances[v][start_date]
            end = daily_balances[v][end_date]
            deposits = sum(
                t["amount"]
                for t in tx_by_vault[v]
                if t["amount"] > 0 and start_date <= t["date"] <= end_date
            )
            withdrawals = sum(
                -t["amount"]
                for t in tx_by_vault[v]
                if t["amount"] < 0 and start_date <= t["date"] <= end_date
            )
            interest = sum(daily_interest[v].values())

            summary[v] = {
                "start": start,
                "end": end,
                "deposits": deposits,
                "withdrawals": withdrawals,
                "interest": interest,
            }
    except KeyError as e:
        typer.echo(f"Error: There is no data before {e.args[0]}.")
        raise typer.Exit()

    return summary


# ==============================
# SUMMARY
# ==============================
def print_summary(summary_data, end_date):
    print("\nVault Summary", f"{end_date.isoformat():>47}")
    print("-------------------------------------------------------------")
    print(
        f"{BOLD}{'Vault Name':<15} {'Principal':>12} {'Interest':>12} {'Total':>12}{RESET}"
    )
    print("-------------------------------------------------------------")

    grand_principal = 0
    grand_interest = 0
    grand_total = 0

    for v, s in summary_data.items():
        principal = s["deposits"] - s["withdrawals"]
        interest = s["interest"]
        if v == "Interest":
            interest = 0
        total = principal + interest

        grand_principal += principal
        grand_interest += interest
        grand_total += total

        print(
            f"{CYAN}{v:<15}{RESET} "
            f"{BLUE}${principal:>11,.2f}{RESET} "
            f"{GREEN}${interest:>11,.2f}{RESET} "
            f"{BOLD}${total:>11,.2f}{RESET}"
        )

    print("-------------------------------------------------------------")
    print(
        f"{BOLD}{'GRAND TOTAL':<15}{RESET} "
        f"{BLUE}${grand_principal:>11,.2f}{RESET} "
        f"{GREEN}${grand_interest:>11,.2f}{RESET} "
        f"{BOLD}${grand_total:>11,.2f}{RESET}"
    )
    print("-------------------------------------------------------------\n")


# ==============================
# NORMALIZE END DATE
# ==============================
def normalize_end_date(end_str):
    """
    Accepts either YYYY-MM-DD or YYYY-MM.
    Returns a datetime.date representing the final day of that period.
    """
    try:
        # Case 1: full date YYYY-MM-DD
        return datetime.strptime(end_str, "%Y-%m-%d").date()
    except ValueError:
        pass

    try:
        # Case 2: year-month YYYY-MM → convert to last day of month
        year, month = map(int, end_str.split("-"))
        last_day = calendar.monthrange(year, month)[1]
        return datetime(year, month, last_day).date()
    except Exception:
        raise ValueError(f"Invalid --end value: {end_str}")
