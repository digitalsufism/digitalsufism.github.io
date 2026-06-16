#!/usr/bin/env python3
"""Dependency-free .xlsx reader (first worksheet only).

Returns a list of dict rows keyed by the header row. Handles shared strings
and inline strings; empty cells are returned as "".
"""
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

_NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_T = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"


def _col_letters(ref):
    return "".join(ch for ch in ref if ch.isalpha())


def _shared_strings(zf):
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    return ["".join(t.text or "" for t in si.iter(_T)) for si in root]


def _cell_value(cell, strings):
    v = cell.find("a:v", _NS)
    if v is None:
        is_el = cell.find("a:is", _NS)
        if is_el is not None:
            return "".join(t.text or "" for t in is_el.iter(_T))
        return ""
    if cell.get("t") == "s":
        return strings[int(v.text)]
    return v.text or ""


def read_rows(path):
    """Read first worksheet of an .xlsx file into a list of dict rows."""
    with zipfile.ZipFile(Path(path)) as zf:
        strings = _shared_strings(zf)
        # locate first worksheet part
        sheet_name = next(
            n for n in zf.namelist()
            if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")
        )
        root = ET.fromstring(zf.read(sheet_name))
    rows = root.find("a:sheetData", _NS).findall("a:row", _NS)
    if not rows:
        return []

    def cells(row):
        out = {}
        for c in row.findall("a:c", _NS):
            out[_col_letters(c.get("r"))] = _cell_value(c, strings)
        return out

    header = cells(rows[0])
    col_to_name = {col: name for col, name in header.items()}
    records = []
    for row in rows[1:]:
        rc = cells(row)
        record = {name: "" for name in col_to_name.values()}
        for col, val in rc.items():
            if col in col_to_name:
                record[col_to_name[col]] = val
        records.append(record)
    return records


if __name__ == "__main__":
    import sys
    from collections import Counter

    recs = read_rows(sys.argv[1])
    print(f"{len(recs)} rows; columns: {list(recs[0].keys()) if recs else []}")
    if len(sys.argv) > 2:
        col = sys.argv[2]
        print(Counter(r.get(col, "") for r in recs).most_common(20))
