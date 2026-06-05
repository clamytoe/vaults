import csv
from datetime import date, timedelta
from typing import Optional

import typer

from vaults.colors import BOLD, CYAN, GREEN, RED, RESET, YELLOW
from vaults.utils import (
    TRANSACTIONS_FILE,
    ensure_all,
    load_transactions,
    load_vaults,
    parse_date,
)

transactions_app = typer.Typer(help="Manage transactions.")


# ==============================
# TRANSACTION COMMANDS
# ==============================
@transactions_app.command("add")
def transactions_add():
    ensure_all()
    vaults = load_vaults()
    if not vaults:
        typer.echo("No vaults defined. Add vaults first.")
        raise typer.Exit()

    typer.echo("\nTransaction Entry Mode")
    typer.echo("Add deposits to vaults. Leave selection blank to finish.\n")

    for idx, v in enumerate(vaults, start=1):
        typer.echo(f"{idx}: {v}")
    typer.echo("")

    while True:
        choice = typer.prompt("Which vault? (# or blank to finish)", default="").strip()
        if choice == "":
            break

        if not choice.isdigit() or not (1 <= int(choice) <= len(vaults)):
            typer.echo("Invalid selection.\n")
            continue

        vault = vaults[int(choice) - 1]

        current_balance = get_vault_balance(vault)
        typer.echo(
            f"Current balance for {vault}: [{CYAN}${current_balance:,.2f}{RESET}]"
        )

        date_str = typer.prompt(
            "Deposit date (YYYY-MM-DD, blank = today)", default=""
        ).strip()
        if date_str == "":
            date_str = date.today().strftime("%Y-%m-%d")

        amount_str = typer.prompt("Deposit amount").strip()
        amount = float(amount_str)

        new_balance = current_balance + amount

        if amount < 0 and new_balance < 0:
            typer.echo(
                f"❌ {RED}Transaction denied: this would overdraw the {vault} vault.{RESET}"
            )
            typer.echo(f"Current balance: {YELLOW}${current_balance:,.2f}{RESET}")
            raise typer.Exit()

        typer.echo(
            f"New balance after this transaction: [{CYAN}${new_balance:,.2f}{RESET}]"
        )

        with open(TRANSACTIONS_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([vault, date_str, amount])

        if amount >= 0:
            typer.echo(f"Added [{color_amount(amount)}] to {vault} on {date_str}.\n")
        else:
            typer.echo(
                f"Withdrew [{color_amount(amount)}] from {vault} on {date_str}.\n"
            )


@transactions_app.command("list")
def transactions_list(
    vault: Optional[str] = typer.Argument(None),
    month: Optional[str] = typer.Option(
        None, "--month", help="Filter by month YYYY-MM"
    ),
    since: Optional[str] = typer.Option(None, "--since", help="Start date YYYY-MM-DD"),
    until: Optional[str] = typer.Option(None, "--until", help="End date YYYY-MM-DD"),
    group_by_vault: bool = typer.Option(
        False, "--group-by-vault", help="Group transactions by vault"
    ),
    group_by_month: bool = typer.Option(
        False, "--group-by-month", help="Group transactions by month"
    ),
    csv_export: Optional[str] = typer.Option(
        None, "--csv", help="Export transactions to CSV file"
    ),
):
    ensure_all()
    tx = load_transactions()

    if not tx:
        typer.echo("No transactions recorded yet.")
        raise typer.Exit()

    # Vault filter
    if vault:
        tx = [t for t in tx if t["vault"].lower() == vault.lower()]
        if not tx:
            typer.echo(f"No transactions found for vault '{vault}'.")
            raise typer.Exit()

    # Month filter
    if month:
        year, mon = map(int, month.split("-"))
        start_date = date(year, mon, 1)
        if mon == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, mon + 1, 1) - timedelta(days=1)

        tx = [t for t in tx if start_date <= t["date"] <= end_date]

    # Since filter
    if since:
        since_date = parse_date(since)
        tx = [t for t in tx if t["date"] >= since_date]

    # Until filter
    if until:
        until_date = parse_date(until)
        tx = [t for t in tx if t["date"] <= until_date]

    # Sort by date
    tx.sort(key=lambda t: t["date"])

    # GROUP BY VAULT MODE
    if group_by_vault:
        typer.echo(f"\n{BOLD}Transactions Grouped by Vault:{RESET}\n")

        # Build groups
        groups = {}
        for t in tx:
            groups.setdefault(t["vault"], []).append(t)

        grand_deposits = 0.0
        grand_withdrawals = 0.0

        for vname, items in groups.items():
            typer.echo(f"{BOLD}{CYAN}{vname}{RESET}")
            typer.echo(f"{BOLD}{'Date':<12}  {'Amount':>12}{RESET}")
            typer.echo("-" * 30)

            deposits = 0.0
            withdrawals = 0.0

            for t in items:
                date_str = f"{t['date']}"
                amt = t["amount"]

                if amt >= 0:
                    amt_str = f"{GREEN}+${amt:,.2f}{RESET}"
                    deposits += amt
                else:
                    amt_str = f"{RED}-${abs(amt):,.2f}{RESET}"
                    withdrawals += abs(amt)

                typer.echo(f"{date_str:<12}  {amt_str:>12}")

            net = deposits - withdrawals
            net_color = GREEN if net >= 0 else RED

            typer.echo("-" * 30)
            typer.echo(f"  Deposits:    {GREEN}${deposits:,.2f}{RESET}")
            typer.echo(f"  Withdrawals: {RED}-${withdrawals:,.2f}{RESET}")
            typer.echo(f"  Net Change:  {net_color}${net:,.2f}{RESET}\n")

            grand_deposits += deposits
            grand_withdrawals += withdrawals

        # Grand totals
        typer.echo(f"{BOLD}GRAND TOTALS:{RESET}")
        net = grand_deposits - grand_withdrawals
        net_color = GREEN if net >= 0 else RED

        typer.echo(f"  Deposits:    {GREEN}${grand_deposits:,.2f}{RESET}")
        typer.echo(f"  Withdrawals: {RED}-${grand_withdrawals:,.2f}{RESET}")
        typer.echo(f"  Net Change:  {net_color}${net:,.2f}{RESET}\n")

        # CSV export still works
        if csv_export:
            with open(csv_export, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["date", "vault", "amount"])
                for t in tx:
                    writer.writerow([t["date"].isoformat(), t["vault"], t["amount"]])

            typer.echo(
                f"{GREEN}Exported {len(tx)} transactions to {csv_export}{RESET}\n"
            )

        return

    # GROUP BY MONTH MODE
    if group_by_month:
        typer.echo(f"\n{BOLD}Transactions Grouped by Month:{RESET}\n")

        # Build groups: { "2026-05": [tx, tx, ...], ... }
        groups = {}
        for t in tx:
            key = f"{t['date'].year}-{t['date'].month:02d}"
            groups.setdefault(key, []).append(t)

        grand_deposits = 0.0
        grand_withdrawals = 0.0

        for month_key, items in sorted(groups.items()):
            typer.echo(f"{BOLD}{CYAN}{month_key}{RESET}")
            typer.echo(f"{BOLD}{'Date':<12}  {'Vault':<20}  {'Amount':>12}{RESET}")
            typer.echo("-" * 48)

            deposits = 0.0
            withdrawals = 0.0

            for t in items:
                date_str = f"{t['date']}"
                vault_str = t["vault"]
                amt = t["amount"]

                if amt >= 0:
                    amt_str = f"{GREEN}+${amt:,.2f}{RESET}"
                    deposits += amt
                else:
                    amt_str = f"{RED}-${abs(amt):,.2f}{RESET}"
                    withdrawals += abs(amt)

                typer.echo(
                    f"{date_str:<12}  {CYAN}{vault_str:<20}{RESET}  {amt_str:>12}"
                )

            net = deposits - withdrawals
            net_color = GREEN if net >= 0 else RED

            typer.echo("-" * 48)
            typer.echo(f"  Deposits:    {GREEN}${deposits:,.2f}{RESET}")
            typer.echo(f"  Withdrawals: {RED}-${withdrawals:,.2f}{RESET}")
            typer.echo(f"  Net Change:  {net_color}${net:,.2f}{RESET}\n")

            grand_deposits += deposits
            grand_withdrawals += withdrawals

        # Grand totals
        typer.echo(f"{BOLD}GRAND TOTALS:{RESET}")
        net = grand_deposits - grand_withdrawals
        net_color = GREEN if net >= 0 else RED

        typer.echo(f"  Deposits:    {GREEN}${grand_deposits:,.2f}{RESET}")
        typer.echo(f"  Withdrawals: {RED}-${grand_withdrawals:,.2f}{RESET}")
        typer.echo(f"  Net Change:  {net_color}${net:,.2f}{RESET}\n")

        # CSV export still works
        if csv_export:
            with open(csv_export, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["date", "vault", "amount"])
                for t in tx:
                    writer.writerow([t["date"].isoformat(), t["vault"], t["amount"]])

            typer.echo(
                f"{GREEN}Exported {len(tx)} transactions to {csv_export}{RESET}\n"
            )

        return

    # Table header
    typer.echo(f"\n{BOLD}Transactions:{RESET}")
    typer.echo(f"{BOLD}{'Date':<12}  {'Vault':<20}  {'Amount':>12}{RESET}")
    typer.echo("-" * 48)

    total_deposits = 0.0
    total_withdrawals = 0.0

    # Table rows
    for t in tx:
        date_str = f"{t['date']}"
        vault_str = t["vault"]

        amount = t["amount"]
        if amount >= 0:
            amount_str = f"{GREEN}+${amount:,.2f}{RESET}"
            total_deposits += amount
        else:
            amount_str = f"{RED}-${abs(amount):,.2f}{RESET}"
            total_withdrawals += abs(amount)

        typer.echo(f"{date_str:<12}  {CYAN}{vault_str:<20}{RESET}  {amount_str:>12}")

    typer.echo("-" * 48)

    # Totals
    net = total_deposits - total_withdrawals
    net_color = GREEN if net >= 0 else RED

    typer.echo(f"{BOLD}Totals:{RESET}")
    typer.echo(f"  Deposits:    {GREEN}${total_deposits:,.2f}{RESET}")
    typer.echo(f"  Withdrawals: {RED}-${total_withdrawals:,.2f}{RESET}")
    typer.echo(f"  Net Change:  {net_color}${net:,.2f}{RESET}\n")

    # CSV export
    if csv_export:
        with open(csv_export, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "vault", "amount"])
            for t in tx:
                writer.writerow([t["date"].isoformat(), t["vault"], t["amount"]])

        typer.echo(f"{GREEN}Exported {len(tx)} transactions to {csv_export}{RESET}\n")


