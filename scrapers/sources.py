"""Load config/sources.json and enforce the terms-of-use gate."""

from __future__ import annotations

from .records import load_json_config


class SourceNotPermitted(Exception):
    """Raised when a source's terms have not been confirmed to allow automated access."""


def source(platform: str) -> dict:
    return load_json_config("sources.json")[platform]


def require_permitted(platform: str) -> dict:
    cfg = source(platform)
    if cfg.get("terms_allow_automation") is not True:
        raise SourceNotPermitted(
            f"{platform}: terms_allow_automation is not true in config/sources.json. "
            "Check the store's terms first, or use the chart-tracker fallback."
        )
    return cfg
