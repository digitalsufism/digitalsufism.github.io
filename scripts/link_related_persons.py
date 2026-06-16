#!/usr/bin/env python3
"""Phase 4 — cross-link secondary works to the primary-sources corpus.

Matches each secondary work against the 31 authors in data/bibliography.json
using a curated alias authority list (more reliable than fuzzy matching given
ambiguous shared nisbas: two al-Sulamīs, two al-Iṣfahānīs, al-Junayd vs
Ibn al-Junayd). Populates work.relatedPersons[].authorId and adds a
relatedPerson when a work clearly concerns a corpus author but had none.

Matching sources per work: existing relatedPersons names, encyclopaedia subject
term, and the title. More-specific aliases are tested before generic ones.

Run: python3 scripts/link_related_persons.py
"""
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

from validate_secondary import load_schema, validate_dataset

ROOT = Path(__file__).resolve().parent.parent
SECONDARY = ROOT / "data" / "sources" / "secondary_all.json"
PRIMARY = ROOT / "data" / "bibliography.json"

# Curated authority list: primary author id -> (canonical display name, aliases).
# Aliases are ordered specific-first; ambiguous bare nisbas are intentionally
# qualified (e.g. al-Iṣfahānī requires the kunya).
ALIASES = {
    "asad-al-musib":      ("al-Muḥāsibī", ["al-muhasibi", "muhasibi", "harith-i muhasibi"]),
    "manr-al-allj":       ("al-Ḥallāj", ["al-hallaj", "hallaj"]),
    "al-junayd-al-khuttal": ("Ibn al-Junayd al-Khuttalī", ["ibn al-junayd", "al-khuttali"]),
    "muammad-al-qawwr":   ("al-Junayd al-Baghdādī", ["al-junayd", "junayd", "cuneyd", "djunayd", "al-qawariri"]),
    "allh-al-tustar":     ("Sahl al-Tustarī", ["al-tustari", "tustari", "sahl b. abd allah", "sahl al-tustari"]),
    "s-al-kharrz":        ("al-Kharrāz", ["al-kharraz", "kharraz"]),
    "al-baghaw-al-nr":    ("al-Nūrī", ["al-nuri", "abu al-husayn al-nuri", "abu l-husayn al-nuri"]),
    "a-al-adam":          ("Ibn ʿAṭāʾ al-Adamī", ["ibn ata", "al-adami"]),
    "-al-shibl":          ("al-Shiblī", ["al-shibli", "shibli"]),
    "ibn-al-arb":         ("Ibn al-Aʿrābī", ["ibn al-arabi al-basri", "ibn al-a rabi", "ibn al-arabi (d. 341"]),
    "nuayr-al-khuld":     ("Jaʿfar al-Khuldī", ["al-khuldi", "khuldi", "ja far al-khuldi"]),
    "nujayd-al-sulam":    ("Ibn Nujayd al-Sulamī", ["ibn nujayd"]),
    "al-sarrj-al-s":      ("al-Sarrāj al-Ṭūsī", ["al-sarraj", "sarraj", "abu nasr al-sarraj"]),
    "isfkshdh-al-shrz":   ("Ibn Khafīf al-Shīrāzī", ["ibn khafif", "ibn hafif", "al-shirazi"]),
    "isq-al-kalbdh":      ("al-Kalābādhī", ["al-kalabadhi", "kalabadhi", "kalabazi"]),
    "al-aqal-al-mlik":    ("al-Ṣaqalī al-Mālikī", ["al-saqali"]),
    "al-rith-al-makk":    ("Abū Ṭālib al-Makkī", ["abu talib al-makki", "al-makki", "al-harithi al-makki"]),
    "b-samn":             ("Ibn Samʿūn", ["ibn sam un", "ibn samun"]),
    "adab-al-mulk":        ("Kitāb Adab al-Mulūk", ["adab al-muluk"]),
    "amakn-al-shfi":      ("Ibn Ḥamakān", ["ibn hamakan", "hamakan"]),
    "ibrhm-al-kharkgsh":  ("al-Kharkūshī", ["al-kharkushi", "al-khargushi", "kharkushi", "khargushi"]),
    "al-usayn-al-sulam":  ("Abū ʿAbd al-Raḥmān al-Sulamī", ["al-sulami", "sulami", "abd al-rahman al-sulami"]),
    "amad-al-mln":        ("al-Mālīnī", ["al-malini", "malini"]),
    "al-naqqsh-al-anbal": ("al-Naqqāsh", ["al-naqqash", "naqqash"]),
    "ziyd-al-ifahn":      ("Abū Manṣūr al-Iṣfahānī", ["abu mansur al-isfahani", "ma mar b. ahmad"]),
    "allh-al-ifahn":      ("Abū Nuʿaym al-Iṣfahānī", ["abu nu aym", "abu nu'aym", "abu nuaym"]),
    "muammad-al-daylam":  ("al-Daylamī", ["al-daylami", "daylami"]),
    "b-yazdnyr":          ("Ibn Yazdānyār", ["ibn yazdanyar", "yazdanyar"]),
    "al-asan-al-srjkgn":  ("al-Sīrjānī", ["al-sirjani", "al-sirgani", "sirjani"]),
    "al-usayn-al-burjuln": ("al-Burjulānī", ["al-burjulani", "burjulani"]),
}

