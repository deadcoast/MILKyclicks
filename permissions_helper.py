#!/usr/bin/env python3
"""
MILKyclicks Permissions Helper
This script helps check and request the necessary permissions for MILKyclicks to function properly.
"""

import os
import sys
import subprocess
from rich.console import Console
from rich.panel import Panel

console = Console()

def check_accessibility_permissions():
    """Check if Terminal has Accessibility permissions"""
    # Uses AppleScript to check accessibility permissions
    script = '''
    tell application "System Events"
        try
            set ui_enabled to UI elements enabled
            return ui_enabled
        on error
            return false
        end try
    end tell
    '''
    
    try:
        result = subprocess.run(
            ['osascript', '-e', script], 
            capture_output=True, 
            text=True
        )
        return result.stdout.strip().lower() == 'true'
    except Exception as e:
        console.print(f"[red]Error checking permissions: {e}[/red]")
        return False

def request_accessibility_permissions():
    """Show instructions for enabling accessibility permissions"""
    terminal_app = "/Applications/Utilities/Terminal.app"
    python_path = sys.executable
    
    console.print(Panel.fit(
        "[bold yellow]MILKyclicks Permissions Setup[/bold yellow]\n\n"
        "To use MILKyclicks, you need to grant Accessibility permissions to:\n"
        f"1. [cyan]{terminal_app}[/cyan]\n"
        f"2. [cyan]{python_path}[/cyan]\n\n"
        "[bold]Instructions:[/bold]\n"
        "1. Open [bold]System Preferences > Security & Privacy > Privacy > Accessibility[/bold]\n"
        "2. Click the lock icon and enter your password\n"
        "3. Click the [bold]+ button[/bold] and add the Terminal app\n"
        "4. Click the [bold]+ button[/bold] again and add your Python executable\n"
        "5. Ensure the checkboxes next to both are selected\n"
        "6. Restart Terminal and try running MILKyclicks again\n\n"
        "[bold green]Would you like to open System Preferences now?[/bold green] (y/n)",
        title="Permissions Required",
        border_style="yellow"
    ))
    
    response = console.input("[bold yellow]> [/bold yellow]")
    if response.lower() in ('y', 'yes'):
        # Open System Preferences directly to Accessibility
        os.system("open 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'")
        console.print("[green]Opened System Preferences. Please grant permissions as described above.[/green]")
    
    console.print("\n[bold]After granting permissions:[/bold]")
    console.print("1. Close Terminal and open a new Terminal window")
    console.print("2. Run MILKyclicks again: [cyan]python src/main.py[/cyan]")

def main():
    """Main function to check and request permissions"""
    console.print("[bold]MILKyclicks Permissions Helper[/bold]")
    
    has_permissions = check_accessibility_permissions()
    
    if has_permissions:
        console.print("[green]✓ Accessibility permissions are already granted![/green]")
        console.print("[cyan]You can now run MILKyclicks: python src/main.py[/cyan]")
    else:
        console.print("[yellow]! Accessibility permissions are required but not granted.[/yellow]")
        request_accessibility_permissions()

if __name__ == "__main__":
    main()
