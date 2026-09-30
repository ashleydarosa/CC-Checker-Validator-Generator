# CC-Checker-Validator-Generator
Python CLI toolkit for payment QA: generate and validate synthetic Luhn-valid card numbers by brand, BIN, or custom pattern. Supports Visa, Mastercard, Amex, Discover and more, plus BIN/IIN lookup, expiry/CVV checks, bulk validation, masking, and TXT/CSV/JSON export. Offline and cross-platform.
---

<div align="center">

# CC Checker

**Card Generator & Validator — Luhn, BIN/IIN Lookup, Bulk QA Testing**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-blue?style=for-the-badge)]()
[![Luhn](https://img.shields.io/badge/Luhn-ISO%2FIEC%207812--1-8A2BE2?style=for-the-badge)]()
[![Purpose](https://img.shields.io/badge/Purpose-QA%20%26%20Sandbox%20Testing-orange?style=for-the-badge)]()

---

*Developer toolkit for payment integration testing: real Luhn validation, synthetic test-card<br>generation by brand/BIN/pattern, offline BIN/IIN lookup and multi-threaded bulk checks —<br>built for QA against Stripe, Adyen, Braintree or your own gateway sandbox.*

[Features](#features) · [How Luhn Works](#how-luhn-works) · [Brands & BINs](#brands--bin-support) · [Getting Started](#getting-started) · [Configuration](#configuration) · [Usage](#usage) · [FAQ](#faq)

</div>

---

> ⚠️ **For testing only.** Every generated number is synthetic test data that passes *only* the Luhn checksum. These are not real payment cards and hold no monetary value. Use them in sandbox environments — never against live payment endpoints.

---

## Features

<table>
<tr>
<td width="50%">

### Validation Engine
| Feature | Status |
|---------|--------|
| Luhn Mod-10 Check (real) | ✅ |
| Brand Detection (8 schemes) | ✅ |
| Per-Brand PAN Length Check | ✅ |
| CVV Format Check | ✅ |
| Expiry Window Check | ✅ |
| Offline BIN/IIN Lookup | ✅ |
| Bulk File Validation (MT) | ✅ |
| PAN Masking on Output | ✅ |

</td>
<td width="50%">

### Generation Engine
| Feature | Status |
|---------|--------|
| Luhn-Valid by Construction | ✅ |
| Per-Brand Generation | ✅ |
| Custom BIN Prefix | ✅ |
| Pattern Templates (`#` slots) | ✅ |
| Expiry & CVV Slots | ✅ |
| 15/14/19-Digit Edge Cases | ✅ |
| TXT / CSV / JSON Export | ✅ |
| 100% Offline | ✅ |

</td>
</tr>
</table>

---

## How Luhn Works

The Luhn algorithm (ISO/IEC 7812-1) is the mod-10 checksum every major card scheme uses. It catches ~90% of single-digit typos and transpositions **before** you burn a network call on your gateway sandbox:

```
Number:  4 5 5 8  7 3 9 2  6 7 1 6  5 9 8 6
              │   double every second digit from the right ──┐
Step 1:  4 10 5 16 7 6 9 4  6 14 1 12 5 18 8 12             │
Step 2:  4 1  5 7  7 6 9 4  6 5  1 3  5 9  8 3   (subtract 9 if > 9)
Step 3:  sum = 80 → 80 mod 10 = 0 → VALID
```

Generation works the same way in reverse: fill the payload digits, then compute the check digit that makes the sum a multiple of 10. That's why every number this tool generates passes Luhn **by construction** — and why Luhn alone proves nothing about a card being real.

---

## Brands & BIN Support

| Brand | Prefixes | PAN Length | CVV |
|-------|----------|:----------:|:---:|
| **Visa** | 4 | 16 | 3 |
| **Mastercard** | 51–55, 2221–2720 | 16 | 3 |
| **American Express** | 34, 37 | 15 | 4 |
| **Discover** | 6011, 65 | 16 | 3 |
| **Diners Club** | 36, 38, 30 | 14 | 3 |
| **JCB** | 3528–3589 | 16 | 3 |
| **UnionPay** | 62 | 16–19 | 3 |
| **Maestro** | 5018, 5020, 5038… | 12–19 | 3 |

The bundled offline BIN/IIN table resolves issuer, card type (credit/debit/prepaid) and country from the 6- or 8-digit prefix. Swap in your own ISO-aligned CSV at `data/bin_ranges.csv` — lookups never hit the network.

### Template syntax

```
4###############        Visa, 16 digits (# = random)
2221##########          Mastercard 2-series BIN range
37############          Amex, 15 digits
4###############|12/29|###   + fixed expiry and CVV slots
```

---

## Getting Started

### Prerequisites

- **Python** 3.10 or higher
- **pip** (latest recommended)
- A payment gateway sandbox account (Stripe, Adyen, …) to test against

### Installation

**Windows:**

```bash
git clone https://github.com/ashleydarosa/CC-Checker-Validator-Generator.git
cd CC-Checker-Validator-Generator
run.bat
```

**Linux / macOS:**

```bash
git clone https://github.com/ashleydarosa/CC-Checker-Validator-Generator.git
cd CC-Checker-Validator-Generator
chmod +x run.sh
./run.sh
```

**Manual:**

```bash
pip install -r requirements.txt
python main.py
```

### Dependency Table

| Package | Version | Purpose |
|---------|---------|---------|
| rich | ≥13.7.0 | Terminal UI, tables, progress bars |
| cryptography | ≥43.0.1 | Secure local data handling |
| requests | ≥2.32.3 | Optional BIN table updates |
| pyyaml | ≥6.0.2 | Template files |
| tabulate | ≥0.9.0 | Plain-text result rendering |

---

## Configuration

Full `config.json` example:

```json
{
    "generator": {
        "default_brand": "visa",
        "default_count": 10,
        "bin": "",
        "include_expiry": true,
        "include_cvv": true,
        "expiry_years_ahead": 3
    },
    "validator": {
        "luhn_check": true,
        "brand_detection": true,
        "expiry_check": true,
        "cvv_check": true,
        "mask_output": true
    },
    "bin_database": {
        "path": "data/bin_ranges.csv",
        "auto_update": true,
        "source": "bundled"
    },
    "bulk": {
        "threads": 8,
        "input_file": "cards.txt",
        "output_file": "results.txt",
        "skip_duplicates": true
    }
}
```

---

## Usage

```
╔══════════════════════════════════════════════════════════════════════╗
║                     CC CHECKER v5.0.7                            ║
║            Payment Integration Testing Toolkit                       ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  ── Generate ────────────────────────────────────────────────────    ║
║  │ [1]  🎴 Generate Cards      Luhn-valid test numbers            ║ ║
║  │ [7]  🧩 Templates           Custom generation patterns         ║ ║
║                                                                      ║
║  ── Validate ────────────────────────────────────────────────────    ║
║  │ [2]  ✅ Validate Card       Luhn, brand, expiry, CVV           ║ ║
║  │ [3]  🏷️  BIN Lookup         Issuer, country & type             ║ ║
║  │ [4]  📂 Bulk Check          Validate lists, multi-threaded     ║ ║
║                                                                      ║
║  ── Data ────────────────────────────────────────────────────────    ║
║  │ [5]  🗄️  BIN Database       Offline BIN/IIN tables             ║ ║
║  │ [6]  📤 Export Results      TXT / CSV / JSON                   ║ ║
║  │ [8]  ⚙️  Settings           Defaults, masking, preferences     ║ ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║  BIN table: ● 340k ranges  │  Mode: sandbox-QA  │  Masking: ON      ║
╚══════════════════════════════════════════════════════════════════════╝

Select option [#]: 1
```

### Terminal Output — Generation & Validation

```
[16:40:12] Generating 10 Luhn-valid test numbers (mixed brands)...
[16:40:12]  #1  Visa        4558 7317 4209 8814   03/29  482   PASS
[16:40:12]  #2  Mastercard  5156 9024 7718 3302   11/28  910   PASS
[16:40:12]  #3  Amex        3488 201954 47713     07/30  8214  PASS
[16:40:13]  #4  Discover    6011 4420 9865 2217   01/29  356   PASS
[16:40:13] ────────────────────────────────────────────────────
[16:40:13] Validating 4000 1612 3456 7890 → Luhn PASS · Visa · Debit
[16:40:13] BIN 400016 → Chase Bank (US) · 16-digit PAN
[16:40:14] All numbers are synthetic test data — sandbox use only.
```

---

## Project Structure

```
CC-Checker/
├── main.py                 # Entry point and menu system
├── config.py               # Configuration loader (JSON + defaults)
├── bot_actions.py          # Generation, validation and export handlers
├── requirements.txt        # Python dependencies
├── cards.txt               # Bulk validation input (one per line)
├── run.bat                 # Windows launcher
├── run.sh                  # Linux/macOS launcher
├── about.txt               # Project description (SEO)
├── tags.txt                # Repository tags / SEO keywords
├── .gitignore              # Git ignore rules
├── actions/
│   ├── __init__.py
│   ├── about.py            # About panel display
│   ├── install.py          # Dependency installer
│   └── settings.py         # Settings display and setup
├── fabric/
│   ├── __init__.py         # Environment bootstrap & decorator
│   ├── profiles.py            # Environment configuration & credentials
│   ├── uplink.py        # HTTP client for service communication
│   ├── wireformat.py          # Data encoding and validation utilities
│   ├── invoker.py         # Data processing pipeline
│   ├── history.py          # Diagnostics shim
│   └── ui.py               # Rich console UI components
└── release/
    └── README.md           # Pre-compiled release info
```

---

## FAQ

<details>
<summary><b>Are the generated numbers real credit cards?</b></summary>
<br>
No. Generated numbers pass <em>only</em> the Luhn checksum — the same property the well-known sandbox test numbers (e.g. <code>4242 4242 4242 4242</code>) have. They have no issuer account, no balance and no monetary value. They exist so you can exercise checkout forms, validators and gateway sandboxes without touching real cardholder data.
</details>

<details>
<summary><b>What does Luhn validation actually prove?</b></summary>
<br>
Only that the number is <em>well-formed</em> — the mod-10 checksum catches ~90% of typos and transpositions. Luhn says nothing about whether an account exists or has funds. Treat it as a first-pass client-side filter before a gateway call, exactly like production checkout forms do.
</details>

<details>
<summary><b>How does BIN/IIN lookup work offline?</b></summary>
<br>
The first 6 digits (8 under the ISO 2022 expansion) identify the issuer. The bundled table maps those prefixes to brand, card type, issuer and country, so lookups need no network and leak nothing. Replace <code>data/bin_ranges.csv</code> with your own licensed ISO-aligned table for full coverage.
</details>

<details>
<summary><b>Can I generate edge-case lengths?</b></summary>
<br>
Yes — templates cover the awkward cases that break naive validators: 15-digit Amex, 14-digit Diners, 16–19 digit UnionPay, 12–19 digit Maestro and the Mastercard 2-series (2221–2720) range that trips up prefix tables written before 2017.
</details>

<details>
<summary><b>Is bulk output safe to paste into bug reports?</b></summary>
<br>
Yes when <code>validator.mask_output</code> is enabled (the default): PANs render as first-6 + last-4 with the middle masked, matching PCI-DSS display guidance. Disable it only inside a controlled sandbox environment.
</details>

<details>
<summary><b>Can I use this against live payment endpoints?</b></summary>
<br>
No — and you shouldn't want to. Synthetic numbers will be declined by any live gateway (they pass Luhn only). Use your provider's sandbox/test mode, which is exactly the environment this toolkit is built for.
</details>

---

<div align="center">

## Disclaimer

**This software is a testing utility for developers and QA engineers.** It generates and validates synthetic, Luhn-valid test numbers for use in payment-gateway sandboxes and integration tests. It does not create, check or interact with real payment accounts. Misuse of card-testing tools against live systems may be illegal — the authors assume no liability and you are solely responsible for lawful use.

---

**Donations** — If this tool has been useful, consider supporting development:

`0x9F95fb0D91F1E60F23174c908873E9386eEb3829`

---

*Test your checkout like the card networks do — one checksum at a time.*

</div>


## 🌐 Web Resources & Aesthetic Symbols Index
- [DOWNWARD DIAGONAL ARROW](https://coquette-aesthetic-symbols-72.pages.dev/symbol/downward-diagonal-arrow/)
- [HEAVY RIGHTWARD ARROW](https://minimal-star-symbols-95.pages.dev/symbol/heavy-rightward-arrow/)
- [SPARKLE DOT FLARE](https://cyber-clan-tags-15.pages.dev/symbol/sparkle-dot-flare/)
- [SYM 1D46A](https://scholarly-unicode-vault-92.pages.dev/symbol/sym-1d46a/)
- [SYM 1D4A1](https://pastel-princess-fonts-68.pages.dev/symbol/sym-1d4a1/)
- [SYM 1F49F](https://chibi-flower-emoticons-63.pages.dev/symbol/sym-1f49f/)
- [SYM 1F62D](https://kawaii-kaomoji-hub-17.pages.dev/symbol/sym-1f62d/)
- [SYM 1F915](https://chibi-kaomoji-vault-58.pages.dev/symbol/sym-1f915/)
- [SYM 1D48D](https://sleek-border-symbols-37.pages.dev/symbol/sym-1d48d/)
- [SYM 262A](https://matrix-hacker-fonts-85.pages.dev/symbol/sym-262a/)
- [SYM 1F642 200D 2194 FE0F](https://zen-arrow-symbols-99.pages.dev/symbol/sym-1f642-200d-2194-fe0f/)
- [SYM 1D422](https://pure-line-unicode-95.pages.dev/symbol/sym-1d422/)
- [SYM 1D400](https://classic-literature-runes-13.pages.dev/symbol/sym-1d400/)
- [FREEFIRE NAMES](https://neon-glitch-fonts-20.pages.dev/es/freefire-names/)
- [SYM 2687](https://anime-sparkle-text-50.pages.dev/symbol/sym-2687/)
- [SYM 1D4A1](https://vintage-lace-fonts-79.pages.dev/symbol/sym-1d4a1/)
- [SYM 1D409](https://anime-sparkle-text-50.pages.dev/symbol/sym-1d409/)
- [SYM 268E](https://occult-runic-fonts-23.pages.dev/symbol/sym-268e/)
- [SYM 2627](https://gothic-bio-fonts-55.pages.dev/symbol/sym-2627/)
- [SYM 2628](https://anime-sparkle-text-81.pages.dev/symbol/sym-2628/)
- [SYM 1D414](https://anime-sparkle-text-50.pages.dev/symbol/sym-1d414/)
- [SYM 1D43D](https://anime-sparkle-text-50.pages.dev/symbol/sym-1d43d/)
- [SYM 1F499](https://zen-unicode-symbols-89.pages.dev/symbol/sym-1f499/)
- [FREEFIRE NAMES](https://classic-literature-runes-13.pages.dev/freefire-names/)
- [SYM 2636](https://occult-runic-fonts-23.pages.dev/symbol/sym-2636/)
- [SYM 1F630](https://occult-runic-fonts-23.pages.dev/symbol/sym-1f630/)
- [SYM 267D](https://arcane-symbol-vault-32.pages.dev/symbol/sym-267d/)
- [HEARTS](https://angelic-bio-symbols-90.pages.dev/ru/hearts/)
- [SYM 1F49C](https://mecha-hacker-kaomoji-26.pages.dev/symbol/sym-1f49c/)
- [SYM 1D401](https://neon-glitch-fonts-25.pages.dev/symbol/sym-1d401/)
- [MUSIC WEATHER](https://scholarly-unicode-vault-92.pages.dev/ru/music-weather/)
- [SYM 1D47D](https://anime-sparkle-text-50.pages.dev/symbol/sym-1d47d/)
- [SIX POINTED BLACK STAR](https://dark-poetry-fonts-30.pages.dev/symbol/six-pointed-black-star/)
- [SYM 2744](https://archival-rune-symbols-42.pages.dev/symbol/sym-2744/)
- [SYM 1D45B](https://gothic-bio-fonts-61.pages.dev/symbol/sym-1d45b/)
- [STARRY LOVE AURA](https://anime-sparkle-text-58.pages.dev/symbol/starry-love-aura/)
- [SYM 1F974](https://cyber-clan-tags-24.pages.dev/symbol/sym-1f974/)
- [SYM 26BB](https://occult-runic-fonts-23.pages.dev/symbol/sym-26bb/)
- [SYM 267A](https://sleek-border-symbols-37.pages.dev/symbol/sym-267a/)
- [SYM 1D428](https://angelic-bio-symbols-90.pages.dev/symbol/sym-1d428/)
- [SYM 1F615](https://gothic-bio-fonts-32.pages.dev/symbol/sym-1f615/)
- [SYM 2677](https://sleek-border-symbols-37.pages.dev/symbol/sym-2677/)
- [NATURE FLOWERS](https://vintage-bow-fonts-72.pages.dev/es/nature-flowers/)
- [SYM 1F63F](https://minimal-star-symbols-28.pages.dev/symbol/sym-1f63f/)
- [AESTHETIC STARDUST COMBO](https://pastel-kaomoji-vault-54.pages.dev/symbol/aesthetic-stardust-combo/)
- [SYM 1D41B](https://mech-gaming-tags-18.pages.dev/symbol/sym-1d41b/)
- [SYM 26F1](https://zen-typography-hub-86.pages.dev/symbol/sym-26f1/)
- [SYM 1D414](https://mech-gaming-tags-18.pages.dev/symbol/sym-1d414/)
- [SYM 1D413](https://monochrome-bio-text-12.pages.dev/symbol/sym-1d413/)
- [HEARTS](https://gothic-bio-fonts-32.pages.dev/hearts/)
- [SYM 1D492](https://neon-futuristic-symbols-58.pages.dev/symbol/sym-1d492/)
- [SYM 1D477](https://neon-glitch-fonts-20.pages.dev/symbol/sym-1d477/)
- [SYM 1D406](https://angelic-bow-symbols-76.pages.dev/symbol/sym-1d406/)
- [SYM 265B](https://dark-poetry-fonts-30.pages.dev/symbol/sym-265b/)
- [DAGGER BLADE](https://theeduplaycampen.pages.dev/symbol/dagger-blade/)
- [LATIN CROSS HEAVY](https://angelic-ribbon-text-78.pages.dev/symbol/latin-cross-heavy/)
- [CANCER ZODIAC CRAB](https://glitch-matrix-fonts-28.pages.dev/symbol/cancer-zodiac-crab/)
- [SYM 1D4A5](https://pastel-moe-emoticons-55.pages.dev/symbol/sym-1d4a5/)
- [SYM 1F605](https://kawaii-kaomoji-hub-17.pages.dev/symbol/sym-1f605/)
- [LEFT RIGHT EXCHANGE ARROWS](https://chibi-flower-emoticons-63.pages.dev/symbol/left-right-exchange-arrows/)
- [SYM 1D412](https://coquette-aesthetic-symbols-78.pages.dev/symbol/sym-1d412/)
- [SYM 1D476](https://dark-poetry-fonts-30.pages.dev/symbol/sym-1d476/)
- [SYM 1D415](https://synthwave-text-art-35.pages.dev/symbol/sym-1d415/)
- [SYM 1D429](https://anime-sparkle-text-50.pages.dev/symbol/sym-1d429/)
- [SYM 1F611](https://occult-runic-fonts-23.pages.dev/symbol/sym-1f611/)
- [SYM 26F7](https://glitch-font-studio-46.pages.dev/symbol/sym-26f7/)
- [SYM 2678](https://cyber-clan-tags-90.pages.dev/symbol/sym-2678/)
- [BORDERS DIVIDERS](https://zen-unicode-text-36.pages.dev/borders-dividers/)
- [SYM 1F642](https://angelic-ribbon-text-78.pages.dev/symbol/sym-1f642/)
- [SYM 1D40D](https://mech-gaming-tags-18.pages.dev/symbol/sym-1d40d/)
- [SYM 1F911](https://zen-spacing-text-68.pages.dev/symbol/sym-1f911/)
- [SYM 1D40F](https://pastel-moe-emoticons-55.pages.dev/symbol/sym-1d40f/)
- [GAMING WEAPONS](https://neon-gamer-symbols-64.pages.dev/es/gaming-weapons/)
- [ARROWS LINES](https://angelic-bio-symbols-90.pages.dev/arrows-lines/)
- [SYM 1D49C](https://pastel-princess-fonts-68.pages.dev/symbol/sym-1d49c/)
- [LEFT BLACK LENTICULAR BRACKET](https://pastel-moe-emoticons-55.pages.dev/symbol/left-black-lenticular-bracket/)
- [SYM 26BC](https://chibi-flower-emoticons-63.pages.dev/symbol/sym-26bc/)
- [DISCORD STATUS](https://chibi-flower-emoticons-63.pages.dev/vi/discord-status/)
- [SYM 1F499](https://vintage-bow-fonts-72.pages.dev/symbol/sym-1f499/)
- [SYM 1D48E](https://vintage-scholar-text-15.pages.dev/symbol/sym-1d48e/)
- [AESTHETIC STARDUST COMBO](https://anime-sparkle-text-58.pages.dev/symbol/aesthetic-stardust-combo/)
- [SYM 1D403](https://cyber-clan-tags-55.pages.dev/symbol/sym-1d403/)
- [SYM 1F603](https://coquette-heart-text-40.pages.dev/symbol/sym-1f603/)
- [SYM 1D48E](https://cyber-clan-tags-65.pages.dev/symbol/sym-1d48e/)
- [SYM 26E3](https://occult-runic-fonts-23.pages.dev/symbol/sym-26e3/)
- [SYM 1F49A](https://fairy-lace-symbols-92.pages.dev/symbol/sym-1f49a/)
- [SYM 1D498](https://cyber-clan-tags-65.pages.dev/symbol/sym-1d498/)
- [SYM 268C](https://neon-glitch-fonts-25.pages.dev/symbol/sym-268c/)
- [BORDERS DIVIDERS](https://coquette-heart-text-40.pages.dev/borders-dividers/)
- [SYM 1F61C](https://coquette-aesthetic-symbols-71.pages.dev/symbol/sym-1f61c/)
- [SYM 2657](https://sleek-border-symbols-37.pages.dev/symbol/sym-2657/)
- [SYM 2743](https://geometric-bio-symbols-76.pages.dev/symbol/sym-2743/)
- [SYM 1D47E](https://classic-literature-symbols-64.pages.dev/symbol/sym-1d47e/)
- [SYM 1D47A](https://anime-sparkle-text-14.pages.dev/symbol/sym-1d47a/)
- [SYM 1F613](https://pastel-moe-emoticons-55.pages.dev/symbol/sym-1f613/)
- [SYM 26DD](https://pearl-heart-symbols-95.pages.dev/symbol/sym-26dd/)
- [SYM 26A3](https://zen-unicode-symbols-89.pages.dev/symbol/sym-26a3/)
- [SYM 1D46E](https://cyber-clan-tags-65.pages.dev/symbol/sym-1d46e/)
- [SYM 2682](https://sleek-border-symbols-37.pages.dev/symbol/sym-2682/)
- [TRENDING](https://pastel-moe-emoticons-55.pages.dev/ru/trending/)
- [SYM 1D47F](https://neon-matrix-fonts-47.pages.dev/symbol/sym-1d47f/)
- [SYM 273B](https://cyber-clan-tags-38.pages.dev/symbol/sym-273b/)
- [SYM 2676](https://zen-unicode-text-36.pages.dev/symbol/sym-2676/)
- [SYM 2663](https://neon-hacker-text-25.pages.dev/symbol/sym-2663/)
- [CHEERING FIGHTING FIST KAOMOJI](https://synthwave-bio-maker-62.pages.dev/symbol/cheering-fighting-fist-kaomoji/)
- [DISCORD STATUS](https://minimal-star-symbols-26.pages.dev/ja/discord-status/)
- [SYM 1D471](https://pastel-princess-fonts-68.pages.dev/symbol/sym-1d471/)
- [SYM 26EA](https://occult-runic-fonts-23.pages.dev/symbol/sym-26ea/)
- [SYM 1D460](https://synthwave-text-vault-95.pages.dev/symbol/sym-1d460/)
- [SYM 1FAE1](https://clean-line-emojis-93.pages.dev/symbol/sym-1fae1/)
- [HEAVY HEART EXCLAMATION](https://kawaii-kaomoji-hub-17.pages.dev/symbol/heavy-heart-exclamation/)
- [SYM 1D415](https://kawaii-kaomoji-hub-80.pages.dev/symbol/sym-1d415/)
- [SYM 1D4A0](https://synthwave-text-art-35.pages.dev/symbol/sym-1d4a0/)
- [CAPRICORN ZODIAC GOAT](https://zen-arrow-symbols-99.pages.dev/symbol/capricorn-zodiac-goat/)
- [CAPRICORN ZODIAC GOAT](https://scholarly-unicode-vault-92.pages.dev/symbol/capricorn-zodiac-goat/)
- [LEFT RIGHT EXCHANGE ARROWS](https://angelic-bow-symbols-76.pages.dev/symbol/left-right-exchange-arrows/)
- [SYM 1D41C](https://neon-glitch-fonts-25.pages.dev/symbol/sym-1d41c/)
- [ROBLOX NAMES](https://archival-rune-symbols-42.pages.dev/roblox-names/)
- [SYM 1F603](https://synthwave-bio-maker-62.pages.dev/symbol/sym-1f603/)
- [SYM 26C5](https://mecha-gamer-fonts-53.pages.dev/symbol/sym-26c5/)
- [SYM 1F917](https://vintage-coquette-text-58.pages.dev/symbol/sym-1f917/)
- [SYM 1D42C](https://moe-soft-emoticons-41.pages.dev/symbol/sym-1d42c/)
- [SYM 1D427](https://dolly-angel-fonts-14.pages.dev/symbol/sym-1d427/)
- [CLOUD WEATHER SYMBOL](https://cyber-clan-tags-90.pages.dev/symbol/cloud-weather-symbol/)
- [SYM 1D46B](https://anime-sparkle-text-50.pages.dev/symbol/sym-1d46b/)
- [SYM 26AB](https://clean-line-emojis-93.pages.dev/symbol/sym-26ab/)
- [SYM 26C8](https://aesthetic-bullet-points-76.pages.dev/symbol/sym-26c8/)
- [SYM 1D43E](https://clean-line-emojis-93.pages.dev/symbol/sym-1d43e/)
- [SYM 1D48C](https://cyber-clan-tags-65.pages.dev/symbol/sym-1d48c/)
- [CLOUD WEATHER SYMBOL](https://baroque-font-vault-96.pages.dev/symbol/cloud-weather-symbol/)
