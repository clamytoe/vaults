#!/usr/bin/env python3
import typer

from .rates import rates_app
from .statement import vault_statement as statement_cli
from .summary import app as summary_app, summary_cli
from .transactions import transactions_app
from .utils import ensure_all
from .vaults import vaults_app

app = typer.Typer(help="Vaults CLI")

# Attach CLI commands
app.command("summary", help="Show vault summary")(summary_cli)
app.command("statement", help="Show vault statement")(statement_cli)

# Attach sub‑apps
app.add_typer(vaults_app, name="vaults")
app.add_typer(transactions_app, name="transactions")
app.add_typer(rates_app, name="rates")

if __name__ == "__main__":  # pragma: no cover
    ensure_all()
    app()
