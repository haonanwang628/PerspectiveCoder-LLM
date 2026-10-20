"""Read consecutive JSON records and format objects with inline lists."""

import json
from pathlib import Path


def read_records(path):
    """Accept both one-line records and consecutive multiline JSON objects."""
    text = Path(path).read_text(encoding="utf-8-sig")
    decoder = json.JSONDecoder()
    records = []
    offset = 0
    while offset < len(text):
        if text[offset].isspace():
            offset += 1
            continue
        record, offset = decoder.raw_decode(text, offset)
        records.append(record)
    return records


def format_record(value, level=0):
    """Indent object fields while keeping lists on a single line."""
    if not isinstance(value, dict) or not value:
        return json.dumps(value, ensure_ascii=False)
    indent = "    " * level
    fields = [
        f"{indent}    {json.dumps(key, ensure_ascii=False)}: "
        f"{format_record(item, level + 1)}"
        for key, item in value.items()
    ]
    return "{\n" + ",\n".join(fields) + "\n" + indent + "}"


def write_records(path, records):
    with Path(path).open("w", encoding="utf-8", newline="\n") as target:
        for record in records:
            target.write(format_record(record) + "\n")
