#!/usr/bin/env python3
"""
OpenDiscourse Download Progress Dashboard

Beautiful TUI showing real-time download progress, statistics, and system status.
"""

import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import psutil

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    DownloadColumn,
    TransferSpeedColumn,
)
from rich.live import Live
from rich.text import Text
from rich.columns import Columns
from rich.align import Align
from rich import box

from sqlalchemy.orm import sessionmaker
from opendiscourse.database import sync_engine
from opendiscourse.utils.download_state import DownloadStateManager, DownloadState, DownloadStatus


class DownloadDashboard:
    """Beautiful TUI dashboard for monitoring download progress."""

    def __init__(self):
        self.console = Console()
        self.session_factory = sessionmaker(bind=sync_engine)
        self.state_manager = None

    def initialize(self):
        """Initialize database connection."""
        with self.session_factory() as session:
            self.state_manager = DownloadStateManager(session)

    def get_download_stats(self) -> Dict[str, int]:
        """Get comprehensive download statistics."""
        with self.session_factory() as session:
            state_mgr = DownloadStateManager(session)
            return state_mgr.get_download_stats()

    def get_recent_downloads(self, limit: int = 20) -> List[DownloadState]:
        """Get recently completed downloads."""
        with self.session_factory() as session:
            return (
                session.query(DownloadState)
                .filter(DownloadState.status.in_([DownloadStatus.COMPLETED.value, DownloadStatus.FAILED.value]))
                .order_by(DownloadState.updated_at.desc())
                .limit(limit)
                .all()
            )

    def get_active_downloads(self) -> List[DownloadState]:
        """Get currently active downloads."""
        with self.session_factory() as session:
            return session.query(DownloadState).filter(DownloadState.status == DownloadStatus.IN_PROGRESS.value).all()

    def get_system_stats(self) -> Dict[str, str]:
        """Get system resource statistics."""
        disk = psutil.disk_usage("/")
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=1)

        return {
            "cpu_usage": f"{cpu:.1f}%",
            "memory_usage": f"{memory.percent:.1f}%",
            "disk_usage": f"{disk.percent:.1f}%",
            "disk_free": f"{disk.free / (1024**3):.1f} GB",
            "scheduler_running": self._check_scheduler_running(),
            "database_size": self._get_database_size(),
        }

    def _check_scheduler_running(self) -> str:
        """Check if download scheduler is running."""
        import subprocess

        try:
            result = subprocess.run(["pgrep", "-f", "download_scheduler"], capture_output=True, text=True)
            return "🟢 Running" if result.returncode == 0 else "🔴 Stopped"
        except:
            return "❓ Unknown"

    def _get_database_size(self) -> str:
        """Get database size."""
        try:
            with self.session_factory() as session:
                result = session.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
                return result.scalar()
        except:
            return "Unknown"

    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if not size_bytes:
            return "Unknown"

        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return ".1f"
            size_bytes /= 1024.0
        return ".1f"

    def create_progress_panel(self) -> Panel:
        """Create progress bars for active downloads."""
        active_downloads = self.get_active_downloads()

        if not active_downloads:
            content = Align.center("[dim]No active downloads[/dim]")
        else:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.fields[filename]}[/bold blue]"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                TextColumn("eta: {task.fields[eta]}"),
                expand=True,
            )

            for download in active_downloads:
                # Simulate progress for demo (in real implementation, track actual progress)
                progress.add_task(
                    f"{download.collection.upper()}: {download.filename}",
                    filename=download.filename[:50] + "..." if len(download.filename) > 50 else download.filename,
                    total=100,
                    completed=50,  # Would be actual progress
                    eta="2.3s",
                )

            content = progress

        return Panel(content, title="🔄 Active Downloads", border_style="blue")

    def create_completed_table(self) -> Panel:
        """Create table of recently completed downloads."""
        recent_downloads = self.get_recent_downloads(15)

        table = Table(box=box.MINIMAL_DOUBLE_HEAD)
        table.add_column("📁 File", style="cyan", no_wrap=True)
        table.add_column("📊 Size", style="green", justify="right")
        table.add_column("✅ Status", style="bold")
        table.add_column("🕒 Time", style="dim")

        if not recent_downloads:
            table.add_row("[dim]No recent downloads[/dim]", "", "", "")
        else:
            for download in recent_downloads:
                status_icon = "✅" if download.status == DownloadStatus.COMPLETED.value else "❌"
                status_text = "Success" if download.status == DownloadStatus.COMPLETED.value else "Failed"
                status_style = "green" if download.status == DownloadStatus.COMPLETED.value else "red"

                time_ago = self._time_ago(download.completed_at or download.updated_at)

                table.add_row(
                    download.filename[:40] + "..." if len(download.filename) > 40 else download.filename,
                    self.format_file_size(download.size_bytes),
                    f"[{status_style}]{status_icon} {status_text}[/{status_style}]",
                    time_ago,
                )

        return Panel(table, title="📋 Recent Downloads", border_style="green")

    def create_stats_panel(self) -> Panel:
        """Create statistics panel."""
        stats = self.get_download_stats()

        total_files = sum(stats.values())
        success_rate = (stats.get(DownloadStatus.COMPLETED.value, 0) / total_files * 100) if total_files > 0 else 0

        stats_text = Text()
        stats_text.append("📊 Download Statistics\n\n", style="bold underline")

        stats_text.append("Total Files: ", style="bold")
        stats_text.append(f"{total_files:,}\n", style="cyan")

        stats_text.append("Success Rate: ", style="bold")
        stats_text.append(".1f")
        stats_text.append("Completed: ", style="bold")
        stats_text.append(f"{stats.get(DownloadStatus.COMPLETED.value, 0):,}\n", style="green")

        stats_text.append("In Progress: ", style="bold")
        stats_text.append(f"{stats.get(DownloadStatus.IN_PROGRESS.value, 0):,}\n", style="yellow")

        stats_text.append("Failed: ", style="bold")
        stats_text.append(f"{stats.get(DownloadStatus.FAILED.value, 0):,}\n", style="red")

        stats_text.append("Pending: ", style="bold")
        stats_text.append(f"{stats.get(DownloadStatus.PENDING.value, 0):,}\n", style="blue")

        return Panel(stats_text, title="📈 Statistics", border_style="yellow")

    def create_system_panel(self) -> Panel:
        """Create system status panel."""
        system_stats = self.get_system_stats()

        system_text = Text()
        system_text.append("🖥️  System Status\n\n", style="bold underline")

        system_text.append("CPU Usage: ", style="bold")
        system_text.append(f"{system_stats['cpu_usage']}\n", style="cyan")

        system_text.append("Memory: ", style="bold")
        system_text.append(f"{system_stats['memory_usage']}\n", style="cyan")

        system_text.append("Disk Usage: ", style="bold")
        system_text.append(f"{system_stats['disk_usage']} ({system_stats['disk_free']} free)\n", style="cyan")

        system_text.append("Scheduler: ", style="bold")
        system_text.append(
            f"{system_stats['scheduler_running']}\n",
            style="green" if "Running" in system_stats["scheduler_running"] else "red",
        )

        system_text.append("Database Size: ", style="bold")
        system_text.append(f"{system_stats['database_size']}\n", style="cyan")

        return Panel(system_text, title="🔧 System", border_style="magenta")

    def _time_ago(self, dt: datetime) -> str:
        """Convert datetime to human readable time ago."""
        if not dt:
            return "Unknown"

        now = datetime.utcnow()
        diff = now - dt

        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return f"{diff.seconds}s ago"

    def create_layout(self) -> Layout:
        """Create the main dashboard layout."""
        layout = Layout()

        # Split into top/bottom
        layout.split(Layout(name="upper", ratio=1), Layout(name="lower", ratio=1))

        # Upper section: progress and stats
        layout["upper"].split_row(Layout(name="progress", ratio=2), Layout(name="stats", ratio=1))

        # Lower section: completed downloads and system status
        layout["lower"].split_row(Layout(name="completed", ratio=2), Layout(name="system", ratio=1))

        return layout

    def run_dashboard(self):
        """Run the live dashboard."""
        self.initialize()

        layout = self.create_layout()

        with Live(layout, refresh_per_second=2, console=self.console) as live:
            try:
                while True:
                    # Update layout with current data
                    layout["upper"]["progress"].update(self.create_progress_panel())
                    layout["upper"]["stats"].update(self.create_stats_panel())
                    layout["lower"]["completed"].update(self.create_completed_table())
                    layout["lower"]["system"].update(self.create_system_panel())

                    time.sleep(2)

            except KeyboardInterrupt:
                self.console.print(
                    "\n[bold green]Dashboard closed. Download scheduler continues running in background.[/bold green]"
                )


def main():
    """Main entry point."""
    console = Console()

    # Show welcome message
    console.print("\n[bold cyan]🚀 OpenDiscourse Download Dashboard[/bold cyan]")
    console.print("[dim]Press Ctrl+C to exit. Downloads continue in background.[/dim]\n")

    dashboard = DownloadDashboard()
    dashboard.run_dashboard()


if __name__ == "__main__":
    main()
