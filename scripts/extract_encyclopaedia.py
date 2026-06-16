#!/usr/bin/env python3
"""Phase 2 — ingest data/sources/info.xlsx (sufi-bios) into the secondary schema.

Maps the 638 curated encyclopaedia entries to encyclopaedia-entry records,
validates every record, and writes/merges into data/secondary.json.

Run:  python3 scripts/extract_encyclopaedia.py
"""
import json
import re
from datetime import datetime
from pathlib import Path

from xlsx_reader import read_rows
from validate_secondary import load_schema, validate_instance

ROOT = Path(__file__).resolve().parent.parent
SOURCE_XLSX = ROOT / "data" / "sources" / "info.xlsx"
OUT = ROOT / "data" / "sources" / "secondary_all.json"

# Encyclopaedia abbreviation -> (full container title, default language)
ENCYCLOPAEDIAS = {
    "DİA": ("Türkiye Diyanet Vakfı İslâm Ansiklopedisi", "Turkish"),
    "DMBI": ("Dāʾirat al-Maʿārif-i Buzurg-i Islāmī", "Persian"),
    "EI2": ("Encyclopaedia of Islam, 2nd ed.", "English"),
    "EI2 (Supplement)": ("Encyclopaedia of Islam, 2nd ed., Supplement", "English"),
    "EI3": ("Encyclopaedia of Islam, THREE", "English"),
    "EIr": ("Encyclopædia Iranica", "English"),
    "EIs": ("Encyclopaedia Islamica", "English"),
    "EAL": ("Encyclopedia of Arabic Literature", "English"),
    "EQ": ("Encyclopaedia of the Qurʾān", "English"),
}

# strip a single layer of enclosing quotation marks (straight or curly)
_QUOTES = '"“”‘’«»'


def clean_title(raw):
    t = (raw or "").strip()
    if t and t[0] in _QUOTES:
        t = t[1:]
    if t and t[-1] in _QUOTES:
        t = t[:-1]
    return t.strip()


def split_authors(raw):
    """Split an author cell like 'A and B' / 'A, B' into individual names."""
    raw = (raw or "").strip()
    if not raw:
        return []
    parts = re.split(r"\s+and\s+|;\s*", raw)
    return [{"name": p.strip()} for p in parts if p.strip()]


def row_to_work(row, index):
    source = (row.get("source") or "").strip()
    container, language = ENCYCLOPAEDIAS.get(source, (source, "Unknown"))
    cat = (row.get("cat") or "").strip()
    term = (row.get("term") or "").strip()

    work = {
        "id": f"sec_e{index:04d}",
        "type": "encyclopaedia-entry",
        "title": clean_title(row.get("title")),
        "authors": split_authors(row.get("author")),
        "container": container,
        "containerAbbrev": source,
        "language": language if language in _ALLOWED_LANGS else "Unknown",
        "subjectCategory": cat if cat in ("entity", "term") else "",
        "provenance": {
            "source": "info.xlsx",
            "sourceId": (row.get("id") or "").strip() or None,
            "annotator": (row.get("annotator") or "").strip() or None,
            "reviewed": True,
        },
    }

    translators = split_authors(row.get("trans"))
    if translators:
        work["translators"] = translators

    page = (row.get("page") or "").strip()
    if page:
        work["pages"] = page

    link = (row.get("link") or "").strip()
    if link:
        work["url"] = link

    bio_id = (row.get("bio_id") or "").strip()
    if cat == "entity" and term:
        related = {"name": term, "authorId": None}
        if bio_id:
            related["bioId"] = bio_id
        work["relatedPersons"] = [related]
    elif cat == "term" and term:
        work["notes"] = f"Subject term: {term}"

    if not work["title"]:
        # fall back to the headword if the article title cell was blank
        work["title"] = term or "[untitled encyclopaedia entry]"
    return work


_ALLOWED_LANGS = {
    "English", "French", "Arabic", "German", "Persian",
    "Turkish", "Italian", "Russian", "Multiple", "Unknown",
}


def main():
    rows = read_rows(SOURCE_XLSX)
    schema = load_schema()

    works = []
    errors = []
    for i, row in enumerate(rows, start=1):
        work = row_to_work(row, i)
        errs = validate_instance(work, schema)
        if errs:
            errors.append((work["id"], errs))
        works.append(work)

    if errors:
        print(f"VALIDATION FAILURES ({len(errors)}):")
        for wid, errs in errors[:20]:
            print(f"  {wid}: {errs[0]}")
        raise SystemExit(1)

    from collections import Counter
    by_source = Counter(w["containerAbbrev"] for w in works)
    by_lang = Counter(w["language"] for w in works)

    dataset = {
        "metadata": {
            "totalWorks": len(works),
            "lastUpdated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "version": "1.0",
            "sources": ["info.xlsx"],
            "counts": {
                "byType": {"encyclopaedia-entry": len(works)},
                "bySource": dict(by_source),
                "byLanguage": dict(by_lang),
            },
        },
        "works": works,
    }

    OUT.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(works)} encyclopaedia records -> {OUT.relative_to(ROOT)}")
    print(f"  by source:   {dict(by_source)}")
    print(f"  by language: {dict(by_lang)}")
    print(f"  entity: {sum(1 for w in works if w['subjectCategory']=='entity')}, "
          f"term: {sum(1 for w in works if w['subjectCategory']=='term')}")


if __name__ == "__main__":
    main()
