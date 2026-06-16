#!/usr/bin/env python3
"""Phase 6 — harvest candidate secondary scholarship from online repositories.

Candidate-generation only: this NEVER writes to data/secondary.json directly.
It queries OpenAlex and Crossref (free, ToS-clean), and optionally Google
Scholar via SerpAPI, normalizes hits to the secondary schema, dedupes against
the existing dataset (DOI first, then normalized author+title+year), and writes
NEW candidates to data/sources/harvest_candidates.json for review in the
human-in-the-loop app before any merge.

Usage:
    python3 scripts/harvest_online.py                 # topic + corpus-author queries
    python3 scripts/harvest_online.py --author "al-Junayd" --author "al-Hallaj"
    python3 scripts/harvest_online.py --scholar       # also query Google Scholar (needs SERPAPI_KEY)
    python3 scripts/harvest_online.py --per-query 50

Dependencies: standard library only (urllib). SerpAPI key via env SERPAPI_KEY.
Be polite: set CONTACT_EMAIL for the OpenAlex/Crossref "polite pool".
"""
import argparse
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

from validate_secondary import load_schema, validate_instance

ROOT = Path(__file__).resolve().parent.parent
SECONDARY = ROOT / "data" / "sources" / "secondary_all.json"
PRIMARY = ROOT / "data" / "bibliography.json"
OUT = ROOT / "data" / "sources" / "harvest_candidates.json"

CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "digitalsufism@gmail.com")
USER_AGENT = f"DigitalSufismBot/1.0 (mailto:{CONTACT_EMAIL})"

TOPIC_TERMS = ["Sufism early", "taṣawwuf formative", "early Islamic mysticism"]

# OpenAlex Crossref type -> our schema type
TYPE_MAP = {
    "article": "journal-article", "journal-article": "journal-article",
    "book": "book", "monograph": "book", "edited-book": "book",
    "book-chapter": "book-chapter", "chapter": "book-chapter",
    "dissertation": "thesis", "thesis": "thesis",
}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def get_json(url, params=None):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ---- existing-dataset index for dedup ---------------------------------------

def load_existing_keys():
    data = json.loads(SECONDARY.read_text(encoding="utf-8"))
    dois, keys = set(), set()
    for w in data["works"]:
        url = (w.get("url") or "").lower()
        m = re.search(r"10\.\d{4,9}/\S+", url)
        if m:
            dois.add(m.group(0).rstrip("/"))
        a = (w.get("authors") or [{}])[0].get("name", "")
        keys.add((norm(a), norm(w.get("title", ""))[:60], (w.get("year") or "").strip()))
    return dois, keys


def corpus_author_names():
    """Distinctive shuhra names of primary-corpus authors for targeted queries."""
    data = json.loads(PRIMARY.read_text(encoding="utf-8"))
    names = []
    for a in data["authors"]:
        # take the last 'al-...' nisba token as the recognizable name
        toks = [t for t in a["name"].split() if t.lower().startswith("al-")]
        names.append(toks[-1] if toks else a["name"].split()[-1])
    return sorted(set(names))


# ---- source adapters --------------------------------------------------------

def from_openalex(query, per_query):
    data = get_json("https://api.openalex.org/works", {
        "search": query,
        "per-page": min(per_query, 200),
        "mailto": CONTACT_EMAIL,
    })
    out = []
    for r in data.get("results", []):
        authors = [{"name": a["author"]["display_name"]}
                   for a in r.get("authorships", []) if a.get("author")]
        out.append({
            "_type": r.get("type", ""),
            "title": r.get("title") or "",
            "authors": authors,
            "year": str(r.get("publication_year") or ""),
            "container": (r.get("primary_location") or {}).get("source", {}).get("display_name", "")
                         if (r.get("primary_location") or {}).get("source") else "",
            "doi": (r.get("doi") or "").replace("https://doi.org/", ""),
            "url": r.get("doi") or (r.get("primary_location") or {}).get("landing_page_url", "") or "",
            "_origin": "openalex",
        })
    return out


def from_crossref(query, per_query):
    data = get_json("https://api.crossref.org/works", {
        "query": query,
        "rows": min(per_query, 100),
        "mailto": CONTACT_EMAIL,
    })
    out = []
    for r in data.get("message", {}).get("items", []):
        authors = [{"name": " ".join(filter(None, [a.get("given"), a.get("family")]))}
                   for a in r.get("author", []) if a.get("family")]
        year = ""
        parts = (r.get("issued") or {}).get("date-parts") or [[]]
        if parts and parts[0]:
            year = str(parts[0][0])
        out.append({
            "_type": r.get("type", ""),
            "title": (r.get("title") or [""])[0],
            "authors": authors,
            "year": year,
            "container": (r.get("container-title") or [""])[0],
            "volume": r.get("volume", ""),
            "issue": r.get("issue", ""),
            "pages": r.get("page", ""),
            "publisher": r.get("publisher", ""),
            "doi": r.get("DOI", ""),
            "url": r.get("URL", ""),
            "_origin": "crossref",
        })
    return out


