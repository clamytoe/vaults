#!/usr/bin/env python3
import typer

from .rates import rates_app
from .statement import vault_statement as statement
from .summary import summary
from .transactions import transactions_app
from .utils import ensure_all
from .vaults import vaults_app

app = typer.Typer(help="Vaults CLI")

app.command("summary", help="Show vault summary")(summary)
app.command("statement", help="Show vault statement")(statement)

app.add_typer(vaults_app, name="vaults")
app.add_typer(transactions_app, name="transactions")
app.add_typer(rates_app, name="rates")


if __name__ == "__main__":
    ensure_all()
    app()
