#!/usr/bin/env python3
"""Phase 3b — handle URL-only chunk files (Persian, Russian, stray WorldCat links).

These blocks carry no structured citation, only a WorldCat URL whose slug
encodes a transliterated title. We emit minimal records (url + slug-derived
title + notes 'metadata pending') rather than dropping them.

Run: python3 scripts/extract_url_only.py
"""
import json
import re
from pathlib import Path

from validate_secondary import load_schema, validate_instance

ROOT = Path(__file__).resolve().parent.parent
CHUNK_DIR = ROOT / "data" / "sources" / "chunks"
OUT_DIR = ROOT / "data" / "sources" / "extracted"

URL_ONLY = {
    "Persian": "Persian",
    "Russian": "Russian",
}


def slug_title(url):
    m = re.search(r"/title/([^/]+)/oclc", url)
    if not m:
        return "[WorldCat record]"
    slug = m.group(1).replace("-", " ").strip()
    return slug[:1].upper() + slug[1:] if slug else "[WorldCat record]"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    schema = load_schema()
    for language, fname in URL_ONLY.items():
        chunk_file = CHUNK_DIR / f"{fname}.json"
        if not chunk_file.exists():
            continue
        blocks = json.loads(chunk_file.read_text(encoding="utf-8"))
        works = []
        for i, b in enumerate(blocks, start=1):
            raw = b["raw"].strip()
            url = raw.split()[0] if raw.lower().startswith("http") else ""
            if not url:
                continue
            work = {
                "id": f"sec_{language[:2].lower()}{i:03d}",
                "type": "book",
                "title": slug_title(url),
                "language": language,
                "url": url,
                "notes": "metadata pending — derived from WorldCat URL slug",
                "provenance": {
                    "source": f"old_bibliography/{language}",
                    "sourceId": b["block_id"],
                    "reviewed": False,
                },
            }
            errs = validate_instance(work, schema)
            if errs:
                raise SystemExit(f"{work['id']}: {errs[0]}")
            works.append(work)
        (OUT_DIR / f"{language}.json").write_text(
            json.dumps({"works": works}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  {language}: {len(works)} URL-only records")


if __name__ == "__main__":
    main()
