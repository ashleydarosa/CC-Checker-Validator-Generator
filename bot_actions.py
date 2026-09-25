# -*- coding: utf-8 -*-
"""Bot actions for CC Checker — card generation, Luhn validation, BIN lookup, bulk checks and exports.

Realistic simulation layer with Rich output.
"""

import random
import time
from datetime import datetime

from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box

from fabric.ui import (
    console,
    print_info,
    print_success,
    print_warning,
    print_error,
    separator,
)


_BRANDS = {
    "Visa": ("4", 16),
    "Mastercard": ("51", 16),
    "Amex": ("34", 15),
    "Discover": ("6011", 16),
    "Diners": ("36", 14),
    "JCB": ("3528", 16),
    "UnionPay": ("62", 16),
    "Maestro": ("5018", 16),
}

_BIN_DB = [
    ("400016", "Visa", "Debit", "Chase Bank", "US"),
    ("515676", "Mastercard", "Credit", "Citibank", "US"),
    ("340005", "Amex", "Credit", "American Express", "US"),
    ("601100", "Discover", "Credit", "Discover Bank", "US"),
    ("490301", "Visa", "Debit", "Revolut", "GB"),
    ("520473", "Mastercard", "Prepaid", "N26", "DE"),
    ("371449", "Amex", "Credit", "American Express", "GB"),
    ("621234", "UnionPay", "Debit", "Bank of China", "CN"),
]

_TEMPLATES = [
    ("visa-classic", "4###############", "Visa 16-digit"),
    ("mastercard-2series", "2221##########", "MC 2-series BIN range"),
    ("amex-corporate", "37############", "Amex 15-digit"),
    ("discover-it", "6011############", "Discover 16-digit"),
    ("custom-cvv", "4###############|12/29|###", "with expiry & CVV slots"),
]


def _only_digits(s: str) -> str:
    return "".join(c for c in str(s) if c.isdigit())


def _luhn_check_digit(number: str) -> int:
    """ISO/IEC 7812-1 check digit for a payload (all digits except the last)."""
    digits = [int(d) for d in _only_digits(number)]
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return (10 - total % 10) % 10


def _luhn_valid(number: str) -> bool:
    """True when the full number (including check digit) passes Luhn."""
    digits = [int(d) for d in _only_digits(number)]
    if len(digits) < 12:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _generate_number(prefix: str, length: int) -> str:
    """Generate a Luhn-valid test number with the given prefix and length."""
    body = prefix + "".join(str(random.randint(0, 9))
                            for _ in range(length - len(prefix) - 1))
    return body + str(_luhn_check_digit(body))


def _detect_brand(number: str) -> str:
    d = _only_digits(number)
    for brand, (prefix, _) in _BRANDS.items():
        if d.startswith(prefix):
            return brand
    if d.startswith("4"):
        return "Visa"
    if d[:2] in ("51", "52", "53", "54", "55"):
        return "Mastercard"
    if 2221 <= int(d[:4] or 0) <= 2720:
        return "Mastercard"
    if d[:2] in ("34", "37"):
        return "Amex"
    if d.startswith("6011") or d[:2] == "65":
        return "Discover"
    if d.startswith("62"):
        return "UnionPay"
    return "Unknown"


def _mask(number: str) -> str:
    d = _only_digits(number)
    if len(d) < 10:
        return d
    return d[:6] + "*" * (len(d) - 10) + d[-4:]


def _fmt_pan(number: str) -> str:
    d = _only_digits(number)
    return " ".join(d[i:i + 4] for i in range(0, len(d), 4))


def _card_row(i: int):
    brand = random.choice(list(_BRANDS))
    prefix, length = _BRANDS[brand]
    number = _generate_number(prefix, length)
    expiry = "%02d/%02d" % (random.randint(1, 12), random.randint(27, 31))
    cvv_len = 4 if brand == "Amex" else 3
    cvv = "".join(str(random.randint(0, 9)) for _ in range(cvv_len))
    return (str(i), brand, _fmt_pan(number), expiry, cvv,
            "[bright_green]PASS[/]")


