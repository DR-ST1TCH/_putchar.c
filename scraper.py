#!/usr/bin/env python3
"""Simple web scraper: fetch a page, extract title, text, links, images,
and optional CSS-selector matches. Output as JSON or CSV.

Usage:
    python scraper.py https://example.com
    python scraper.py https://example.com -s "h1" -s "p.intro" -o out.json
    python scraper.py https://example.com --links -f csv -o links.csv
    python scraper.py https://example.com --crawl 10    # follow same-domain links
"""
import argparse
import csv
import json
import sys
import time
from collections import deque
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SimpleScraper/1.0)"}


def fetch(url, session, timeout=10, retries=3):
    """GET a URL with simple retry/backoff. Returns HTML text or None."""
    for attempt in range(retries):
        try:
            resp = session.get(url, headers=HEADERS, timeout=timeout)
            resp.raise_for_status()
            if "html" not in resp.headers.get("Content-Type", ""):
                return None
            return resp.text
        except requests.RequestException as exc:
            print(f"[warn] {url}: {exc} (attempt {attempt + 1}/{retries})", file=sys.stderr)
            time.sleep(2 ** attempt)
    return None


def parse(html, url, selectors=()):
    """Extract data from an HTML document."""
    soup = BeautifulSoup(html, "html.parser")
    data = {
        "url": url,
        "title": soup.title.get_text(strip=True) if soup.title else None,
        "links": sorted({urldefrag(urljoin(url, a["href"]))[0]
                         for a in soup.find_all("a", href=True)
                         if urlparse(urljoin(url, a["href"])).scheme in ("http", "https")}),
        "images": sorted({urljoin(url, i["src"]) for i in soup.find_all("img", src=True)}),
    }
    if selectors:
        data["matches"] = {sel: [el.get_text(" ", strip=True) for el in soup.select(sel)]
                           for sel in selectors}
    else:
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        data["text"] = soup.get_text(" ", strip=True)
    return data


def crawl(start, max_pages, delay, selectors):
    """Breadth-first crawl limited to the start URL's domain."""
    domain = urlparse(start).netloc
    seen, queue, results = {start}, deque([start]), []
    with requests.Session() as session:
        while queue and len(results) < max_pages:
            url = queue.popleft()
            html = fetch(url, session)
            if html is None:
                continue
            page = parse(html, url, selectors)
            results.append(page)
            print(f"[{len(results)}/{max_pages}] {url}", file=sys.stderr)
            for link in page["links"]:
                if urlparse(link).netloc == domain and link not in seen:
                    seen.add(link)
                    queue.append(link)
            time.sleep(delay)
    return results


def write_output(results, fmt, path, links_only):
    out = open(path, "w", newline="", encoding="utf-8") if path else sys.stdout
    try:
        if fmt == "json":
            payload = ([{"url": r["url"], "links": r["links"]} for r in results]
                       if links_only else results)
            json.dump(payload, out, indent=2, ensure_ascii=False)
            out.write("\n")
        else:
            writer = csv.writer(out)
            if links_only:
                writer.writerow(["source", "link"])
                writer.writerows((r["url"], l) for r in results for l in r["links"])
            else:
                writer.writerow(["url", "title", "num_links", "num_images"])
                writer.writerows((r["url"], r["title"], len(r["links"]), len(r["images"]))
                                 for r in results)
    finally:
        if path:
            out.close()


def main():
    p = argparse.ArgumentParser(description="Simple web scraper")
    p.add_argument("url")
    p.add_argument("-s", "--selector", action="append", default=[],
                   help="CSS selector to extract (repeatable)")
    p.add_argument("--links", action="store_true", help="output only links")
    p.add_argument("--crawl", type=int, default=1, metavar="N",
                   help="max pages to crawl on the same domain (default 1)")
    p.add_argument("--delay", type=float, default=1.0,
                   help="seconds between requests when crawling (default 1)")
    p.add_argument("-f", "--format", choices=["json", "csv"], default="json")
    p.add_argument("-o", "--output", help="output file (default: stdout)")
    args = p.parse_args()

    results = crawl(args.url, args.crawl, args.delay, args.selector)
    if not results:
        sys.exit("No pages could be fetched.")
    write_output(results, args.format, args.output, args.links)


if __name__ == "__main__":
    main()
