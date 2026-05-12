import os
import sys
import getpass
import time
from threading import Timer

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import pyperclip
import pyotp

from botpass.core.vault import Vault
from botpass.core.utils import generate_password_diceware, generate_password_random, check_password_strength, check_hibp

console = Console()

# Hardcoded paths that work on my machine (or relative to current dir)
VAULT_PATH = os.path.expanduser("vault.db")
SALT_PATH = os.path.expanduser("salt.bin")
CONFIG_PATH = os.path.expanduser("config.json")

# yeah yeah, singleton pattern. sue me.
_vault_instance = None  

def get_vault():
    global _vault_instance
    if not _vault_instance:
        _vault_instance = Vault(VAULT_PATH, SALT_PATH, CONFIG_PATH)
    return _vault_instance

def clear_clipboard():
    """Clear clipboard after delay."""
    pyperclip.copy("")
    # Don't print here, it messes up the prompt
    
def copy_with_timeout(text: str, timeout: int = 10):
    pyperclip.copy(text)
    console.print(f"[green]Copied to clipboard! Clears in {timeout} seconds...[/green]")
    t = Timer(timeout, clear_clipboard)
    t.daemon = True
    t.start()

def banner():
    console.print("\n[bold]Botpass[/bold] [dim]— Your Local Vault[/dim]\n")

def cmd_setup():
    v = get_vault()
    console.print("[yellow]Looks like this is your first time here.[/yellow]")
    console.print("[bold red]WARNING: If you forget your master password, your data is GONE. No recovery.[/bold red]")
    
    pw1 = getpass.getpass("❯ Enter a strong master password: ")
    pw2 = getpass.getpass("❯ Verify password: ")
    
    if pw1 != pw2:
        console.print("[red][ ERROR ] Passwords don't match. Try again.[/red]")
        return False
        
    try:
        v.setup(pw1)
        console.print("[green]Vault initialized! All your secrets are safe. Probably.[/green]")
        return True
    except Exception as e:
        console.print(f"[red]Error during setup: {e}[/red]")
        return False

def cmd_unlock():
    v = get_vault()
    pw = getpass.getpass("❯ Master Password: ")
    
    if v.unlock(pw):
        console.print("[green]Vault unlocked![/green]")
        return True
    else:
        console.print("[red][ ERROR ] Wrong password. Try again.[/red]")
        return False

def cmd_list():
    v = get_vault()
    try:
        entries = v.list_entries()
        if not entries:
            console.print("[yellow]Vault is empty. Add something![/yellow]")
            return

        from rich.box import MINIMAL
        table = Table(show_header=True, header_style="bold", box=MINIMAL, border_style="dim")
        table.add_column("Domain", style="white bold")
        table.add_column("Username", style="white")
        table.add_column("Tags", style="dim")
        table.add_column("Notes/2FA", style="dim")

        # I find this easier to debug than a one-liner
        for e in entries:
            notes_preview = e.get("notes", "") or ""
            if len(notes_preview) > 30:
                notes_preview = notes_preview[:30] + "..."
            if e.get("totp_secret"):
                notes_preview = "[bold red]2FA[/bold red] " + notes_preview
            table.add_row(e.get("domain", "?"), e.get("username", "?"), e.get("tags", ""), notes_preview)
            
        console.print(table)
    except Exception as e:
        console.print(f"[red]Something broke. Try again? ({e})[/red]")

def cmd_add():
    v = get_vault()
    domain = console.input("[bold dim]❯[/bold dim] [white]Domain/Site:[/white] ")
    username = console.input("[bold dim]❯[/bold dim] [white]Username:[/white] ")
    
    use_gen = console.input("[bold dim]❯[/bold dim] [white]Generate password? (y/n):[/white] ").strip().lower()
    if use_gen == "y":
        password = cmd_generate(return_pw=True)
    else:
        password = getpass.getpass("❯ Password: ")
    
    # Show strength
    strength = check_password_strength(password)
    console.print(f"Password strength: [{_strength_color(strength['score'])}]{strength['label']}[/{_strength_color(strength['score'])}]")
    for fb in strength["feedback"]:
        console.print(f"  → {fb}")
    
    # Check HIBP
    console.print("[dim]Checking against known breaches...[/dim]")
    breach_count = check_hibp(password)
    if breach_count > 0:
        console.print(f"[bold red][ WARNING ] This password appeared in {breach_count:,} data breaches! Consider a different one.[/bold red]")
        proceed = console.input("[yellow]Save anyway? (y/n): [/yellow]").strip().lower()
        if proceed != "y":
            console.print("Cancelled.")
            return
    elif breach_count == 0:
        console.print("[green][ OK ] Not found in any known breaches.[/green]")
    else:
        console.print("[dim]Could not reach breach database. Skipping check.[/dim]")
    
    notes = console.input("[bold dim]❯[/bold dim] [white]Notes (optional):[/white] ").strip()
    tags = console.input("[bold dim]❯[/bold dim] [white]Tags (comma separated, optional):[/white] ").strip()
    totp_secret = console.input("[bold dim]❯[/bold dim] [white]2FA Setup Key (optional):[/white] ").strip()
    
    try:
        v.add(domain, username, password, notes, tags, totp_secret)
        console.print(f"[green]Added {domain} to the vault.[/green]")
    except Exception as e:
        console.print(f"[red]Oops! {e}[/red]")

