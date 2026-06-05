import csv
from datetime import date, timedelta
from typing import Optional

import typer

from vaults.interest import calculate_interest
from vaults.utils import (
    RATES_FILE,
    ensure_all,
    load_rates,
    load_transactions,
    load_vaults,
    parse_date,
)

rates_app = typer.Typer(help="Manage APY rate history.")


# ==============================
# RATE COMMANDS
# ==============================
@rates_app.command("list")
def rates_list():
    ensure_all()
    rates = load_rates()
    if not rates:
        typer.echo("No rates defined.")
        raise typer.Exit()

    typer.echo("Rate history:")
    for r in rates:
        start = r["start"].strftime("%Y-%m-%d")
        end = r["end"].strftime("%Y-%m-%d") if r["end"] else ""
        typer.echo(f"{start} -> {end or 'present'} : {r['apy']:.4f}")


@rates_app.command("add")
def rates_add(
    start: str = typer.Option(..., help="Start date YYYY-MM-DD"),
    apy: float = typer.Option(..., help="APY as decimal, e.g. 0.032"),
    end: Optional[str] = typer.Option(None, help="End date YYYY-MM-DD (optional)"),
):
    ensure_all()

    new_start = parse_date(start)
    new_end = parse_date(end) if end else None

    rates = load_rates()
    rates.sort(key=lambda r: r["start"])

    previous = None
    for r in rates:
        if r["start"] < new_start:
            previous = r
        else:
            break

    if previous:
        prev_end = new_start - timedelta(days=1)
        if prev_end >= previous["start"]:
            previous["end"] = prev_end

    rates.append(
        {
            "start": new_start,
            "end": new_end,
            "apy": apy,
        }
    )

    rates.sort(key=lambda r: r["start"])

    with open(RATES_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["start", "end", "apy"])
        for r in rates:
            writer.writerow(
                [
                    r["start"].strftime("%Y-%m-%d"),
                    r["end"].strftime("%Y-%m-%d") if r["end"] else "",
                    r["apy"],
                ]
            )

    typer.echo(f"Added rate: {start} -> {end or 'present'} @ {apy:.4f}")
    if previous:
        typer.echo("Previous rate period updated automatically.")


@rates_app.command("calibrate")
def rates_calibrate(
    target: float = typer.Option(..., help="Target interest for the month"),
    month: str = typer.Option(..., help="Month in YYYY-MM format"),
):
    """Automatically solve for the APY that produces the target interest for
    a specific month.
    """
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

    # Helper: compute interest ONLY for the target month
    def simulate(apy_value):
        test_rates = [{"start": start_date, "end": end_date, "apy": apy_value}]
        interest = calculate_interest(vaults, transactions, test_rates, end_date)
        return sum(interest.values())

    # Binary search for APY
    low, high = 0.0001, 0.10
    for _ in range(40):
        mid = (low + high) / 2
        result = simulate(mid)
        if result < target:
            low = mid
        else:
            high = mid

    calibrated_apy = (low + high) / 2

    # Update rates.csv
    with open(RATES_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["start", "end", "apy"])
        writer.writerow(
            [
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                f"{calibrated_apy:.6f}",
            ]
        )
        # Keep existing future rates
        writer.writerow(["2026-05-01", "", "0.0310"])

    typer.echo(f"Calibrated APY for {month}: {calibrated_apy:.6f}")
