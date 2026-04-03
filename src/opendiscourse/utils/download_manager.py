"""Download manager with aria2c support for high-speed parallel downloads."""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class DownloadManager:
    """High-performance download manager using aria2c for parallel downloads."""

    def __init__(self, max_concurrent: int = 8, download_dir: Optional[Path] = None):
        self.max_concurrent = max_concurrent
        self.download_dir = download_dir or Path(tempfile.gettempdir()) / "opendiscourse_downloads"
        self.download_dir.mkdir(parents=True, exist_ok=True)

    async def download_files(
        self, urls: List[str], output_dir: Optional[Path] = None, preserve_structure: bool = False
    ) -> Dict[str, Path]:
        """
        Download multiple files in parallel using aria2c.

        Args:
            urls: List of URLs to download
            output_dir: Directory to save files (default: temp dir)
            preserve_structure: Whether to preserve URL directory structure

        Returns:
            Dict mapping URLs to downloaded file paths
        """
        if not urls:
            return {}

        output_dir = output_dir or self.download_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create aria2c input file
        input_file = output_dir / "aria2c_input.txt"
        with open(input_file, "w") as f:
            for url in urls:
                if preserve_structure:
                    # Extract path from URL to preserve structure
                    parsed = urlparse(url)
                    relative_path = parsed.path.lstrip("/")
                    output_path = output_dir / relative_path
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    f.write(f"{url}\n  out={relative_path}\n")
                else:
                    f.write(f"{url}\n")

        # Run aria2c
        cmd = [
            "aria2c",
            "--input-file",
            str(input_file),
            "--dir",
            str(output_dir),
            "--max-concurrent-downloads",
            str(self.max_concurrent),
            "--max-connection-per-server",
            "4",
            "--min-split-size",
            "1M",
            "--split",
            "4",
            "--continue=true",
            "--auto-file-renaming=false",
            "--allow-overwrite=true",
            "--quiet=false",
            "--summary-interval=0",
            "--log-level=notice",
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info(f"Downloaded {len(urls)} files successfully")
            else:
                logger.error(f"aria2c failed: {stderr.decode()}")

            # Map URLs to downloaded files
            result = {}
            for url in urls:
                if preserve_structure:
                    parsed = urlparse(url)
                    relative_path = parsed.path.lstrip("/")
                    file_path = output_dir / relative_path
                else:
                    # Extract filename from URL
                    filename = Path(urlparse(url).path).name
                    file_path = output_dir / filename

                if file_path.exists():
                    result[url] = file_path

            return result

        finally:
            # Clean up input file
            if input_file.exists():
                input_file.unlink()

    async def download_file(self, url: str, output_path: Optional[Path] = None) -> Optional[Path]:
        """
        Download a single file using aria2c.

        Args:
            url: URL to download
            output_path: Where to save the file

        Returns:
            Path to downloaded file or None if failed
        """
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cmd = ["aria2c", url, "--out", output_path.name, "--dir", str(output_path.parent)]
        else:
            output_path = self.download_dir / Path(urlparse(url).path).name
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cmd = ["aria2c", url, "--dir", str(self.download_dir)]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
            )

            await process.wait()

            if process.returncode == 0 and output_path.exists():
                return output_path

        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")

        return None

    def cleanup_old_downloads(self, max_age_days: int = 7) -> int:
        """
        Clean up old downloaded files.

        Args:
            max_age_days: Remove files older than this many days

        Returns:
            Number of files removed
        """
        import time

        removed = 0
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)

        for file_path in self.download_dir.rglob("*"):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    removed += 1
                except Exception as e:
                    logger.warning(f"Failed to remove {file_path}: {e}")

        logger.info(f"Cleaned up {removed} old download files")
        return removed