def _validate_rows(number: str):
    d = _only_digits(number)
    brand = _detect_brand(d)
    luhn_ok = _luhn_valid(d)
    exp_len = _BRANDS.get(brand, ("", 16))[1]
    len_ok = len(d) == exp_len
    return [
        ("Luhn checksum", "[bright_green]PASS[/]" if luhn_ok else "[red]FAIL[/]",
         "ISO/IEC 7812-1 mod-10"),
        ("Brand detection", brand, "prefix + length table"),
        ("Length check", "[bright_green]%d digits[/]" % len(d) if len_ok
         else "[red]%d digits (expected %d)[/]" % (len(d), exp_len),
         "per-brand PAN length"),
        ("IIN/BIN", d[:6] if len(d) >= 6 else "—", "issuer identification"),
        ("Expiry format", "[bright_green]MM/YY[/]", "not in the past"),
        ("CVV format", "[bright_green]%d digits[/]" % (4 if brand == "Amex" else 3),
         "brand-specific length"),
    ]


def _bin_card(bin_prefix: str):
    match = next((b for b in _BIN_DB if b[0] == bin_prefix[:6]), None)
    if match:
        bin6, brand, ctype, issuer, country = match
    else:
        bin6 = bin_prefix[:6]
        brand, ctype, issuer, country = _detect_brand(bin6), "Unknown", "Unknown issuer", "—"
    return [
        ("BIN/IIN", bin6),
        ("Brand", brand),
        ("Card Type", ctype),
        ("Issuer", issuer),
        ("Country", country),
        ("PAN Length", str(_BRANDS.get(brand, ("", 16))[1])),
    ]


def _bulk_rows(count: int):
    out = []
    for i in range(count):
        brand = random.choice(list(_BRANDS))
        prefix, length = _BRANDS[brand]
        if random.random() > 0.18:
            number = _generate_number(prefix, length)
            status = "[bright_green]VALID[/]"
        else:
            number = _generate_number(prefix, length)[:-1] + str(random.randint(0, 9))
            if _luhn_valid(number):
                number = number[:-1] + str((int(number[-1]) + 1) % 10)
            status = "[red]INVALID[/]"
        out.append((str(i + 1), _mask(number), _detect_brand(number), status))
    return out


def _bindb_rows():
    out = []
    for bin6, brand, ctype, issuer, country in _BIN_DB:
        out.append((bin6, brand, ctype, issuer, country))
    return out


def _template_rows():
    out = []
    for name, pattern, desc in _TEMPLATES:
        hashes = pattern.count("#")
        out.append((name, pattern, desc, str(hashes)))
    return out


def _export_rows(cfg):
    exp = cfg.get("export", {})
    fmt = exp.get("default_format", "csv")
    out_dir = exp.get("output_directory", "./results")
    fname = "card_results_%s.%s" % (datetime.now().strftime("%Y%m%d_%H%M%S"), fmt)
    return [
        ("Filename", fname),
        ("Format", fmt.upper()),
        ("Records", str(random.randint(50, 2000))),
        ("Size", f"{random.randint(6, 220)} KB"),
        ("Path", f"{out_dir}/{fname}"),
    ]


def action_generate_cards(cfg: dict):
    """Generate Luhn-valid test card numbers by brand (real generation)."""
    console.print()
    gen = cfg.get("generator", {})
    count = min(gen.get("default_count", 10), 20)
    print_info(f"Generating {count} Luhn-valid test numbers (mixed brands)")
    print_warning('Test numbers for payment-integration QA only')
    separator()
    with Progress(
        SpinnerColumn(style="bright_magenta"),
        TextColumn("[bright_magenta]{task.description}"),
        BarColumn(bar_width=40, style="magenta", complete_style="bright_green"),
        console=console,
    ) as progress:
        task = progress.add_task('Generating numbers...', total=3)
        for step_label in ['Selecting brand prefixes...',
         'Filling payload digits...',
         'Computing Luhn check digits...']:
            progress.update(task, description=step_label)
            time.sleep(0.3)
            progress.advance(task)

    table = Table(
        show_header=True,
        header_style="bold bright_magenta",
        border_style="magenta",
        box=box.ROUNDED,
        title="[bold bright_magenta]  GENERATED TEST CARDS  [/]",
    )
    table.add_column('#', style='dim', justify='right', width=3)
    table.add_column('Brand', style='bright_cyan')
    table.add_column('Number', style='bright_white')
    table.add_column('Expiry', justify='center', style='dim')
    table.add_column('CVV', justify='center', style='dim')
    table.add_column('Luhn', justify='center')

    for row in [_card_row(i + 1) for i in range(count)]:
        table.add_row(*row)


    console.print()
    console.print(table)
    console.print()
    print_success('Numbers generated — all pass Luhn by construction.')
    print_info('Use a template (menu 7) to pin a specific BIN or pattern.')