def cmd_get():
    v = get_vault()
    domain = console.input("[cyan]Domain to retrieve: [/cyan]")
    
    try:
        data = v.get(domain)
        if not data:
            console.print("[red]Not found in vault.[/red]")
            return
            
        console.print(f"[green]Username: [/green] {data.get('username')}")
        if data.get('tags'):
            console.print(f"[blue]Tags: {data.get('tags')}[/blue]")
        if data.get('notes'):
            console.print(f"[dim]Notes: {data.get('notes')}[/dim]")
        if data.get('totp_secret'):
            try:
                totp = pyotp.TOTP(data.get('totp_secret'))
                console.print(f"[bold red]TOTP (2FA): {totp.now()}[/bold red]")
            except Exception:
                console.print("[red]Invalid TOTP secret configured![/red]")
        copy_with_timeout(data.get("password"), 10)
    except Exception as e:
        console.print(f"[red]Something broke. ({e})[/red]")

def cmd_delete():
    v = get_vault()
    domain = console.input("[bold dim]❯[/bold dim] [white]Domain to delete:[/white] ")
    
    try:
        if v.delete(domain):
            console.print(f"[green]Deleted {domain}. It's gone forever.[/green]")
        else:
            console.print("[red]Not found.[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

def cmd_update():
    v = get_vault()
    domain = console.input("[bold dim]❯[/bold dim] [white]Domain to update:[/white] ")
    
    data = v.get(domain)
    if not data:
        console.print("[red]Not found in vault.[/red]")
        return
    
    console.print(f"Current username: {data.get('username')}")
    if data.get('notes'):
        console.print(f"Current notes: {data.get('notes')}")
    if data.get('tags'):
        console.print(f"Current tags: {data.get('tags')}")
    if data.get('totp_secret'):
        console.print(f"Current 2FA Setup Key: {data.get('totp_secret')}")
        
    new_un = console.input("[bold dim]❯[/bold dim] [white]New username (leave blank to keep):[/white] ").strip()
    new_pw_input = console.input("[bold dim]❯[/bold dim] [white]New password? (enter/generate/skip):[/white] ").strip().lower()
    
    new_pw = None
    if new_pw_input == "generate":
        new_pw = cmd_generate(return_pw=True)
    elif new_pw_input == "enter":
        new_pw = getpass.getpass("New password: ")
    
    new_notes = console.input("[bold dim]❯[/bold dim] [white]New notes (leave blank to keep):[/white] ").strip()
    new_tags = console.input("[bold dim]❯[/bold dim] [white]New tags (leave blank to keep):[/white] ").strip()
    new_totp = console.input("[bold dim]❯[/bold dim] [white]New 2FA Setup Key (leave blank to keep):[/white] ").strip()
    
    try:
        v.update_entry(
            domain, 
            new_username=new_un if new_un else None, 
            new_password=new_pw,
            new_notes=new_notes if new_notes else None,
            new_tags=new_tags if new_tags else None,
            new_totp_secret=new_totp if new_totp else None
        )
        console.print(f"[green]Updated {domain}.[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

def cmd_changepw():
    v = get_vault()
    console.print("[yellow]Changing master password will re-encrypt your entire vault.[/yellow]")
    pw1 = getpass.getpass("❯ Enter NEW strong master password: ")
    pw2 = getpass.getpass("❯ Verify NEW password: ")
    
    if pw1 != pw2:
        console.print("[red][ ERROR ] Passwords don't match.[/red]")
        return
        
    try:
        v.change_master_password(pw1)
        console.print("[green]Done. All your secrets are safe with the new password. Probably.[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

def cmd_generate(return_pw=False):
    """Generate a password. If return_pw=True, returns the password instead of copying."""
    style = console.input("[bold dim]❯[/bold dim] [white]Style? (diceware/random):[/white] ").strip().lower()
    
    if style == "diceware" or style == "d":
        pw = generate_password_diceware()
    else:
        pw = generate_password_random()
    
    console.print(f"[green]Generated: [bold]{pw}[/bold][/green]")
    
    strength = check_password_strength(pw)
    console.print(f"Strength: [{_strength_color(strength['score'])}]{strength['label']}[/{_strength_color(strength['score'])}]")
    
    if return_pw:
        return pw
    else:
        copy_with_timeout(pw)

def cmd_export():
    v = get_vault()
    filepath = console.input("[bold dim]❯[/bold dim] [white]Export path (e.g., backup.botpass):[/white] ").strip()
    if not filepath:
        filepath = "vault_backup.botpass"
    
    try:
        v.export_backup(filepath)
        console.print(f"[green]Vault exported to {filepath}. Keep it safe![/green]")
    except Exception as e:
        console.print(f"[red]Export failed: {e}[/red]")

def cmd_breach():
    """Check a password against Have I Been Pwned."""
    pw = getpass.getpass("❯ Password to check: ")
    console.print("[dim]Checking against known breaches (using k-anonymity)...[/dim]")
    count = check_hibp(pw)
    if count > 0:
        console.print(f"[bold red][ WARNING ] Found in {count:,} breaches! Change this password immediately.[/bold red]")
    elif count == 0:
        console.print("[green][ OK ] Not found in any known breaches. You're good.[/green]")
    else:
        console.print("[yellow]Could not reach the breach database. Try again later.[/yellow]")

def _strength_color(score):
    colors = ["red", "red", "yellow", "green", "bold green"]
    return colors[score]

def cmd_import():
    v = get_vault()
    filepath = console.input("[bold dim]❯[/bold dim] [white]Backup file path (e.g., vault_backup.botpass):[/white] ").strip()
    if not filepath:
        console.print("[red]No path given.[/red]")
        return
    
    if not os.path.exists(filepath):
        console.print(f"[red]File not found: {filepath}[/red]")
        return
    
    try:
        result = v.import_backup(filepath)
        console.print(f"[green]Import done! {result['imported']} entries imported, {result['skipped']} skipped (duplicates).[/green]")
    except Exception as e:
        console.print(f"[red]Import failed: {e}[/red]")

def main():
    banner()
    
    v = get_vault()
    
    # Check if we need setup
    if not os.path.exists(VAULT_PATH):
        if not cmd_setup():
            sys.exit(1)
    else:
        # Loop until unlocked
        unlocked = False
        while not unlocked:
            unlocked = cmd_unlock()
            
    # Interactive loop
    while True:
        try:
            console.print("\n[bold dim]Commands:[/bold dim] [white]list, add, get, update, del, generate, breach, export, import, changepw, lock, quit[/white]")
            cmd = console.input("[bold dim]❯[/bold dim] ").strip().lower()
            
            if cmd == "quit" or cmd == "q" or cmd == "exit":
                v.lock()
                console.print("Locked and quitting. Bye!")
                break
            elif cmd == "lock":
                v.lock()
                console.print("[green]Vault locked.[/green]")
                # wait for unlock
                unlocked = False
                while not unlocked:
                    unlocked = cmd_unlock()
            elif cmd == "list":
                cmd_list()
            elif cmd == "add":
                cmd_add()
            elif cmd == "get":
                cmd_get()
            elif cmd == "update":
                cmd_update()
            elif cmd == "del":
                cmd_delete()
            elif cmd == "generate" or cmd == "gen":
                cmd_generate()
            elif cmd == "breach":
                cmd_breach()
            elif cmd == "export":
                cmd_export()
            elif cmd == "changepw":
                cmd_changepw()
            elif cmd == "import":
                cmd_import()
            elif cmd == "":
                pass
            else:
                console.print(f"[red]Unknown command: {cmd}[/red]")
                
        except KeyboardInterrupt:
            v.lock()
            console.print("\n[yellow]Caught Ctrl+C. Locked vault. Exiting.[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Unhandled error: {e}[/red]")

if __name__ == "__main__":
    main()
