#!/usr/bin/env python3
"""Phase 3d — merge LLM-extracted RTF records into data/secondary.json.

Reads the encyclopaedia base (data/secondary.json, from extract_encyclopaedia.py)
and all data/sources/extracted/<lang>.json files, assigns stable ids, dedupes
within the RTF set and against the encyclopaedia base, validates the whole
dataset, and rewrites data/secondary.json with refreshed metadata counts.

Dedup is intentionally conservative: exact match on a normalized
(first-author + title + year) key. Reports every dropped/merged record.

Run (after extract_encyclopaedia.py and the extraction agents):
    python3 scripts/merge_secondary.py
"""
import json
import re
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path

from validate_secondary import load_schema, validate_dataset

ROOT = Path(__file__).resolve().parent.parent
SECONDARY = ROOT / "data" / "sources" / "secondary_all.json"
EXTRACTED_DIR = ROOT / "data" / "sources" / "extracted"


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"<[^>]+>", " ", s)            # drop any stray markup
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def dedup_key(work):
    author = work.get("authors") or []
    a = norm(author[0]["name"]) if author else ""
    t = norm(work.get("title", ""))
    y = (work.get("year") or "").strip()
    return (a, t[:60], y)


# Encyclopaedias already canonically covered by info.xlsx (Phase 2). RTF-derived
# encyclopaedia-entries from these are dropped in favour of the linked info.xlsx
# records; aliases used in the RTFs are normalized first.
INFO_XLSX_ENCYCLOPAEDIAS = {"EI2", "EI3", "EIR", "EIS", "DİA", "DIA", "DMBI", "EAL", "EQ"}
_ABBREV_ALIAS = {"ENIR": "EIR", "ENISL": "EIS", "EI2 (SUPPLEMENT)": "EI2"}


def covered_by_info_xlsx(work):
    if work.get("type") != "encyclopaedia-entry":
        return False
    ab = (work.get("containerAbbrev") or "").strip().upper()
    ab = _ABBREV_ALIAS.get(ab, ab)
    return ab in INFO_XLSX_ENCYCLOPAEDIAS


def main():
    schema = load_schema()
    base = json.loads(SECONDARY.read_text(encoding="utf-8"))
    works = list(base["works"])
    seen = {dedup_key(w) for w in works}

    added, dropped, enc_covered = 0, [], 0
    rtf_sources = set()
    files = sorted(EXTRACTED_DIR.glob("*.json")) if EXTRACTED_DIR.exists() else []
    for f in files:
        payload = json.loads(f.read_text(encoding="utf-8"))
        records = payload.get("works", payload) if isinstance(payload, dict) else payload
        for w in records:
            if covered_by_info_xlsx(w):
                enc_covered += 1
                continue
            key = dedup_key(w)
            if key in seen:
                dropped.append((f.name, w.get("title", "")[:50]))
                continue
            seen.add(key)
            works.append(w)
            rtf_sources.add(w.get("provenance", {}).get("source", f.stem))
            added += 1

    # assign stable sequential ids by type bucket (encyclopaedia keep their e-ids)
    counter = 0
    for w in works:
        if w["id"].startswith("sec_e"):
            continue
        counter += 1
        w["id"] = f"sec_r{counter:04d}"

    by_type = Counter(w["type"] for w in works)
    by_lang = Counter(w["language"] for w in works)
    by_source = Counter(w.get("containerAbbrev", "") for w in works if w.get("containerAbbrev"))

    base["works"] = works
    base["metadata"].update({
        "totalWorks": len(works),
        "lastUpdated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "sources": sorted({"info.xlsx"} | rtf_sources),
        "counts": {
            "byType": dict(by_type),
            "byLanguage": dict(by_lang),
            "bySource": dict(by_source),
        },
    })

    errors = validate_dataset(base, schema)
    if errors:
        print(f"DATASET INVALID — {len(errors)} error(s):")
        for e in errors[:30]:
            print("  -", e)
        raise SystemExit(1)

    SECONDARY.write_text(json.dumps(base, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Merged: +{added} RTF records, {len(dropped)} duplicates dropped, "
          f"{enc_covered} RTF encyclopaedia-entries dropped (canonical in info.xlsx)")
    print(f"Total works: {len(works)}")
    print(f"  byType: {dict(by_type)}")
    print(f"  byLanguage: {dict(by_lang)}")
    if dropped:
        print(f"\nDuplicates dropped (first 15 of {len(dropped)}):")
        for src, title in dropped[:15]:
            print(f"  [{src}] {title}")


if __name__ == "__main__":
    main()
