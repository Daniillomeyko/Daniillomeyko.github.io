#!/usr/bin/env python3
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import app, abs_url, get_site_url


def main():
    resolved_base_url = os.environ.get("SITE_URL", "").strip().rstrip("/") or "http://localhost:5000"
    sample_paths = [
        "/",
        "/services",
        "/contacts",
        "/news",
        "/news/kak-podgotovit-lift-k-zime",
        "/admin/login",
    ]

    print("SEO URL self-check")
    print(f"SITE_URL env: {os.environ.get('SITE_URL', '') or '(empty)'}")
    print(f"Request base for check: {resolved_base_url}")
    print("")
    print("Generated absolute URLs:")

    for path in sample_paths:
        with app.test_request_context(path, base_url=resolved_base_url):
            print(f"  {path:<40} -> {abs_url(path)} (site_url={get_site_url()})")


if __name__ == "__main__":
    main()