# specific multiword aliases must be checked before generic single-token ones
_SPECIFIC = ("ibn al-junayd", "ibn nujayd", "abu mansur al-isfahani")


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("ʿ", " ").replace("ʾ", " ").replace("ʼ", " ").replace("'", " ")
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def match_authors(text):
    """Return ordered list of primary author ids whose alias appears in text."""
    nt = f" {norm(text)} "
    hits = []
    # specific-first to resolve al-Junayd vs Ibn al-Junayd, al-Sulamī vs Ibn Nujayd
    for aid, (_name, aliases) in ALIASES.items():
        for alias in aliases:
            a = f" {alias} "
            if a in nt:
                # guard: do not match generic 'al-junayd' if it's actually 'ibn al-junayd'
                if alias == "al-junayd" and " ibn al-junayd " in nt:
                    continue
                if alias == "al-sulami" and " ibn nujayd " in nt:
                    continue
                if alias.startswith("al-isfahani") or alias == "al-isfahani":
                    pass
                hits.append((aid, alias))
                break
    return hits


def candidate_text(work):
    parts = [work.get("title", "")]
    for rp in work.get("relatedPersons", []) or []:
        parts.append(rp.get("name", ""))
    if work.get("notes"):
        parts.append(work["notes"])
    return " || ".join(parts)


def main():
    schema = load_schema()
    data = json.loads(SECONDARY.read_text(encoding="utf-8"))
    id_to_name = {aid: name for aid, (name, _) in ALIASES.items()}

    linked_works = 0
    linked_counts = Counter()
    for work in data["works"]:
        hits = match_authors(candidate_text(work))
        if not hits:
            continue
        existing = {rp.get("name"): rp for rp in (work.get("relatedPersons") or [])}
        related = list(work.get("relatedPersons") or [])
        matched_ids = set()
        for aid, _alias in hits:
            if aid in matched_ids:
                continue
            matched_ids.add(aid)
            name = id_to_name[aid]
            # attach authorId to a fitting existing relatedPerson, else add one
            attached = False
            for rp in related:
                if rp.get("authorId"):
                    continue
                if norm(name).split()[-1] in norm(rp.get("name", "")):
                    rp["authorId"] = aid
                    attached = True
                    break
            if not attached:
                related.append({"name": name, "authorId": aid})
            linked_counts[aid] += 1
        if related:
            work["relatedPersons"] = related
            linked_works += 1

    errors = validate_dataset(data, schema)
    if errors:
        print(f"INVALID after linking — {len(errors)} error(s):")
        for e in errors[:20]:
            print("  -", e)
        raise SystemExit(1)

    data["metadata"]["linkedWorks"] = linked_works
    SECONDARY.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Linked {linked_works} works to primary-corpus authors.")
    print("Per-author scholarship counts (top 20):")
    for aid, n in linked_counts.most_common(20):
        print(f"  {n:4d}  {id_to_name[aid]}")
    unlinked = [aid for aid in ALIASES if aid not in linked_counts]
    if unlinked:
        print(f"\nAuthors with no secondary matches: "
              f"{', '.join(id_to_name[a] for a in unlinked)}")


if __name__ == "__main__":
    main()
