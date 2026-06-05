from datetime import timedelta


def compute_starting_balance(tx_list, start_date):
    bal = 0
    for t in tx_list:
        if t["date"] < start_date:
            bal += t["amount"]
    return bal


def get_daily_balances(vaults, transactions, start_date, end_date):
    # group transactions by vault
    tx_by_vault = {v: [] for v in vaults}
    for t in transactions:
        if t["vault"] in tx_by_vault:
            tx_by_vault[t["vault"]].append(t)

    for v in vaults:
        tx_by_vault[v].sort(key=lambda x: x["date"])

    # build daily balances
    daily = {v: {} for v in vaults}

    current = start_date
    while current <= end_date:
        for v in vaults:
            if current == start_date:
                bal = compute_starting_balance(tx_by_vault[v], start_date)
            else:
                bal = daily[v][current - timedelta(days=1)]

            for t in tx_by_vault[v]:
                if t["date"] == current:
                    bal += t["amount"]

            daily[v][current] = bal

        current += timedelta(days=1)

    return daily
