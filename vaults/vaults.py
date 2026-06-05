import typer

from vaults.utils import ensure_all, load_vaults, save_vaults

vaults_app = typer.Typer(help="Manage vaults.")


# ==============================
# VAULT COMMANDS
# ==============================
@vaults_app.command("list")
def vaults_list():
    ensure_all()
    vaults = load_vaults()
    if not vaults:
        typer.echo("No vaults defined yet.")
        raise typer.Exit()
    typer.echo("Vaults:")
    for idx, v in enumerate(vaults, start=1):
        typer.echo(f"{idx}: {v}")


@vaults_app.command("add")
def vaults_add():
    ensure_all()
    vaults = load_vaults()
    typer.echo("\nVault Setup Mode (blank name to finish)\n")
    while True:
        name = typer.prompt("Vault name", default="").strip()
        if name == "":
            break
        if name in vaults:
            typer.echo("Vault already exists.")
            continue
        vaults.append(name)
    save_vaults(vaults)
    typer.echo(f"\nSaved {len(vaults)} vault(s).\n")
