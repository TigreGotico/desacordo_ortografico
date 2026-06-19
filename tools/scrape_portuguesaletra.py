#!/usr/bin/env python3
"""Scrape portuguesaletra.com's *Acordo Ortográfico* category into a dataset of words
whose spelling the 1990 reform touched.

Each article on https://portuguesaletra.com/category/acordo-ortografico/ documents one
vocábulo with a fixed, labelled layout:

    Português Europeu   · Ortografia Antiga _1945 · <pre-1990 European form(s)>
    Português Brasileiro · Ortografia Antiga _1943 · <pre-1990 Brazilian form(s)>
    Acordo Ortográfico   · Ortografia Nova  _1990  · vocábulo(s) válido(s): <AO1990 form(s)>
    observações          · <usage notes, e.g. "X não é usado no Brasil">

This client crawls the category pagination, parses each article into that schema, and
writes one JSON record per word:

    {"slug", "url", "title", "eu_1945": [...], "br_1943": [...], "ao1990": [...],
     "notes": "...", "changed": true|false|null}

Stdlib only. Polite by default: a real User-Agent, a delay between requests, retries with
back-off, and it honours the site's small robots.txt (only /cgi-bin and named bad bots).

    python tools/scrape_portuguesaletra.py -o portuguesaletra_ao.jsonl --delay 1.0
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request

BASE = "https://portuguesaletra.com"
CATEGORY = BASE + "/category/acordo-ortografico/"
ARTICLE_RE = re.compile(r"https://portuguesaletra\.com/acordo-ortografico/[a-z0-9-]+/")
UA = "Mozilla/5.0 (+desacordo_ortografico research scraper; contact: TigreGotico)"

# Field labels in article order. The text between two consecutive labels is the value.
_EU = "Ortografia Antiga _1945"
_BR = "Ortografia Antiga _1943"
_NEW = "vocábulo(s) válido(s)"
_OBS = "observações"
_END = "Referências"
_PT_HDR = "Português Brasileiro"
_AO_HDR = "Acordo Ortográfico"


def _get(url: str, *, retries: int = 3, timeout: int = 30) -> str:
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except (urllib.error.URLError, TimeoutError) as e:  # noqa: PERF203
            last = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"failed to fetch {url}: {last}")


def article_urls(delay: float) -> list[str]:
    """Walk the category pagination until a page yields no new article links."""
    seen, page = [], 1
    while True:
        url = CATEGORY if page == 1 else f"{CATEGORY}page/{page}/"
        try:
            body = _get(url)
        except RuntimeError:
            break
        found = [u for u in dict.fromkeys(ARTICLE_RE.findall(body)) if u not in seen]
        if not found:
            break
        seen.extend(found)
        page += 1
        time.sleep(delay)
    return seen


def _text(article_html: str) -> str:
    """Article HTML -> flat text, with the labels above kept intact."""
    t = re.sub(r"(?is)<script.*?</script>|<style.*?</style>|<nav.*?</nav>", "", article_html)
    m = re.search(r"(?is)(<h1.*?Refer[êe]ncias)", t)
    seg = m.group(1) if m else t
    txt = html.unescape(re.sub(r"(?s)<[^>]+>", " ", seg))
    return re.sub(r"\s+", " ", txt).strip()


def _between(text: str, start: str, end: str) -> str:
    i = text.find(start)
    if i < 0:
        return ""
    i += len(start)
    j = text.find(end, i)
    return text[i:j if j >= 0 else len(text)].strip()


def _forms(value: str) -> list[str]:
    """Split a 'a, b, c' value into a clean list of word forms."""
    value = value.strip(" .;–-").strip()
    return [w.strip() for w in re.split(r"[,/]| e ", value) if w.strip()]


def parse_article(url: str, article_html: str) -> dict | None:
    txt = _text(article_html)
    mt = re.search(r"(?is)<title>(.*?)</title>", article_html)
    title = html.unescape(mt.group(1)).split("|")[0].strip() if mt else url
    eu = _forms(_between(txt, _EU, _PT_HDR))
    br = _forms(_between(txt, _BR, _AO_HDR))
    ao = _forms(_between(txt, _NEW, _OBS))
    notes = _between(txt, _OBS, _END)
    if not (eu or br or ao):
        return None
    low = notes.lower()
    if "não altera" in low or "mantida" in low or "mantém" in low:
        changed = False
    elif "alterada" in low or "altera-se" in low:
        changed = True
    else:
        changed = None
    aoset = {w.lower() for w in ao}
    return {
        "slug": url.rstrip("/").rsplit("/", 1)[-1],
        "url": url,
        "title": title,
        "eu_1945": eu,
        "br_1943": br,
        "ao1990": ao,
        "notes": notes,
        "changed": changed,
        # did the pre-1990 European / Brazilian spelling actually change under AO1990?
        "eu_changed": bool(eu) and any(w.lower() not in aoset for w in eu),
        "br_changed": bool(br) and any(w.lower() not in aoset for w in br),
    }


def scrape(out_path: str, delay: float = 0.5, limit: int | None = None) -> int:
    """Crawl every article and stream one JSON record per word to ``out_path``."""
    print("discovering article URLs…", file=sys.stderr)
    urls = article_urls(delay)
    if limit:
        urls = urls[:limit]
    print(f"{len(urls)} articles", file=sys.stderr)
    n = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for i, url in enumerate(urls, 1):
            try:
                rec = parse_article(url, _get(url))
            except RuntimeError as e:
                print(f"  ! {url}: {e}", file=sys.stderr)
                rec = None
            if rec:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                n += 1
            if i % 50 == 0 or i == len(urls):
                print(f"  [{i}/{len(urls)}] {n} parsed", file=sys.stderr)
            time.sleep(delay)
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--out", default="portuguesaletra_ao.jsonl")
    ap.add_argument("--delay", type=float, default=0.5, help="seconds between requests")
    ap.add_argument("--limit", type=int, default=None, help="cap article count (testing)")
    args = ap.parse_args()
    n = scrape(args.out, args.delay, args.limit)
    print(f"wrote {n} words to {args.out}")


if __name__ == "__main__":
    main()
