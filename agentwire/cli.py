"""Command-line interface for AgentWire."""

import os
import sys
import signal
import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="agentwire",
    help="Real-time message bus and inspector for multi-agent LLM systems",
    add_completion=False,
)
console = Console()

PID_FILE = Path(".agentwire.pid")
DEFAULT_PORT = 7433
DEFAULT_DB = "sqlite:///agentwire.db"


@app.command()
def start(
    port: int = typer.Option(DEFAULT_PORT, "--port", "-p", help="Port to run server on"),
    db: str = typer.Option(DEFAULT_DB, "--db", help="Database URL (sqlite:// or postgres://)"),
    no_dashboard: bool = typer.Option(False, "--no-dashboard", help="API-only mode, no dashboard"),
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind to"),
):
    """Start the AgentWire server."""
    
    # Check if already running
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            # Check if process is actually running
            os.kill(pid, 0)
            console.print(f"[yellow]AgentWire is already running (PID: {pid})[/yellow]")
            console.print(f"[yellow]Use 'agentwire stop' to stop it first[/yellow]")
            return
        except (ProcessLookupError, ValueError):
            # Process not running, remove stale PID file
            PID_FILE.unlink()
    
    console.print(f"[green]Starting AgentWire server...[/green]")
    console.print(f"  Host: {host}")
    console.print(f"  Port: {port}")
    console.print(f"  Database: {db}")
    console.print(f"  Dashboard: {'disabled' if no_dashboard else 'enabled'}")
    
    try:
        # Start uvicorn
        import uvicorn
        
        # Store PID
        PID_FILE.write_text(str(os.getpid()))
        
        console.print(f"\n[green]✓ Server started at http://{host}:{port}[/green]")
        console.print(f"[green]✓ Dashboard at http://localhost:{port}[/green]")
        console.print(f"[dim]Press Ctrl+C to stop[/dim]\n")
        
        # Run server
        uvicorn.run(
            "agentwire.bus:app",
            host=host,
            port=port,
            log_level="info",
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")
    finally:
        if PID_FILE.exists():
            PID_FILE.unlink()


@app.command()
def stop():
    """Stop the AgentWire server."""
    
    if not PID_FILE.exists():
        console.print("[yellow]AgentWire is not running[/yellow]")
        return
    
    try:
        pid = int(PID_FILE.read_text().strip())
        console.print(f"[yellow]Stopping AgentWire (PID: {pid})...[/yellow]")
        
        # Send SIGTERM
        os.kill(pid, signal.SIGTERM)
        
        # Wait a bit and check if stopped
        import time
        time.sleep(1)
        
        try:
            os.kill(pid, 0)
            console.print("[yellow]Server is still running, sending SIGKILL...[/yellow]")
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        
        PID_FILE.unlink()
        console.print("[green]✓ AgentWire stopped[/green]")
        
    except (ProcessLookupError, ValueError) as e:
        console.print(f"[red]Error stopping server: {e}[/red]")
        if PID_FILE.exists():
            PID_FILE.unlink()


@app.command()
def status():
    """Show AgentWire server status."""
    
    # Check if running
    is_running = False
    pid = None
    
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, 0)
            is_running = True
        except (ProcessLookupError, ValueError):
            PID_FILE.unlink()
    
    # Create status table
    table = Table(title="AgentWire Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green" if is_running else "red")
    
    table.add_row("Status", "Running ✓" if is_running else "Stopped ✗")
    if pid:
        table.add_row("PID", str(pid))
    table.add_row("Server URL", f"http://localhost:{DEFAULT_PORT}")
    table.add_row("Dashboard URL", f"http://localhost:{DEFAULT_PORT}")
    
    # Try to get stats from API if running
    if is_running:
        try:
            import httpx
            response = httpx.get(f"http://localhost:{DEFAULT_PORT}/api/stats", timeout=2)
            if response.status_code == 200:
                stats = response.json()
                table.add_row("Total Messages", str(stats.get("total_messages", 0)))
                table.add_row("Total Sessions", str(stats.get("total_sessions", 0)))
                table.add_row("Total Tokens", f"{stats.get('total_tokens', 0):,}")
                table.add_row("Total Cost", f"${stats.get('total_cost_usd', 0):.4f}")
        except Exception:
            pass
    
    console.print(table)


@app.command()
def clear(
    session: Optional[str] = typer.Option(None, "--session", "-s", help="Clear specific session"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Clear all sessions and messages."""
    
    if session:
        if not force:
            confirm = typer.confirm(f"Clear session '{session}'?")
            if not confirm:
                console.print("[yellow]Cancelled[/yellow]")
                return
        
        try:
            import httpx
            response = httpx.delete(
                f"http://localhost:{DEFAULT_PORT}/api/sessions/{session}",
                timeout=5
            )
            if response.status_code == 200:
                console.print(f"[green]✓ Session '{session}' cleared[/green]")
            else:
                console.print(f"[red]Error: {response.status_code}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            console.print("[yellow]Is the server running? Use 'agentwire start'[/yellow]")
    else:
        if not force:
            confirm = typer.confirm("Clear ALL sessions and messages?")
            if not confirm:
                console.print("[yellow]Cancelled[/yellow]")
                return
        
        try:
            import httpx
            response = httpx.delete(
                f"http://localhost:{DEFAULT_PORT}/api/messages",
                timeout=5
            )
            if response.status_code == 200:
                console.print("[green]✓ All data cleared[/green]")
            else:
                console.print(f"[red]Error: {response.status_code}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            console.print("[yellow]Is the server running? Use 'agentwire start'[/yellow]")


@app.command()
def docker(
    action: str = typer.Argument(..., help="Action: 'up' or 'down'"),
):
    """Manage AgentWire with Docker Compose."""
    
    if action not in ("up", "down"):
        console.print("[red]Error: action must be 'up' or 'down'[/red]")
        return
    
    compose_file = Path("docker-compose.yml")
    
    if action == "up":
        # Generate docker-compose.yml
        compose_content = """version: '3.8'

services:
  agentwire:
    image: python:3.10-slim
    command: >
      sh -c "pip install agentwire &&
             agentwire start --host 0.0.0.0 --port 7433"
    ports:
      - "7433:7433"
    volumes:
      - agentwire-data:/data
    environment:
      - AGENTWIRE_DB=sqlite:////data/agentwire.db
    restart: unless-stopped

volumes:
  agentwire-data:
"""
        compose_file.write_text(compose_content)
        console.print("[green]✓ Generated docker-compose.yml[/green]")
        
        # Run docker compose up
        console.print("[yellow]Starting Docker containers...[/yellow]")
        result = subprocess.run(["docker", "compose", "up", "-d"], capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print("[green]✓ AgentWire started in Docker[/green]")
            console.print(f"[green]✓ Dashboard at http://localhost:7433[/green]")
        else:
            console.print(f"[red]Error: {result.stderr}[/red]")
    
    elif action == "down":
        if not compose_file.exists():
            console.print("[yellow]docker-compose.yml not found[/yellow]")
            return
        
        console.print("[yellow]Stopping Docker containers...[/yellow]")
        result = subprocess.run(["docker", "compose", "down"], capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print("[green]✓ AgentWire stopped[/green]")
        else:
            console.print(f"[red]Error: {result.stderr}[/red]")


if __name__ == "__main__":
    app()
