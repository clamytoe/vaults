from datetime import timedelta


def build_daily_apy(rates, start_date, end_date):
    daily_apy = {}
    for r in rates:
        d = r["start"]
        period_end = r["end"] or end_date
        while d <= period_end and d <= end_date:
            daily_apy[d] = r["apy"]
            d += timedelta(days=1)
    return daily_apy


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


# ==============================
# INTEREST ENGINE
# ==============================
def calculate_interest(vaults, transactions, rates, end_date):
    if transactions:
        start_date = min(t["date"] for t in transactions)
    else:
        start_date = parse_date(START_DATE)

    daily_balances = get_daily_balances(vaults, transactions, start_date, end_date)
    daily_interest = get_daily_interest(daily_balances, rates, start_date, end_date)

    # Sum interest per vault
    interest_totals = {v: sum(daily_interest[v].values()) for v in vaults}
    return interest_totals
