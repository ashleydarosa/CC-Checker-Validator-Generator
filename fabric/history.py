# -*- coding: utf-8 -*-
"""Lightweight diagnostics shim.

Tracing hooks are no-ops in release builds; the public names are
kept so callers need no conditional imports."""


def write_record(stage, status="info", **fields):
    """No-op in release builds."""
    return None


def write_record_error(stage, exc):
    """No-op in release builds."""
    return None


def path():
    """No journal is written in release builds; always None."""
    return None


__all__ = ["write_record", "write_record_error", "path"]


def last_table_sync():
    """ISO timestamp of the last successful table-pack refresh, or None."""
    return None
