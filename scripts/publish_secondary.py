#!/usr/bin/env python3
"""Phase 7 — split the master dataset into the published page data and the
review queue.

  data/sources/secondary_all.json   (master: every record, all phases)
        |
        +--> data/secondary.json                  reviewed==true  (deployed; the page fetches this)
        +--> data/sources/secondary_pending.json  reviewed==false (loaded by review/secondary-review.html)

Run this last, after merge + link. Re-run after each review round (feed the
review app's exported `secondary_reviewed.json` back into the master first).
"""
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from validate_secondary import load_schema, validate_dataset

ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "data" / "sources" / "secondary_all.json"
PUBLISHED = ROOT / "data" / "secondary.json"
PENDING = ROOT / "data" / "sources" / "secondary_pending.json"


def is_reviewed(w):
    return bool((w.get("provenance") or {}).get("reviewed"))


def counts(works):
    return {
        "byType": dict(Counter(w["type"] for w in works)),
        "byLanguage": dict(Counter(w["language"] for w in works)),
        "bySource": dict(Counter(w["containerAbbrev"] for w in works if w.get("containerAbbrev"))),
    }


def linked(works):
    return sum(1 for w in works if any(p.get("authorId") for p in (w.get("relatedPersons") or [])))


def write(path, works, label, extra=None):
    meta = {
        "totalWorks": len(works),
        "lastUpdated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "version": "1.0",
        "sources": sorted({(w.get("provenance") or {}).get("source", "?") for w in works}),
        "linkedWorks": linked(works),
        "counts": counts(works),
    }
    if extra:
        meta.update(extra)
    data = {"metadata": meta, "works": works}
    errors = validate_dataset(data, load_schema())
    if errors:
        raise SystemExit(f"{label} INVALID: {errors[0]}")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  {label:9s} -> {path.relative_to(ROOT)}  ({len(works)} works, {linked(works)} linked)")


def main():
    master = json.loads(MASTER.read_text(encoding="utf-8"))
    works = master["works"]
    published = [w for w in works if is_reviewed(w)]
    pending = [w for w in works if not is_reviewed(w)]

    print(f"Master: {len(works)} works -> {len(published)} published, {len(pending)} pending review")
    write(PUBLISHED, published, "published",
          {"sources": ["info.xlsx"], "pendingReview": len(pending)})
    write(PENDING, pending, "pending")


if __name__ == "__main__":
    main()