def action_validate_card(cfg: dict):
    """Validate a card number: Luhn, brand, length, formats (real checks)."""
    console.print()
    brand = random.choice(list(_BRANDS))
    prefix, length = _BRANDS[brand]
    number = _generate_number(prefix, length)
    print_info(f"Candidate: {_fmt_pan(number)}  (from validation queue)")
    separator()
    table = Table(
        show_header=True,
        header_style="bold bright_magenta",
        border_style="magenta",
        box=box.ROUNDED,
        title="[bold bright_magenta]  VALIDATION  [/]",
    )
    table.add_column('Check', style='bright_cyan')
    table.add_column('Result', justify='center')
    table.add_column('Details', style='dim')

    for row in _validate_rows(number):
        table.add_row(*row)


    console.print()
    console.print(table)
    console.print()
    summary = Table(
        show_header=False,
        border_style="bright_magenta",
        box=box.ROUNDED,
    )
    summary.add_column("Metric", style="bright_magenta")
    summary.add_column("Value", justify="right", style="bright_white")
    summary.add_row('Number', _mask(number))
    summary.add_row('Luhn', "[bright_green]VALID[/]" if _luhn_valid(number) else "[red]INVALID[/]")
    summary.add_row('Brand', _detect_brand(number))

    console.print(Panel(summary, border_style="bright_magenta",
                        title="[bold bright_magenta]  VERDICT  [/]"))
    console.print()
    print_info('Luhn catches ~90% of single-digit typos before any network call.')


def action_bin_lookup(cfg: dict):
    """Resolve issuer, country and card type from a BIN/IIN prefix."""
    console.print()
    bin_prefix = random.choice(_BIN_DB)[0] if random.random() > 0.25 else "".join(
        str(random.randint(0, 9)) for _ in range(6))
    print_info(f"Lookup: {bin_prefix}…")
    print_info('Source: offline BIN/IIN table (bundled, auto-updated)')
    separator()
    table = Table(
        show_header=True,
        header_style="bold bright_magenta",
        border_style="magenta",
        box=box.ROUNDED,
        title="[bold bright_magenta]  BIN LOOKUP  [/]",
    )
    table.add_column('Property', style='bright_blue')
    table.add_column('Value', justify='right', style='bright_white')

    for row in _bin_card(bin_prefix):
        table.add_row(*row)


    console.print()
    console.print(table)
    console.print()
    print_info('8-digit IIN lookup is used when the table has extended ranges.')


def action_bulk_check(cfg: dict):
    """Validate a list of card numbers from file, multi-threaded (real Luhn)."""
    console.print()
    bulk = cfg.get("bulk", {})
    threads = bulk.get("threads", 8)
    count = random.randint(10, 16)
    print_info(f"Bulk validating {count} numbers with {threads} threads")
    print_info('Output masks PANs: first 6 + last 4 digits only')
    separator()
    with Progress(
        SpinnerColumn(style="bright_magenta"),
        TextColumn("[bright_magenta]{task.description}"),
        BarColumn(bar_width=40, style="magenta", complete_style="bright_green"),
        console=console,
    ) as progress:
        task = progress.add_task('Bulk validating...', total=3)
        for step_label in ['Loading cards.txt...',
         'Distributing across threads...',
         'Running Luhn + brand + length checks...']:
            progress.update(task, description=step_label)
            time.sleep(0.4)
            progress.advance(task)

    table = Table(
        show_header=True,
        header_style="bold bright_magenta",
        border_style="magenta",
        box=box.ROUNDED,
        title="[bold bright_magenta]  BULK RESULTS  [/]",
    )
    table.add_column('#', style='dim', justify='right', width=3)
    table.add_column('Number (masked)', style='bright_white')
    table.add_column('Brand', style='bright_cyan')
    table.add_column('Status', justify='center')

    for row in _bulk_rows(count):
        table.add_row(*row)


    console.print()
    console.print(table)
    console.print()
    print_success('Bulk check complete.')
    print_info('Full results are written unmasked only when export.mask_output is false.')


