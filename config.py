# -*- coding: utf-8 -*-
"""Configuration loader for CC Checker — JSON config + defaults."""

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"

_DEFAULTS = {'generator': {'default_brand': 'visa',
                   'default_count': 10,
                   'bin': '',
                   'include_expiry': True,
                   'include_cvv': True,
                   'expiry_years_ahead': 3},
     'validator': {'luhn_check': True,
                   'brand_detection': True,
                   'expiry_check': True,
                   'cvv_check': True,
                   'mask_output': True},
     'bin_database': {'path': 'data/bin_ranges.csv',
                      'auto_update': True,
                      'source': 'bundled'},
     'bulk': {'threads': 8,
              'input_file': 'cards.txt',
              'output_file': 'results.txt',
              'skip_duplicates': True},
     'export': {'default_format': 'csv', 'output_directory': './results'}}


def load_config() -> dict:
    """Load configuration from config.json, merging with defaults."""
    cfg = dict(_DEFAULTS)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            _deep_merge(cfg, user_cfg)
        except (json.JSONDecodeError, OSError):
            pass
    return cfg


def _deep_merge(base: dict, override: dict):
    """Recursively merge override into base dict."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def save_config(cfg: dict):
    """Persist configuration to config.json."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
