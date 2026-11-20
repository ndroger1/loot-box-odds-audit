"""Small helpers for deciding which links stay 'on the publisher's site'."""

from __future__ import annotations

from urllib.parse import urlsplit

# Second-level suffixes that need three labels to identify a site (e.g. nexon.co.kr)
TWO_PART_SUFFIXES = {"co.kr", "or.kr", "co.uk", "org.uk", "com.au", "co.jp", "com.cn", "com.tw", "com.hk"}

# Links to these are never treated as a publisher's own site
EXCLUDED_SITES = {
    "steampowered.com", "steamcommunity.com", "apple.com", "google.com", "youtube.com",
    "youtu.be", "facebook.com", "instagram.com", "twitter.com", "x.com", "tiktok.com",
    "discord.gg", "discord.com", "reddit.com", "twitch.tv", "linktr.ee", "bit.ly",
    "playstation.com", "xbox.com", "microsoft.com", "nintendo.com", "epicgames.com",
}


def site_of(url: str) -> str:
    host = (urlsplit(url).hostname or "").lower()
    labels = host.split(".")
    if len(labels) >= 3 and ".".join(labels[-2:]) in TWO_PART_SUFFIXES:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def is_excluded(url: str) -> bool:
    return site_of(url) in EXCLUDED_SITES


def same_site(url: str, site: str) -> bool:
    return site_of(url) == site
