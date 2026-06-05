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


def currency(value: float) -> str:
    sign = ""
    if value > 0:
        color = "green"
        sign = "+"
    elif value < 0:
        color = "red"
        sign = "-"
    else:
        color = "white"
    return typer.style(f"{sign}${abs(value):,.2f}", fg=color, bold=True)


def bold(text: str) -> str:
    return typer.style(text, bold=True)


def error(text: str) -> str:
    return typer.style(text, fg="red")


def label(text: str, bold: bool = False) -> str:
    return typer.style(text, fg="cyan", bold=bold)


def warning(text: str) -> str:
    return typer.style(text, fg="yellow")


def success(text: str) -> str:
    return typer.style(text, fg="green")
