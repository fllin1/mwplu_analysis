#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bulk Runner CLI
A user-friendly command-line interface for running PLU processing pipelines in bulk.

Usage:
    python bulk_runner.py --help
    python bulk_runner.py status
    python bulk_runner.py run --stages ocr --stages synthesis --cities grenoble --cities nantes
    python bulk_runner.py run --stages upload_supabase --cities all
    python bulk_runner.py run --all-stages --dry-run

Version: 1.0
Date: 2025-05-28
Author: Grey Panda
"""

import subprocess
import sys
from typing import List

import typer
from loguru import logger
from rich.console import Console
from rich.table import Table

from src.mwplu.bulk_processor import BulkProcessor, PipelineStage

app = typer.Typer(
    name="bulk_runner",
    help="Bulk PLU processing pipeline runner",
    pretty_exceptions_enable=False,
)
console = Console()


@app.command()
def status(
    refresh: bool = typer.Option(  # pylint: disable=redefined-outer-name
        False,
        "--refresh",
        "-r",
        help="Refresh YAML configurations before showing status",
    )
):
    """Show the current status of data across pipeline stages."""

    if refresh:
        console.print("[yellow]Refreshing configuration files...[/yellow]")
        try:
            subprocess.run(
                ["python", "config/generate_plu_configs.py"],
                capture_output=True,
                text=True,
                check=True,
            )
            console.print("[green]✓ Configurations updated[/green]\n")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error updating configs: {e}[/red]")
            return

    processor = BulkProcessor()

    status_data = processor.get_pipeline_status()
    cities = processor.get_available_cities()

    console.print("\n[bold blue]PLU Pipeline Status[/bold blue]")
    console.print(f"Available cities: {', '.join(sorted(cities))}\n")

    # Create a table showing file counts per stage per city
    table = Table(title="File Counts by Stage and City")
    table.add_column("City", style="cyan", no_wrap=True)
    table.add_column("External", justify="right")
    table.add_column("Raw", justify="right")
    table.add_column("Interim", justify="right")
    table.add_column("Processed", justify="right")

    for city in sorted(cities):
        external_count = status_data.get("external", {}).get(city, 0)
        raw_count = status_data.get("raw", {}).get(city, 0)
        interim_count = status_data.get("interim", {}).get(city, 0)
        processed_count = status_data.get("processed", {}).get(city, 0)

        table.add_row(
            city,
            str(external_count) if external_count > 0 else "-",
            str(raw_count) if raw_count > 0 else "-",
            str(interim_count) if interim_count > 0 else "-",
            str(processed_count) if processed_count > 0 else "-",
        )

    console.print(table)

    if not refresh:
        console.print(
            "\n[dim]💡 Tip: Use --refresh to update file counts if you've made manual changes[/dim]"
        )


@app.command()
def run(
    stages: List[str] = typer.Option(
        None,
        "--stages",
        "-s",
        help="Pipeline stages to run (ocr, extract_pages, synthesis, upload_supabase)",
    ),
    cities: List[str] = typer.Option(
        None, "--cities", "-c", help="Cities to process (or 'all' for all cities)"
    ),
    all_stages: bool = typer.Option(
        False, "--all-stages", help="Run all pipeline stages"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be executed without running"
    ),
    force: bool = typer.Option(
        False, "--force", help="Force execution without confirmation"
    ),
):
    """Run bulk processing for specified stages and cities."""

    processor = BulkProcessor()
    available_cities = processor.get_available_cities()

    # Validate and convert stages
    if all_stages:
        pipeline_stages = list(PipelineStage)
    elif stages:
        pipeline_stages = []
        for stage in stages:
            try:
                pipeline_stages.append(PipelineStage(stage))
            except ValueError:
                console.print(f"[red]Error:[/red] Invalid stage '{stage}'")
                console.print(
                    f"Valid stages: {', '.join([s.value for s in PipelineStage])}"
                )
                sys.exit(1)
    else:
        console.print("[red]Error:[/red] Must specify --stages or --all-stages")
        sys.exit(1)

    # Validate cities
    if cities and "all" not in cities:
        invalid_cities = set(cities) - available_cities
        if invalid_cities:
            console.print(
                f"[red]Error:[/red] Invalid cities: {', '.join(invalid_cities)}"
            )
            console.print(f"Available cities: {', '.join(sorted(available_cities))}")
            sys.exit(1)

    # Show what will be executed
    console.print("\n[bold]Pipeline Configuration:[/bold]")
    console.print(f"Stages: {', '.join([s.value for s in pipeline_stages])}")
    if cities:
        if "all" in cities:
            console.print(f"Cities: all ({', '.join(sorted(available_cities))})")
        else:
            console.print(f"Cities: {', '.join(cities)}")
    else:
        console.print(f"Cities: all ({', '.join(sorted(available_cities))})")

    # Confirmation prompt
    if not dry_run and not force:
        confirmed = typer.confirm("\nDo you want to proceed?")
        if not confirmed:
            console.print("Operation cancelled.")
            sys.exit(0)

    # Execute the pipeline
    console.print(
        f"\n[bold green]{'DRY RUN - ' if dry_run else ''}Starting bulk processing...[/bold green]"
    )

    try:
        results = processor.run_pipeline_stages(
            stages=pipeline_stages,
            cities=cities if cities and "all" not in cities else None,
            dry_run=dry_run,
        )

        if dry_run:
            console.print("\n[bold]Dry Run Results:[/bold]")
            console.print(
                f"Total tasks that would be executed: {results['total_tasks']}"
            )
        else:
            console.print("\n[bold]Execution Results:[/bold]")
            console.print(f"Total tasks: {results['total']}")
            console.print(f"[green]Successful: {results['successful']}[/green]")
            if results["failed"] > 0:
                console.print(f"[red]Failed: {results['failed']}[/red]")

            if results["failed"] == 0:
                console.print(
                    "\n[bold green]✅ All tasks completed successfully![/bold green]"
                )
            else:
                console.print(
                    "\n[bold yellow]⚠️  Some tasks failed. Check logs for details.[/bold yellow]"
                )

    except Exception as e:  # pylint: disable=broad-exception-caught
        console.print(f"[red]Error during execution: {e}[/red]")
        logger.exception("Bulk processing failed")
        sys.exit(1)


@app.command()
def list_stages():
    """List all available pipeline stages."""
    console.print("\n[bold]Available Pipeline Stages:[/bold]")
    for stage in PipelineStage:
        console.print(f"  • {stage.value}")


@app.command()
def list_cities():
    """List all available cities."""
    processor = BulkProcessor()
    cities = processor.get_available_cities()

    console.print("\n[bold]Available Cities:[/bold]")
    for city in sorted(cities):
        console.print(f"  • {city}")


@app.command()
def upload_all():
    """Quick command to upload all processed data to Supabase."""
    processor = BulkProcessor()

    console.print(
        "\n[bold blue]Uploading all processed data to Supabase...[/bold blue]"
    )

    confirmed = typer.confirm("This will upload all processed JSON files. Continue?")
    if not confirmed:
        console.print("Operation cancelled.")
        return

    try:
        results = processor.run_pipeline_stages(
            stages=[PipelineStage.UPLOAD_SUPABASE], cities=["all"]
        )

        console.print("\n[bold]Upload Results:[/bold]")
        console.print(f"Total upload tasks: {results['total']}")
        console.print(f"[green]Successful: {results['successful']}[/green]")
        if results["failed"] > 0:
            console.print(f"[red]Failed: {results['failed']}[/red]")

    except Exception as e:  # pylint: disable=broad-exception-caught
        console.print(f"[red]Error during upload: {e}[/red]")
        logger.exception("Upload failed")


@app.command()
def refresh():
    """Refresh YAML configuration files to reflect current directory state."""
    console.print("\n[bold blue]Refreshing PLU Configuration Files[/bold blue]")
    console.print("Scanning directories and updating YAML files...\n")

    try:
        subprocess.run(
            ["python", "config/generate_plu_configs.py"],
            capture_output=True,
            text=True,
            check=True,
        )
        console.print("[green]✅ Configuration files successfully updated![/green]")
        console.print(
            "\n[dim]You can now run 'python bulk_runner.py status' to see updated \
            file counts.[/dim]"
        )
    except subprocess.CalledProcessError as e:
        console.print("[red]❌ Error updating configuration files:[/red]")
        console.print(f"[red]{e.stderr}[/red]")
        logger.exception("Failed to refresh configurations")


if __name__ == "__main__":
    app()