def from_scholar(query, per_query):
    key = os.environ.get("SERPAPI_KEY")
    if not key:
        print("  ! --scholar requested but SERPAPI_KEY not set; skipping Scholar", file=sys.stderr)
        return []
    data = get_json("https://serpapi.com/search", {
        "engine": "google_scholar", "q": query, "num": min(per_query, 20), "api_key": key,
    })
    out = []
    for r in data.get("organic_results", []):
        pub = r.get("publication_info", {})
        authors = [{"name": a["name"]} for a in pub.get("authors", []) if a.get("name")]
        ym = re.search(r"\b(1[5-9]\d{2}|20\d{2})\b", pub.get("summary", ""))
        out.append({
            "_type": "article",
            "title": r.get("title", ""),
            "authors": authors,
            "year": ym.group(0) if ym else "",
            "container": pub.get("summary", ""),
            "url": r.get("link", ""),
            "_origin": "scholar",
        })
    return out


# ---- normalize to schema ----------------------------------------------------

def to_record(hit, index):
    rec = {
        "id": f"sec_h{index:04d}",
        "type": TYPE_MAP.get((hit.get("_type") or "").lower(), "journal-article"),
        "title": (hit.get("title") or "").strip(),
        "language": "English",  # online sources are predominantly EN; reviewer corrects
        "provenance": {"source": hit.get("_origin", "online"), "reviewed": False},
    }
    if hit.get("authors"):
        rec["authors"] = hit["authors"]
    for f in ("container", "volume", "issue", "pages", "publisher", "year", "url"):
        if hit.get(f):
            rec[f] = str(hit[f])
    if hit.get("doi"):
        rec.setdefault("url", "https://doi.org/" + hit["doi"])
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--author", action="append", default=[], help="extra author query (repeatable)")
    ap.add_argument("--per-query", type=int, default=25)
    ap.add_argument("--scholar", action="store_true", help="also query Google Scholar (SerpAPI)")
    ap.add_argument("--sleep", type=float, default=1.0, help="seconds between API calls")
    args = ap.parse_args()

    schema = load_schema()
    dois, keys = load_existing_keys()

    queries = list(TOPIC_TERMS)
    authors = args.author or corpus_author_names()
    queries += [f"Sufism {a}" for a in authors]

    adapters = [from_openalex, from_crossref]
    if args.scholar:
        adapters.append(from_scholar)

    raw = []
    for q in queries:
        for adapter in adapters:
            try:
                hits = adapter(q, args.per_query)
                raw.extend(hits)
                print(f"  {adapter.__name__:14s} '{q}': {len(hits)} hits")
            except Exception as e:  # noqa: BLE001 — keep harvesting on a single failure
                print(f"  ! {adapter.__name__} '{q}' failed: {e}", file=sys.stderr)
            time.sleep(args.sleep)

    # dedup: against existing dataset AND within this harvest
    candidates, seen_local, n_dup = [], set(), 0
    idx = 0
    for hit in raw:
        if not (hit.get("title") or "").strip():
            continue
        doi = (hit.get("doi") or "").lower().rstrip("/")
        a0 = (hit.get("authors") or [{}])[0].get("name", "")
        key = (norm(a0), norm(hit.get("title", ""))[:60], str(hit.get("year") or "").strip())
        if (doi and doi in dois) or key in keys or key in seen_local:
            n_dup += 1
            continue
        seen_local.add(key)
        if doi:
            dois.add(doi)
        idx += 1
        rec = to_record(hit, idx)
        errs = validate_instance(rec, schema)
        if errs:
            print(f"  ! candidate {rec['id']} invalid: {errs[0]}", file=sys.stderr)
            continue
        candidates.append(rec)

    payload = {
        "metadata": {
            "totalWorks": len(candidates),
            "lastUpdated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "version": "1.0",
            "sources": sorted({c["provenance"]["source"] for c in candidates}),
            "note": "Harvested candidates — review before merging into data/secondary.json",
        },
        "works": candidates,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(candidates)} new candidates ({n_dup} duplicates skipped) -> {OUT.relative_to(ROOT)}")
    print("Review these in review/secondary-review.html, then merge accepted records.")


if __name__ == "__main__":
    main()
