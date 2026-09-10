from typer.testing import CliRunner
from vaults.cli import app

runner = CliRunner()


def test_cli_root_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "vaults" in result.output
    assert "transactions" in result.output
    assert "rates" in result.output
    assert "statement" in result.output
    assert "summary" in result.output


def test_cli_vaults_help():
    result = runner.invoke(app, ["vaults", "--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_cli_transactions_help():
    result = runner.invoke(app, ["transactions", "--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_cli_rates_help():
    result = runner.invoke(app, ["rates", "--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_cli_statement_help():
    result = runner.invoke(app, ["statement", "--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_cli_summary_help():
    result = runner.invoke(app, ["summary", "--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output
