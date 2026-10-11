#!/usr/bin/env python3
"""Simple web scraper: fetch a page and extract title, text, links, images,
or elements matching a CSS selector.

Usage:
    python3 scraper.py https://example.com
    python3 scraper.py https://example.com --select "h1, h2" --json
    python3 scraper.py https://example.com --links --output links.csv

Requires: pip install requests beautifulsoup4
"""
import argparse
import csv
import json
import sys
import time
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (compatible; SimpleScraper/1.0)"


def allowed_by_robots(url, user_agent=USER_AGENT):
    """Check robots.txt; return True if fetching is allowed (or robots.txt is unavailable)."""
    parts = urlparse(url)
    rp = RobotFileParser()
    rp.set_url(f"{parts.scheme}://{parts.netloc}/robots.txt")
    try:
        rp.read()
    except Exception:
        return True
    return rp.can_fetch(user_agent, url)


def fetch(url, retries=3, timeout=10):
    """GET a URL with retries and backoff; return the response."""
    headers = {"User-Agent": USER_AGENT}
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            if attempt == retries:
                raise
            wait = 2 ** attempt
            print(f"[warn] {exc}; retrying in {wait}s", file=sys.stderr)
            time.sleep(wait)


def parse(html, base_url, selector=None):
    """Extract data from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    data = {
        "url": base_url,
        "title": soup.title.get_text(strip=True) if soup.title else None,
        "links": [
            {"text": a.get_text(strip=True), "href": urljoin(base_url, a["href"])}
            for a in soup.find_all("a", href=True)
        ],
        "images": [urljoin(base_url, img["src"]) for img in soup.find_all("img", src=True)],
    }
    if selector:
        data["selected"] = [el.get_text(" ", strip=True) for el in soup.select(selector)]
    else:
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        data["text"] = soup.get_text("\n", strip=True)
    return data


def save(data, path, fmt):
    """Write results to a file as JSON or CSV."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        if fmt == "csv":
            rows = data.get("selected") and [{"text": t} for t in data["selected"]] or data["links"]
            if not rows:
                return
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        else:
            json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    p = argparse.ArgumentParser(description="Simple web scraper")
    p.add_argument("url", help="Page to scrape")
    p.add_argument("--select", help="CSS selector to extract text from")
    p.add_argument("--links", action="store_true", help="Print only links")
    p.add_argument("--json", action="store_true", help="Print full result as JSON")
    p.add_argument("--output", "-o", help="Save to file (.json or .csv)")
    p.add_argument("--ignore-robots", action="store_true", help="Skip robots.txt check")
    args = p.parse_args()

    if not args.ignore_robots and not allowed_by_robots(args.url):
        sys.exit("Blocked by robots.txt (use --ignore-robots only if you have permission).")

    try:
        resp = fetch(args.url)
    except requests.RequestException as exc:
        sys.exit(f"Request failed: {exc}")

    data = parse(resp.text, resp.url, args.select)

    if args.output:
        save(data, args.output, "csv" if args.output.endswith(".csv") else "json")
        print(f"Saved to {args.output}")
    elif args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif args.links:
        for link in data["links"]:
            print(f"{link['text']}\t{link['href']}")
    elif args.select:
        print("\n".join(data["selected"]))
    else:
        print(f"Title: {data['title']}\n")
        print(data["text"])


if __name__ == "__main__":
    main()
