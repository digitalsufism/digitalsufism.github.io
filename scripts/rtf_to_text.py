#!/usr/bin/env python3
"""Phase 3a — normalize old_bibliography/ RTF+TXT into clean, chunked text.

Uses macOS `textutil` to convert RTF -> UTF-8 plain text (diacritics and <i>
tags preserved), then splits each file into author-blocks (blank-line
separated). Within a block, lines beginning with an en/em dash are additional
works by the same author. Section headers (short lines, no terminal period,
not author-like) are recorded as the running section for the blocks that follow.

Outputs:
  data/sources/txt/<lang>.txt        cleaned plain text (audit trail)
  data/sources/chunks/<lang>.json    [{block_id, language, section, raw}]
"""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "old_bibliography"
TXT_DIR = ROOT / "data" / "sources" / "txt"
CHUNK_DIR = ROOT / "data" / "sources" / "chunks"

# filename fragment -> language label (matches schema enum)
FILES = {
    "English": "2019-07-03_Website_Secondary_English.rtf",
    "French": "2019-06-29_Website_Secondary_French.rtf",
    "Arabic": "2019-06-30_Website_Secondary_Arabic.rtf",
    "German": "2019-06-30_Website_Secondary_German.rtf",
    "Persian": "2019-07-16_Website_Secondary_Persian.rtf",
    "Turkish": "2019-07-23_Website_Secondary_Turkish.rtf",
    "Russian": "2019-07-16_Website_Secondary_NorthernEuropean.rtf",
    "EncyclopediaArticles": "2019-07-28_Website_Secondary_EncyclopediaArticles.rtf",
    "Italian": "2019-08-04_Website_Secondary_SoutherEurope.txt",
}


def to_text(path):
    if path.suffix.lower() == ".txt":
        text = path.read_text(encoding="utf-8", errors="replace")
    else:
        text = subprocess.run(
            ["textutil", "-convert", "txt", str(path), "-stdout"],
            capture_output=True, text=True, check=True,
        ).stdout
    # repair the known malformed italic tag in the Italian file
    text = text.replace("<i.R", "<i>R")
    # normalize newlines / non-breaking spaces
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    return text


def is_header(line):
    """Heuristic: short label line that introduces a section, not a citation."""
    s = line.strip()
    if not s or len(s) > 80:
        return False
    if s.endswith((".", ",", ")")):
        return False
    if "<i>" in s or "http" in s.lower():
        return False
    # citations almost always contain a year or page marker; headers do not
    if re.search(r"\b1[0-9]{3}\b|\bpp?\.", s):
        return False
    lowered = s.lower()
    keywords = ("source", "studies", "translation", "encyclop", "primary",
                "secondary", "articles", "edition", "monograph")
    return any(k in lowered for k in keywords)


def chunk_text(text, language):
    """Split cleaned text into author-blocks separated by blank lines."""
    blocks = []
    section = ""
    counter = 0
    for raw_block in re.split(r"\n\s*\n", text):
        block = raw_block.strip("\n")
        if not block.strip():
            continue
        lines = [ln for ln in block.split("\n") if ln.strip()]
        # a one-line block that looks like a header sets the running section
        if len(lines) == 1 and is_header(lines[0]):
            section = lines[0].strip()
            continue
        counter += 1
        blocks.append({
            "block_id": f"{language}_{counter:03d}",
            "language": language,
            "section": section,
            "raw": block.strip(),
        })
    return blocks


def main():
    TXT_DIR.mkdir(parents=True, exist_ok=True)
    CHUNK_DIR.mkdir(parents=True, exist_ok=True)
    summary = {}
    for language, fname in FILES.items():
        path = SRC / fname
        if not path.exists():
            print(f"  ! missing {fname}")
            continue
        text = to_text(path)
        (TXT_DIR / f"{language}.txt").write_text(text, encoding="utf-8")
        blocks = chunk_text(text, language)
        (CHUNK_DIR / f"{language}.json").write_text(
            json.dumps(blocks, ensure_ascii=False, indent=2), encoding="utf-8")
        summary[language] = len(blocks)
        print(f"  {language:22s} {len(blocks):4d} blocks")
    total = sum(summary.values())
    print(f"\nTotal author-blocks: {total}")


if __name__ == "__main__":
    main()