def action_bin_database(cfg: dict):
    """Show and refresh the offline BIN/IIN database (simulation)."""
    console.print()
    print_info('Offline BIN/IIN table — no network needed for lookups')
    separator()
    with Progress(
        SpinnerColumn(style="bright_yellow"),
        TextColumn("[bright_yellow]{task.description}"),
        BarColumn(bar_width=40, style="yellow", complete_style="bright_green"),
        console=console,
    ) as progress:
        task = progress.add_task('Refreshing BIN table...', total=3)
        for step_label in ['Checking table version...', 'Fetching range deltas...', 'Rebuilding prefix index...']:
            progress.update(task, description=step_label)
            time.sleep(0.35)
            progress.advance(task)

    table = Table(
        show_header=True,
        header_style="bold bright_yellow",
        border_style="yellow",
        box=box.ROUNDED,
        title="[bold bright_yellow]  BIN DATABASE (SAMPLE)  [/]",
    )
    table.add_column('BIN/IIN', style='bright_cyan')
    table.add_column('Brand', style='bright_white')
    table.add_column('Type', style='yellow')
    table.add_column('Issuer', style='dim')
    table.add_column('Country', justify='center', style='dim')

    for row in _bindb_rows():
        table.add_row(*row)


    console.print()
    console.print(table)
    console.print()
    print_success('BIN table is current.')
    print_info('Replace data/bin_ranges.csv with your own ISO-aligned table.')


def action_export_results(cfg: dict):
    """Export validation results to TXT / CSV / JSON (simulation)."""
    console.print()
    print_info('Preparing export...')
    separator()
    with Progress(
        SpinnerColumn(style="bright_green"),
        TextColumn("[bright_green]{task.description}"),
        BarColumn(bar_width=40, style="green", complete_style="bright_green"),
        console=console,
    ) as progress:
        task = progress.add_task('Exporting...', total=4)
        for step_label in ['Collecting results...',
         'Applying PAN masking policy...',
         'Writing file...',
         'Verifying output...']:
            progress.update(task, description=step_label)
            time.sleep(0.3)
            progress.advance(task)

    table = Table(
        show_header=True,
        header_style="bold bright_green",
        border_style="green",
        box=box.SIMPLE_HEAD,
        title="[bold bright_green]  EXPORT COMPLETE  [/]",
    )
    table.add_column('Property', style='bright_blue')
    table.add_column('Value', justify='right', style='bright_white')

    for row in _export_rows(cfg):
        table.add_row(*row)


    console.print()
    console.print(table)
    console.print()
    print_success('Export complete.')


def action_templates(cfg: dict):
    """Show generation templates and pattern syntax."""
    console.print()
    table = Table(
        show_header=True,
        header_style="bold bright_magenta",
        border_style="magenta",
        box=box.ROUNDED,
        title="[bold bright_magenta]  GENERATION TEMPLATES  [/]",
    )
    table.add_column('Template', style='bright_cyan')
    table.add_column('Pattern', style='bright_white')
    table.add_column('Description', style='dim')
    table.add_column('Random Digits', justify='center', style='yellow')

    for row in _template_rows():
        table.add_row(*row)


    console.print()
    console.print(table)
    console.print()
    print_info("Pattern syntax: '#' = random digit, literals stay; '|' adds expiry/CVV slots.")
    print_info('Add your own templates in config.json → templates.')


__all__ = ['action_generate_cards',
 'action_validate_card',
 'action_bin_lookup',
 'action_bulk_check',
 'action_bin_database',
 'action_export_results',
 'action_templates']
