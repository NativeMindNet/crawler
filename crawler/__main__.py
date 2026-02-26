"""
Universal Single-Platform Crawler - Main Entry Point

Usage:
    python -m crawler <command> [options]

Commands:
    scrape <url>              Scrape and parse a single URL
    api serve                 Start the FastAPI server
    worker run                Start the worker loop
    task add <url>            Add a task to the queue
    task status <id>          Get task status
    task list                 List all tasks
    bulk ingest <file>        Start bulk ingestion
    bulk status <id>          Get bulk job status
    config validate <name>    Validate platform config
    config list               List available platforms
"""

import sys
import asyncio
from pathlib import Path

from crawler.cli import app as cli_app


def main():
    """Main entry point."""
    # Default to help if no arguments
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    # Run CLI
    cli_app()


if __name__ == "__main__":
    main()
