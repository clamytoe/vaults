import typer

# ==============================
# COLORS
# ==============================
BLUE = "\033[94m"
GREEN = "\033[92m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"
YELLOW = "\033[93m"
RED = "\033[91m"


def currency(value: float) -> str:  # pragma: no cover
    sign = ""
    if value > 0:
        color = "green"
        sign = "+"
    elif value < 0:
        color = "red"
        sign = "-"
    else:
        color = "white"
    return typer.style(f"{sign}${abs(value):>11,.2f}", fg=color, bold=True)


def bold(text: str) -> str:  # pragma: no cover
    return typer.style(text, bold=True)


def error(text: str) -> str:  # pragma: no cover
    return typer.style(text, fg="red")


def label(text: str, bold: bool = False) -> str:  # pragma: no cover
    return typer.style(text, fg="cyan", bold=bold)


def warning(text: str) -> str:  # pragma: no cover
    return typer.style(text, fg="yellow")


def success(text: str) -> str:  # pragma: no cover
    return typer.style(text, fg="green")
