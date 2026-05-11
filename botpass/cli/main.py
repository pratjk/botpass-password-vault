import os
import sys
import getpass
import time
from threading import Timer

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import pyperclip

from botpass.core.vault import Vault

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
    art = """
[bold cyan]
  _           _                     
 | |         | |                    
 | |__   ___ | |_ _ __   __ _  ___ ___ 
 | '_ \\ / _ \\| __| '_ \\ / _` |/ __/ __|
 | |_) | (_) | |_| |_) | (_| | (__\\__ \\
 |_.__/ \\___/ \\__| .__/ \\__,_|\\___|___/
                 | |                    
                 |_|                    
[/bold cyan]
    [italic]Your Local Vault[/italic]
    """
    console.print(Panel.fit(art, border_style="cyan"))

def cmd_setup():
    v = get_vault()
    console.print("[yellow]Looks like this is your first time here.[/yellow]")
    console.print("[bold red]WARNING: If you forget your master password, your data is GONE. No recovery.[/bold red]")
    
    pw1 = getpass.getpass("Enter a strong master password: ")
    pw2 = getpass.getpass("Verify password: ")
    
    if pw1 != pw2:
        console.print("[red]🙅 Nope. Passwords don't match. Try again.[/red]")
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
    pw = getpass.getpass("Master Password: ")
    
    if v.unlock(pw):
        console.print("[green]Vault unlocked![/green]")
        return True
    else:
        console.print("[red]🙅 Nope. Wrong password. Try again.[/red]")
        return False

def cmd_list():
    v = get_vault()
    try:
        entries = v.list_entries()
        if not entries:
            console.print("[yellow]Vault is empty. Add something![/yellow]")
            return

        table = Table(title="Vault Entries", show_header=True, header_style="bold magenta")
        table.add_column("Domain", style="cyan")
        table.add_column("Username", style="green")

        # I find this easier to debug than a one-liner
        for e in entries:
            table.add_row(e.get("domain", "?"), e.get("username", "?"))
            
        console.print(table)
    except Exception as e:
        console.print(f"[red]Something broke. Try again? ({e})[/red]")

def cmd_add():
    v = get_vault()
    domain = console.input("[cyan]Domain/Site: [/cyan]")
    username = console.input("[cyan]Username: [/cyan]")
    password = getpass.getpass("Password: ")
    
    try:
        v.add(domain, username, password)
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
        copy_with_timeout(data.get("password"), 10)
    except Exception as e:
        console.print(f"[red]Something broke. ({e})[/red]")

def cmd_delete():
    v = get_vault()
    domain = console.input("[cyan]Domain to delete: [/cyan]")
    
    try:
        if v.delete(domain):
            console.print(f"[green]Deleted {domain}. It's gone forever.[/green]")
        else:
            console.print("[red]Not found.[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

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
            console.print("\n[bold]Commands:[/bold] [cyan]list[/cyan], [cyan]add[/cyan], [cyan]get[/cyan], [cyan]del[/cyan], [cyan]lock[/cyan], [cyan]quit[/cyan]")
            cmd = console.input("> ").strip().lower()
            
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
            elif cmd == "del":
                cmd_delete()
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