@transactions_app.command("stats")
def transactions_stats(
    vault: Optional[str] = typer.Argument(None),
    month: Optional[str] = typer.Option(
        None, "--month", help="Filter by month YYYY-MM"
    ),
    since: Optional[str] = typer.Option(None, "--since", help="Start date YYYY-MM-DD"),
    until: Optional[str] = typer.Option(None, "--until", help="End date YYYY-MM-DD"),
):
    ensure_all()
    tx = load_transactions()

    if not tx:
        typer.echo("No transactions recorded yet.")
        raise typer.Exit()

    # Vault filter
    if vault:
        tx = [t for t in tx if t["vault"].lower() == vault.lower()]

    # Month filter
    if month:
        year, mon = map(int, month.split("-"))
        start_date = date(year, mon, 1)
        if mon == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, mon + 1, 1) - timedelta(days=1)
        tx = [t for t in tx if start_date <= t["date"] <= end_date]

    # Since filter
    if since:
        since_date = parse_date(since)
        tx = [t for t in tx if t["date"] >= since_date]

    # Until filter
    if until:
        until_date = parse_date(until)
        tx = [t for t in tx if t["date"] <= until_date]

    if not tx:
        typer.echo("No transactions match the selected filters.")
        raise typer.Exit()

    # Sort for date-based stats
    tx.sort(key=lambda t: t["date"])

    deposits = [t["amount"] for t in tx if t["amount"] > 0]
    withdrawals = [abs(t["amount"]) for t in tx if t["amount"] < 0]

    total_deposits = sum(deposits)
    total_withdrawals = sum(withdrawals)
    net = total_deposits - total_withdrawals

    # Colors
    net_color = GREEN if net >= 0 else RED

    typer.echo(f"\n{BOLD}Transaction Stats:{RESET}")
    typer.echo("-" * 40)

    # Totals
    typer.echo(f"{BOLD}Totals:{RESET}")
    typer.echo(f"  Deposits:       {GREEN}${total_deposits:,.2f}{RESET}")
    typer.echo(f"  Withdrawals:    {RED}-${total_withdrawals:,.2f}{RESET}")
    typer.echo(f"  Net Change:     {net_color}${net:,.2f}{RESET}\n")

    # Counts
    typer.echo(f"{BOLD}Counts:{RESET}")
    typer.echo(f"  Total Tx:       {len(tx)}")
    typer.echo(f"  Deposits:       {len(deposits)}")
    typer.echo(f"  Withdrawals:    {len(withdrawals)}\n")

    # Averages
    typer.echo(f"{BOLD}Averages:{RESET}")
    typer.echo(
        f"  Avg Deposit:    {GREEN}${(sum(deposits)/len(deposits)) if deposits else 0:,.2f}{RESET}"
    )
    typer.echo(
        f"  Avg Withdrawal: {RED}-${(sum(withdrawals)/len(withdrawals)) if withdrawals else 0:,.2f}{RESET}\n"
    )

    # Extremes
    typer.echo(f"{BOLD}Extremes:{RESET}")
    if deposits:
        typer.echo(f"  Largest Deposit:    {GREEN}${max(deposits):,.2f}{RESET}")
    else:
        typer.echo("  Largest Deposit:    None")

    if withdrawals:
        typer.echo(f"  Largest Withdrawal: {RED}-${max(withdrawals):,.2f}{RESET}")
    else:
        typer.echo("  Largest Withdrawal: None")

    typer.echo("")

    # Dates
    typer.echo(f"{BOLD}Date Range:{RESET}")
    typer.echo(f"  First Tx:       {tx[0]['date']}")
    typer.echo(f"  Most Recent Tx: {tx[-1]['date']}\n")


def color_amount(amount: float) -> str:
    if amount >= 0:
        color = "green"
    else:
        color = "red"
        amount = abs(amount)
    return typer.style(f"${amount:,.2f}", fg=color)


def get_vault_balance(vault_name: str) -> float:
    transactions = load_transactions()
    balance = 0.0

    for tx in transactions:
        # Skip malformed entries just in case
        if not tx or "vault" not in tx or "amount" not in tx:
            continue

        if tx["vault"] == vault_name:
            balance += float(tx["amount"])

    return balance
