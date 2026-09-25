# -*- coding: utf-8 -*-
"""Settings action — configuration overview for CC Checker."""

from pathlib import Path

from rich.table import Table
from rich.panel import Panel
from rich import box

from fabric.ui import console, print_info, print_warning


def action_settings():
    """Display setup instructions: config.json sections and examples."""
    table = Table(
        show_header=True,
        header_style="bold bright_magenta",
        border_style="bright_magenta",
        box=box.ROUNDED,
        title="[bold bright_magenta] ◈ CONFIGURATION ◈ [/]",
        title_style="bright_magenta",
    )
    table.add_column("Setting", style="bright_magenta")
    table.add_column("Description", style="dim")
    table.add_column("Example", style="bright_black")

    table.add_row('generator.default_brand', 'Brand for quick generation', 'visa / mastercard / amex')
    table.add_row('generator.default_count', 'Numbers per batch', '10')
    table.add_row('generator.bin', 'Pin a specific BIN prefix', '"400016"')
    table.add_row('validator.luhn_check', 'ISO/IEC 7812-1 mod-10', 'true')
    table.add_row('validator.mask_output', 'Mask PANs in output', 'true')
    table.add_row('bin_database.path', 'Offline BIN/IIN table', 'data/bin_ranges.csv')
    table.add_row('bulk.threads', 'Parallel validation threads', '8')
    table.add_row('bulk.input_file', 'Bulk input list', 'cards.txt')
    table.add_row('export.default_format', 'Export format', 'csv / txt / json')

    panel = Panel(
        table,
        title="[bold bright_magenta] CC Checker Settings [/]",
        border_style="bright_magenta",
        box=box.DOUBLE,
    )

    console.print()
    console.print(panel)

    base_dir = Path(__file__).parent.parent
    config_path = base_dir / "config.json"

    console.print()
    console.print("[dim]Configuration files:[/]")
    console.print(f"  [bright_magenta]config.json[/]  → {config_path}")
    console.print()
    print_info('Generated numbers are synthetic and pass only Luhn — they hold no value.')
    print_info('Keep validator.mask_output enabled when sharing screenshots or logs.')
    print_warning("Keep API keys and secrets secure. Never commit config.json to version control.")
    print_info("Edit config files with any text editor (e.g. VS Code, Notepad).")
