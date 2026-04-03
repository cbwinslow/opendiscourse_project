#!/usr/bin/env python3
"""
OpenDiscourse Download Progress Dashboard - Simple Version

A simpler dashboard for testing and monitoring download progress.
"""

from datetime import datetime
from opendiscourse.database import sync_engine
from opendiscourse.utils.download_state import DownloadStateManager, DownloadStatus, DownloadState
from sqlalchemy.orm import sessionmaker
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box


def main():
    """Simple dashboard display."""
    console = Console()

    console.print("\n[bold cyan]🚀 OpenDiscourse Download Dashboard[/bold cyan]\n")

    session_factory = sessionmaker(bind=sync_engine)

    with session_factory() as session:
        state_mgr = DownloadStateManager(session)

        # Get stats
        stats = state_mgr.get_download_stats()
        total_files = sum(stats.values())
        success_rate = (stats.get(DownloadStatus.COMPLETED.value, 0) / total_files * 100) if total_files > 0 else 0

        # Create stats panel
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

        stats_panel = Panel(stats_text, title="📈 Statistics", border_style="yellow")

        # Get recent downloads
        recent_downloads = (
            session.query(DownloadState)
            .filter(DownloadState.status.in_([DownloadStatus.COMPLETED.value, DownloadStatus.FAILED.value]))
            .order_by(DownloadState.updated_at.desc())
            .limit(10)
            .all()
        )

        # Create table
        table = Table(box=box.MINIMAL_DOUBLE_HEAD)
        table.add_column("📁 File", style="cyan", no_wrap=True)
        table.add_column("📊 Size", style="green", justify="right")
        table.add_column("✅ Status", style="bold")
        table.add_column("🕒 Time", style="dim")

        if not recent_downloads:
            table.add_row("[dim]No downloads yet[/dim]", "", "", "")
        else:
            for download in recent_downloads:
                status_icon = "✅" if download.status == DownloadStatus.COMPLETED.value else "❌"
                status_text = "Success" if download.status == DownloadStatus.COMPLETED.value else "Failed"
                status_style = "green" if download.status == DownloadStatus.COMPLETED.value else "red"

                time_ago = "N/A"
                if download.updated_at:
                    diff = datetime.utcnow() - download.updated_at
                    if diff.days > 0:
                        time_ago = f"{diff.days}d ago"
                    elif diff.seconds > 3600:
                        time_ago = f"{diff.seconds // 3600}h ago"
                    elif diff.seconds > 60:
                        time_ago = f"{diff.seconds // 60}m ago"
                    else:
                        time_ago = f"{diff.seconds}s ago"

                table.add_row(
                    download.filename[:40] + "..." if len(download.filename) > 40 else download.filename,
                    f"{download.size_bytes or 0:,} B",
                    f"[{status_style}]{status_icon} {status_text}[/{status_style}]",
                    time_ago,
                )

        downloads_panel = Panel(table, title="📋 Recent Downloads", border_style="green")

        # Display
        console.print(stats_panel)
        console.print()
        console.print(downloads_panel)


if __name__ == "__main__":
    main()
