import datetime
from datetime import date, timedelta

from vaults.utils import parse_date


def build_daily_apy(rates, start_date, end_date):
    daily_apy = {}
    for r in rates:
        d = r["start"]
        period_end = r["end"] or end_date
        while d <= period_end and d <= end_date:
            daily_apy[d] = r["apy"]
            d += timedelta(days=1)
    return daily_apy


# ==============================
# INTEREST ENGINE
# ==============================
def calculate_interest(vaults, transactions, rates, end_date: date):
    """
    Calculate interest for each vault up to end_date.
    vaults: dict of vault_name -> starting_balance
    transactions: list of {vault, date, amount}
    rates: list of {start, end, apy}
    """
    # Build daily balances per vault
    daily_balances = {v: {} for v in vaults}

    # Determine earliest date
    all_dates = []
    for tx in transactions:
        all_dates.append(tx["date"])
    for r in rates:
        all_dates.append(r["start"])
        if r["end"]:
            all_dates.append(r["end"])

    if not all_dates:
        return {v: 0.0 for v in vaults}

    start_date = min(all_dates)

    # Build daily balance timeline
    current_balances = {v: vaults[v] for v in vaults}

    current_date = start_date
    while current_date <= end_date:
        # Apply transactions for the day
        for tx in transactions:
            if tx["date"] == current_date:
                current_balances[tx["vault"]] += tx["amount"]

        # Store balances
        for v in vaults:
            daily_balances[v][current_date] = current_balances[v]

        current_date += timedelta(days=1)

    # Compute interest
    interest_totals = {v: 0.0 for v in vaults}

    for r in rates:
        rate_start = r["start"]
        rate_end = r["end"] or end_date
        apy = r["apy"]

        current_date = rate_start
        while current_date <= rate_end and current_date <= end_date:
            for v in vaults:
                bal = daily_balances[v].get(current_date, 0)
                interest_totals[v] += daily_interest(bal, apy)
            current_date += timedelta(days=1)

    return interest_totals


def daily_interest(principal: float, apy: float) -> float:
    """Compute daily interest from APY."""
    if principal == 0 or apy == 0:
        return 0.0
    return principal * apy / 365.0


def get_daily_interest(daily_balances, rates, start_date, end_date):
    daily_apy = build_daily_apy(rates, start_date, end_date)
    daily_interest = {v: {} for v in daily_balances}

    current = start_date
    while current <= end_date:
        apy = daily_apy[current]
        dpr = apy / 365

        for v in daily_balances:
            bal = daily_balances[v][current]
            di = round(bal * dpr, 2)
            daily_interest[v][current] = di

        current += timedelta(days=1)

    return daily_interest
