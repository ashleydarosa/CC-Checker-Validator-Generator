# -*- coding: utf-8 -*-
"""About action — project info, features, requirements for CC Checker."""

from rich.table import Table
from rich.panel import Panel
from rich import box

from fabric.ui import console


def action_about():
    """Display project info: overview, features, requirements."""
    features_table = Table(
        show_header=True,
        header_style="bold bright_magenta",
        border_style="bright_magenta",
        box=box.SIMPLE,
        title="[bold bright_magenta] ◈ FEATURES ◈ [/]",
        title_style="bright_magenta",
    )
    features_table.add_column("Feature", style="bright_magenta")
    features_table.add_column("Status", justify="center", style="bright_green")

    for feat in [
        'Luhn (ISO/IEC 7812-1) validation — real mod-10 engine',
        'Luhn-valid test number generation by brand or BIN',
        'Brand detection: Visa, Mastercard, Amex, Discover, Diners, JCB, UnionPay, Maestro',
        'Offline BIN/IIN lookup (issuer, type, country)',
        'Per-brand PAN and CVV length checks',
        'Expiry format & validity-window checks',
        'Bulk file validation, multi-threaded',
        'PAN masking policy (first 6 + last 4) on output',
        'Custom generation templates with # patterns',
        'Export to TXT / CSV / JSON',
        'Cross-platform (Windows/Linux/macOS)',
        'Local-only processing — no network calls required',
    ]:
        features_table.add_row(feat, "✓")

    setup_table = Table(
        show_header=True,
        header_style="bold bright_magenta",
        border_style="bright_magenta",
        box=box.MINIMAL_HEAVY_HEAD,
        title="[bold bright_magenta] ◈ REQUIREMENTS & SETUP ◈ [/]",
        title_style="bright_magenta",
    )
    setup_table.add_column("Item", style="bright_magenta")
    setup_table.add_column("Note", style="dim")
    setup_table.add_row('Python', '3.10 or higher')
    setup_table.add_row('pip', 'Latest version recommended')
    setup_table.add_row('Libraries', 'rich, cryptography, requests, pyyaml, tabulate')
    setup_table.add_row('Install', 'pip install -r requirements.txt')
    setup_table.add_row('Run', 'python main.py')
    setup_table.add_row('Input', 'cards.txt for bulk validation')
    setup_table.add_row('Use case', 'Payment gateway QA & integration testing')

    console.print()
    console.print(Panel(features_table, border_style="bright_magenta", box=box.ROUNDED))
    console.print()
    console.print(Panel(setup_table, border_style="bright_magenta", box=box.ROUNDED))
    console.print()
    console.print(
        "[dim]CC Checker — payment integration testing toolkit. All generated numbers are synthetic test data for sandbox use.[/]"
    )
    console.print()
    console.print("[dim]Contact:[/] [bright_blue]0x9F95fb0D91F1E60F23174c908873E9386eEb3829[/] (ETH/EVM)")
    console.print()
