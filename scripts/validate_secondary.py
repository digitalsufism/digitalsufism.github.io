#!/usr/bin/env python3
"""Dependency-free validator for the secondary-scholarship dataset.

Implements the subset of JSON Schema Draft-07 used by scripts/secondary_schema.json:
type, required, additionalProperties (false), properties, enum, minLength,
minimum, pattern, items, and local $ref (#/definitions/...).

Usage:
    python3 scripts/validate_secondary.py data/secondary.json
or import validate_dataset() / validate_instance().
"""
import json
import re
import sys
from pathlib import Path

SCHEMA_PATH = Path(__file__).with_name("secondary_schema.json")


def _resolve(ref, root):
    if not ref.startswith("#/"):
        raise ValueError(f"Only local refs supported, got {ref!r}")
    node = root
    for part in ref[2:].split("/"):
        node = node[part]
    return node


def _type_ok(value, expected):
    types = expected if isinstance(expected, list) else [expected]
    for t in types:
        if t == "null" and value is None:
            return True
        if t == "object" and isinstance(value, dict):
            return True
        if t == "array" and isinstance(value, list):
            return True
        if t == "string" and isinstance(value, str):
            return True
        if t == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if t == "boolean" and isinstance(value, bool):
            return True
        if t == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
    return False


def _validate(value, schema, root, path, errors):
    if "$ref" in schema:
        _validate(value, _resolve(schema["$ref"], root), root, path, errors)
        return

    if "type" in schema and not _type_ok(value, schema["type"]):
        errors.append(f"{path}: expected type {schema['type']}, got {type(value).__name__}")
        return

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} not in allowed values {schema['enum']}")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: string shorter than minLength {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: {value!r} does not match pattern {schema['pattern']}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: {value} below minimum {schema['minimum']}")

    if isinstance(value, dict):
        for req in schema.get("required", []):
            if req not in value:
                errors.append(f"{path}: missing required property '{req}'")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in props:
                    errors.append(f"{path}: unexpected property '{key}'")
        for key, subval in value.items():
            if key in props:
                _validate(subval, props[key], root, f"{path}.{key}", errors)

    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            _validate(item, schema["items"], root, f"{path}[{i}]", errors)


def load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_instance(work, schema=None):
    """Validate a single work record against #/definitions/work. Returns error list."""
    schema = schema or load_schema()
    errors = []
    _validate(work, schema["definitions"]["work"], schema, "work", errors)
    return errors


def validate_dataset(data, schema=None):
    """Validate a full {metadata, works} dataset. Returns error list."""
    schema = schema or load_schema()
    errors = []
    _validate(data, schema, schema, "$", errors)
    return errors


def main(argv):
    if len(argv) != 2:
        print("usage: validate_secondary.py <dataset.json>", file=sys.stderr)
        return 2
    data = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    errors = validate_dataset(data)
    if errors:
        print(f"INVALID — {len(errors)} error(s):")
        for e in errors[:50]:
            print("  -", e)
        if len(errors) > 50:
            print(f"  ... and {len(errors) - 50} more")
        return 1
    print(f"VALID — {len(data.get('works', []))} works conform to schema")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
