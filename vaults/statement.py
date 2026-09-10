from datetime import date, timedelta
from os import environ
from typing import Optional

import typer
from dotenv import load_dotenv

from vaults.balances import get_daily_balances
from vaults.colors import BLUE, BOLD, CYAN, GREEN, RED, RESET
from vaults.interest import get_daily_interest
from vaults.summary import summarize_month
from vaults.utils import (
    ensure_all,
    load_postings,
    load_rates,
    load_transactions,
    load_vaults,
    parse_date,
)

load_dotenv()


# ==============================
# STATEMENT COMMANDS
# ==============================
def vault_statement(
    month: str = typer.Option(..., help="Month in YYYY-MM format"),
    daily: bool = typer.Option(False, help="Include daily interest table"),
    vault: Optional[str] = typer.Option(None, help="Filter to a single vault"),
):
    ensure_all()

    # Parse month boundaries
    year, mon = map(int, month.split("-"))
    start_date = date(year, mon, 1)
    if mon == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, mon + 1, 1) - timedelta(days=1)

    vaults = load_vaults()
    transactions = load_transactions()
    rates = load_rates()
    postings = load_postings()

    # Filter vaults if requested
    if vault:
        vaults = [v for v in vaults if v == vault]

    # Compute balances and interest using shared engines
    daily_balances = get_daily_balances(vaults, transactions, start_date, end_date)
    daily_interest = get_daily_interest(daily_balances, rates, start_date, end_date)
    summary_data = summarize_month(
        daily_balances, daily_interest, transactions, vaults, start_date, end_date
    )

    # Print header
    bar = "-" * 83
    bank_name = environ.get("BANK_NAME", "BANK")
    title = f"{bank_name}: VAULT STATEMENT"
    date_range = f"{start_date:%B 1} - {end_date:%B %d, %Y}"
    typer.echo(f"{BOLD}{bar}{RESET}")
    typer.echo(f"{BOLD}{title.center(83)}{RESET}")
    typer.echo(f"{BOLD}{date_range.center(83)}{RESET}")
    typer.echo(f"{BOLD}{bar}{RESET}\n")

    # Determine APY in effect during the statement period
    apy_in_effect = None
    for r in rates:
        r_start = r["start"]
        r_end   = r["end"] or end_date

        # Check if rate period overlaps the statement period
        if r_start <= end_date and r_end >= start_date:
            apy_in_effect = r["apy"]
            break

    apy = apy_in_effect * 100 if apy_in_effect is not None else 0

    typer.echo(f"        APY in effect: {CYAN}{apy:.4f}%{RESET}")

    total_interest = sum(s["interest"] for s in summary_data.values())
    typer.echo(f"Total Interest Earned: {GREEN}${total_interest:,.2f}{RESET}")

    starting_total = sum(s["start"] for s in summary_data.values())
    ending_total = sum(s["end"] for s in summary_data.values())
    typer.echo(f"     Starting Balance: {BLUE}${starting_total:,.2f}{RESET}")
    typer.echo(f"       Ending Balance: {BLUE}${ending_total:,.2f}{RESET}\n")

    COL_VAULT = 15
    COL_MONEY = 12

    header = (
        f"{'Vault':<{COL_VAULT}}"
        f"{'Start':>{COL_MONEY}}  "
        f"{'Deposits':>{COL_MONEY}}  "
        f"{'Withdrawals':>{COL_MONEY}}  "
        f"{'Interest':>{COL_MONEY}}  "
        f"{'End':>{COL_MONEY}}"
    )
    typer.echo(header)
    typer.echo(bar)

    for v, s in summary_data.items():
        typer.echo(
            f"{v:<{COL_VAULT}}"
            f"{BLUE}${s['start']:>{COL_MONEY - 1},.2f}{RESET}  "
            f"{CYAN}${s['deposits']:>{COL_MONEY - 1},.2f}{RESET}  "
            f"{RED}${s['withdrawals']:>{COL_MONEY - 1},.2f}{RESET}  "
            f"{GREEN}${s['interest']:>{COL_MONEY - 1},.2f}{RESET}  "
            f"{BOLD}${s['end']:>{COL_MONEY - 1},.2f}{RESET}"
        )

    typer.echo(bar)

    typer.echo(
        f"{BOLD}{'TOTALS':<{COL_VAULT}}{RESET}"
        f"{BLUE}${starting_total:>{COL_MONEY - 1},.2f}{RESET}  "
        f"{CYAN}${sum(s['deposits'] for s in summary_data.values()):>{COL_MONEY - 1},.2f}{RESET}  "
        f"{RED}${sum(s['withdrawals'] for s in summary_data.values()):>{COL_MONEY - 1},.2f}{RESET}  "
        f"{GREEN}${total_interest:>{COL_MONEY - 1},.2f}{RESET}  "
        f"{BOLD}${ending_total:>{COL_MONEY - 1},.2f}{RESET}"
    )
    typer.echo("")

    # Posting delays
    typer.echo("POSTING DELAYS")
    typer.echo(bar)
    for orig_str, posted_date in postings.items():
        initiated_date = parse_date(orig_str)
        if start_date <= posted_date <= end_date:
            typer.echo(f"{initiated_date} → posted {posted_date}")
    typer.echo("")

    # Optional daily table
    if daily:
        typer.echo("DAILY INTEREST DETAIL")
        typer.echo(bar + "\n")

        COL_DATE = 10
        COL_VAULT = 15
        COL_MONEY = 10
        COL_APY = 5

        daily_header = (
            f"{'Date':<{COL_DATE}}  "
            f"{'Vault':<{COL_VAULT}}"
            f"{'Balance':>{COL_MONEY}}  "
            f"{'APY':>{COL_APY}}  "
            f"{'Interest':>{COL_MONEY}}  "
        )
        typer.echo(daily_header)
        typer.echo(bar)

        # APY for each day
        for v in vaults:
            for d in sorted(daily_balances[v]):
                bal = daily_balances[v][d]

                # Find rate active on day d
                day_apy = None
                for r in rates:
                    r_start = r["start"]
                    r_end   = r["end"] or end_date
                    if r_start <= d <= r_end:
                        day_apy = r["apy"]
                        break

                apy = day_apy * 100 if day_apy is not None else 0
                di = daily_interest[v][d]

                typer.echo(
                    f"{d}   {v:<{COL_VAULT}}  ${bal:>{COL_MONEY},.2f}   {apy:>{COL_APY}.2f}%   ${di:>{COL_MONEY}.2f}"
                )

        typer.echo(bar)
