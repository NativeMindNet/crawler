"""CLI application using Typer."""

import typer
from typing import Optional
from pathlib import Path

app = typer.Typer(
    name="crawler",
    help="Universal Single-Platform Crawler CLI",
    add_completion=False,
)


@app.command("scrape")
def scrape(
    url: str = typer.Argument(..., help="URL to scrape"),
    platform: str = typer.Option(..., "--platform", "-p", help="Platform name"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    parse: bool = typer.Option(True, "--parse/--no-parse", help="Parse after scraping"),
):
    """Scrape and optionally parse a single URL."""
    from crawler.cli.commands.scrape import scrape_command
    asyncio.run(scrape_command(url, platform, output, parse))


@app.command("health")
def health(
    api_url: str = typer.Option("http://localhost:8000", "--api-url", "-u", help="API URL"),
):
    """Check crawler health."""
    from crawler.cli.commands.health import health_command
    asyncio.run(health_command(api_url))


# Task commands
task_app = typer.Typer()
app.add_typer(task_app, name="task")


@task_app.command("add")
def task_add(
    url: str = typer.Argument(..., help="URL to add"),
    platform: str = typer.Option(..., "--platform", "-p", help="Platform name"),
    priority: int = typer.Option(0, "--priority", help="Task priority"),
):
    """Add a task to the queue."""
    from crawler.cli.commands.task import task_add_command
    asyncio.run(task_add_command(url, platform, priority))


@task_app.command("status")
def task_status(
    task_id: str = typer.Argument(..., help="Task ID"),
    db_path: str = typer.Option("/data/state/crawler.db", "--db-path", help="Database path"),
):
    """Get task status."""
    from crawler.cli.commands.task import task_status_command
    asyncio.run(task_status_command(task_id, db_path))


@task_app.command("list")
def task_list(
    platform: Optional[str] = typer.Option(None, "--platform", "-p", help="Filter by platform"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    limit: int = typer.Option(50, "--limit", "-l", help="Max tasks to show"),
    db_path: str = typer.Option("/data/state/crawler.db", "--db-path", help="Database path"),
):
    """List all tasks."""
    from crawler.cli.commands.task import task_list_command
    asyncio.run(task_list_command(platform, status, limit, db_path))


# Worker commands
worker_app = typer.Typer()
app.add_typer(worker_app, name="worker")


@worker_app.command("run")
def worker_run(
    platform: str = typer.Option(..., "--platform", "-p", help="Platform name"),
    db_path: str = typer.Option("/data/state/crawler.db", "--db-path", help="Database path"),
    data_dir: str = typer.Option("/data", "--data-dir", help="Data directory"),
    config_dir: str = typer.Option("/config", "--config-dir", help="Config directory"),
    max_retries: int = typer.Option(3, "--max-retries", help="Max retries per task"),
):
    """Start processing the task queue."""
    from crawler.cli.commands.worker import worker_run_command
    asyncio.run(worker_run_command(platform, db_path, data_dir, config_dir, max_retries))


@worker_app.command("resume")
def worker_resume(
    platform: str = typer.Option(..., "--platform", "-p", help="Platform name"),
    db_path: str = typer.Option("/data/state/crawler.db", "--db-path", help="Database path"),
    data_dir: str = typer.Option("/data", "--data-dir", help="Data directory"),
    config_dir: str = typer.Option("/config", "--config-dir", help="Config directory"),
):
    """Resume processing from last checkpoint."""
    from crawler.cli.commands.worker import worker_resume_command
    asyncio.run(worker_resume_command(platform, db_path, data_dir, config_dir))


@worker_app.command("drain")
def worker_drain(
    platform: str = typer.Option(..., "--platform", "-p", help="Platform name"),
    db_path: str = typer.Option("/data/state/crawler.db", "--db-path", help="Database path"),
    data_dir: str = typer.Option("/data", "--data-dir", help="Data directory"),
    config_dir: str = typer.Option("/config", "--config-dir", help="Config directory"),
):
    """Process all pending tasks and exit."""
    from crawler.cli.commands.worker import worker_drain_command
    asyncio.run(worker_drain_command(platform, db_path, data_dir, config_dir))


# Bulk commands
bulk_app = typer.Typer()
app.add_typer(bulk_app, name="bulk")


@bulk_app.command("ingest")
def bulk_ingest(
    file: Path = typer.Argument(..., help="File to ingest (CSV/GIS/JSON)"),
    profile: str = typer.Option(..., "--profile", help="Mapping profile name"),
    platform: str = typer.Option(..., "--platform", "-p", help="Platform name"),
):
    """Start bulk ingestion."""
    from crawler.cli.commands.bulk import bulk_ingest_command
    asyncio.run(bulk_ingest_command(file, profile, platform))


@bulk_app.command("status")
def bulk_status(
    job_id: str = typer.Argument(..., help="Job ID"),
    db_path: str = typer.Option("/data/state/crawler.db", "--db-path", help="Database path"),
):
    """Get bulk job status."""
    from crawler.cli.commands.bulk import bulk_status_command
    asyncio.run(bulk_status_command(job_id, db_path))


# Config commands
config_app = typer.Typer()
app.add_typer(config_app, name="config")


@config_app.command("validate")
def config_validate(
    platform: str = typer.Argument(..., help="Platform name to validate"),
    config_dir: str = typer.Option("/config", "--config-dir", help="Config directory"),
):
    """Validate platform configuration."""
    from crawler.cli.commands.config import config_validate_command
    config_validate_command(platform, config_dir)


@config_app.command("list")
def config_list(
    config_dir: str = typer.Option("/config", "--config-dir", help="Config directory"),
):
    """List available platform configurations."""
    from crawler.cli.commands.config import config_list_command
    config_list_command(config_dir)


if __name__ == "__main__":
    app()
