#!/usr/bin/env python3
"""
OpenDiscourse Download Scheduler

Schedules and manages long-running data ingestion tasks.
Designed to run continuously and handle downloads through the night.
"""

import asyncio
import logging
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import schedule
from sqlalchemy.orm import sessionmaker

from opendiscourse.config import get_settings
from opendiscourse.database import sync_engine
from opendiscourse.ingestion.govinfo import GovInfoIngestion
from opendiscourse.ingestion.fec import FECIngestion
from opendiscourse.utils.download_manager import DownloadManager
from opendiscourse.utils.download_state import DownloadStateManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("/tmp/opendiscourse_logs/scheduler.log"), logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)
settings = get_settings()


class DownloadScheduler:
    """Manages scheduled downloads and ingestion tasks."""

    def __init__(self):
        self.session_factory = sessionmaker(bind=sync_engine)
        self.download_manager = DownloadManager(max_concurrent=4)
        self.state_manager = None
        self.running = True
        self.ingestion_tasks = {"govinfo": GovInfoIngestion(), "fec": FECIngestion()}

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def shutdown(self, signum, frame):
        """Graceful shutdown handler."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    async def initialize(self):
        """Initialize database connections and state."""
        with self.session_factory() as session:
            self.state_manager = DownloadStateManager(session)

    def schedule_downloads(self):
        """Setup scheduled download tasks."""

        # GovInfo downloads - run during off-peak hours (2-6 AM)
        schedule.every().day.at("02:00").do(self.run_govinfo_ingestion)
        schedule.every().day.at("03:00").do(self.run_govinfo_bill_texts)
        schedule.every().day.at("04:00").do(self.run_govinfo_congressional_record)
        schedule.every().day.at("05:00").do(self.run_govinfo_federal_register)

        # FEC downloads - run during different off-peak hours (8-11 PM)
        schedule.every().day.at("20:00").do(self.run_fec_candidates)
        schedule.every().day.at("21:00").do(self.run_fec_committees)
        schedule.every().day.at("22:00").do(self.run_fec_contributions)
        schedule.every().day.at("23:00").do(self.run_fec_disbursements)

        # Maintenance tasks - run daily at 6 AM
        schedule.every().day.at("06:00").do(self.cleanup_old_downloads)
        schedule.every().day.at("06:30").do(self.update_download_stats)

        # Retry failed downloads - run every 2 hours
        schedule.every(2).hours.do(self.retry_failed_downloads)

        logger.info("Download schedule configured")

    async def run_govinfo_ingestion(self):
        """Run GovInfo bill status ingestion."""
        try:
            logger.info("Starting GovInfo bill status ingestion")
            with self.session_factory() as session:
                state_mgr = DownloadStateManager(session)
                ingestion = GovInfoIngestion()

                # Update bill statuses
                result = await ingestion.update_bill_statuses()
                logger.info(f"GovInfo bill status update: {result}")

        except Exception as e:
            logger.error(f"GovInfo bill status ingestion failed: {e}")

    async def run_govinfo_bill_texts(self):
        """Run GovInfo bill text downloads."""
        try:
            logger.info("Starting GovInfo bill text downloads")
            with self.session_factory() as session:
                state_mgr = DownloadStateManager(session)
                ingestion = GovInfoIngestion()

                # Download bill texts
                result = await ingestion.download_bill_texts()
                logger.info(f"GovInfo bill text download: {result}")

        except Exception as e:
            logger.error(f"GovInfo bill text download failed: {e}")

    async def run_govinfo_congressional_record(self):
        """Run GovInfo Congressional Record downloads."""
        try:
            logger.info("Starting GovInfo Congressional Record downloads")
            with self.session_factory() as session:
                state_mgr = DownloadStateManager(session)
                ingestion = GovInfoIngestion()

                # Download Congressional Record
                result = await ingestion.download_congressional_records()
                logger.info(f"GovInfo Congressional Record download: {result}")

        except Exception as e:
            logger.error(f"GovInfo Congressional Record download failed: {e}")

    async def run_govinfo_federal_register(self):
        """Run GovInfo Federal Register downloads."""
        try:
            logger.info("Starting GovInfo Federal Register downloads")
            with self.session_factory() as session:
                state_mgr = DownloadStateManager(session)
                ingestion = GovInfoIngestion()

                # Download Federal Register
                result = await ingestion.download_federal_register()
                logger.info(f"GovInfo Federal Register download: {result}")

        except Exception as e:
            logger.error(f"GovInfo Federal Register download failed: {e}")

    async def run_fec_candidates(self):
        """Run FEC candidate data ingestion."""
        try:
            logger.info("Starting FEC candidate ingestion")
            with self.session_factory() as session:
                state_mgr = DownloadStateManager(session)
                ingestion = FECIngestion()

                # Ingest candidates
                result = await ingestion.ingest_candidates()
                logger.info(f"FEC candidate ingestion: {result}")

        except Exception as e:
            logger.error(f"FEC candidate ingestion failed: {e}")

    async def run_fec_committees(self):
        """Run FEC committee data ingestion."""
        try:
            logger.info("Starting FEC committee ingestion")
            with self.session_factory() as session:
                state_mgr = DownloadStateManager(session)
                ingestion = FECIngestion()

                # Ingest committees
                result = await ingestion.ingest_committees()
                logger.info(f"FEC committee ingestion: {result}")

        except Exception as e:
            logger.error(f"FEC committee ingestion failed: {e}")

    async def run_fec_contributions(self):
        """Run FEC contribution data ingestion."""
        try:
            logger.info("Starting FEC contributions ingestion")
            with self.session_factory() as session:
                state_mgr = DownloadStateManager(session)
                ingestion = FECIngestion()

                # Ingest contributions (this is the big one)
                result = await ingestion.ingest_contributions()
                logger.info(f"FEC contributions ingestion: {result}")

        except Exception as e:
            logger.error(f"FEC contributions ingestion failed: {e}")

    async def run_fec_disbursements(self):
        """Run FEC disbursement data ingestion."""
        try:
            logger.info("Starting FEC disbursements ingestion")
            with self.session_factory() as session:
                state_mgr = DownloadStateManager(session)
                ingestion = FECIngestion()

                # Ingest disbursements
                result = await ingestion.ingest_disbursements()
                logger.info(f"FEC disbursements ingestion: {result}")

        except Exception as e:
            logger.error(f"FEC disbursements ingestion failed: {e}")

    def cleanup_old_downloads(self):
        """Clean up old download files."""
        try:
            removed = self.download_manager.cleanup_old_downloads(max_age_days=7)
            logger.info(f"Cleaned up {removed} old download files")

            with self.session_factory() as session:
                state_mgr = DownloadStateManager(session)
                cleaned_states = state_mgr.cleanup_completed_tasks(days_old=30)
                logger.info(f"Cleaned up {cleaned_states} old download state records")

        except Exception as e:
            logger.error(f"Download cleanup failed: {e}")

    def update_download_stats(self):
        """Update and log download statistics."""
        try:
            with self.session_factory() as session:
                state_mgr = DownloadStateManager(session)

                # Get stats for each source
                sources = ["govinfo", "fec"]
                for source in sources:
                    stats = state_mgr.get_download_stats(source)
                    logger.info(f"Download stats for {source}: {stats}")

                # Mark duplicate URLs
                duplicates = state_mgr.mark_duplicate_urls()
                if duplicates > 0:
                    logger.warning(f"Marked {duplicates} duplicate download tasks as cancelled")

        except Exception as e:
            logger.error(f"Stats update failed: {e}")

    def retry_failed_downloads(self):
        """Retry failed downloads that haven't exceeded max retries."""
        try:
            with self.session_factory() as session:
                state_mgr = DownloadStateManager(session)
                failed_tasks = state_mgr.get_failed_tasks()

                if failed_tasks:
                    logger.info(f"Retrying {len(failed_tasks)} failed download tasks")

                    for task in failed_tasks:
                        # Here we would queue the retry - for now just log
                        logger.info(f"Would retry: {task.url} (attempt {task.retries + 1}/{task.max_retries})")

        except Exception as e:
            logger.error(f"Failed download retry failed: {e}")

    def run_forever(self):
        """Run the scheduler continuously."""
        logger.info("OpenDiscourse Download Scheduler started")

        while self.running:
            try:
                # Run pending scheduled tasks
                schedule.run_pending()

                # Sleep for a minute
                time.sleep(60)

            except KeyboardInterrupt:
                logger.info("Scheduler interrupted by user")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(300)  # Wait 5 minutes on error

        logger.info("OpenDiscourse Download Scheduler stopped")


async def main():
    """Main entry point."""
    scheduler = DownloadScheduler()
    await scheduler.initialize()
    scheduler.schedule_downloads()
    scheduler.run_forever()


if __name__ == "__main__":
    # Ensure log directory exists
    Path("/tmp/opendiscourse_logs").mkdir(parents=True, exist_ok=True)

    # Run the scheduler
    asyncio.run(main())
