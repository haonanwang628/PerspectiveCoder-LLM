import argparse
import ast
import json
from pathlib import Path

from openpyxl import Workbook

if __package__:
    from .baseline1_json_to_excel import (
        CODE_COLUMNS, add_sheet, codebook_rows, save_workbook,
    )
else:
    from baseline1_json_to_excel import (
        CODE_COLUMNS, add_sheet, codebook_rows, save_workbook,
    )


def parse_payload(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return ast.literal_eval(value)
    return value


def flatten_row(record, prefix=""):
    row = {}
    for key, value in record.items():
        name = f"{prefix}/{key}" if prefix else CODE_COLUMNS.get(key, key)
        if isinstance(value, dict):
            row.update(flatten_row(value, name))
        else:
            row[name] = value
    return row


def add_grouped_sheet(workbook, title, groups):
    rows, ranges = [], []
    for metadata, entries in groups:
        start = len(rows) + 2
        rows.extend({**metadata, **entry} for entry in (entries or [{}]))
        ranges.append((start, len(rows) + 1, metadata))
    sheet = add_sheet(workbook, title, rows)
    columns = {cell.value: cell.column for cell in sheet[1]}
    for start, end, metadata in ranges:
        if start < end:
            for key in metadata:
                sheet.merge_cells(
                    start_row=start, end_row=end,
                    start_column=columns[key], end_column=columns[key],
                )
    return sheet


def role_groups(members):
    fields = list(dict.fromkeys(
        key for member in members for key in member if key != "init_codebook"
    ))
    labels = {"role": "Role", "positionality": "Positionality"}
    for index, member in enumerate(members, 1):
        metadata = {"Agent": f"Role{index}"}
        metadata.update({labels.get(key, key): member.get(key, "") for key in fields})
        yield metadata, codebook_rows(member.get("init_codebook", []))


def section_groups(sections):
    labels = {
        "agreements": "Agreement",
        "disagreements": "Disagreement",
        "discussion_results": "Discussion Result",
        "decision_agreement_codebook": "Decision Agreement",
    }
    for section, entries in sections.items():
        if not entries:
            continue
        if not isinstance(entries, list):
            entries = [entries]
        rows = [
            flatten_row(entry) if isinstance(entry, dict) else {"Value": entry}
            for entry in entries
        ]
        yield {"Type": labels.get(section, section)}, rows


def round_groups(payload):
    for block in parse_payload(payload):
        for agent, response in block.items():
            field = next((key for key in (
                "Disagreement_Evidence", "Reasoning", "Final_Results"
            ) if key in response), None)
            metadata = {"Agent": agent}
            metadata.update(flatten_row({
                key: value for key, value in response.items() if key != field
            }))
            entries = [flatten_row(item) for item in response.get(field, [])]
            yield metadata, entries


def convert_discuss(input_file, output_file=None):
    input_file = Path(input_file)
    output_file = Path(output_file) if output_file else input_file.with_suffix(".xlsx")
    with input_file.open(encoding="utf-8-sig") as source:
        data = json.load(source)

    workbook = Workbook()
    workbook.remove(workbook.active)
    add_grouped_sheet(workbook, "Role_Team", role_groups(data["Role_Team"]))
    add_grouped_sheet(
        workbook, "Agreed_disagreed_codebook",
        section_groups(data["Agreed_disagreed_codebook"]),
    )
    for name, payload in data.get("Discussion", {}).items():
        add_grouped_sheet(workbook, name, round_groups(payload))

    if data.get("Decision_agreed_codebook"):
        decision = parse_payload(data["Decision_agreed_codebook"])
        groups = section_groups(decision) if isinstance(decision, dict) else round_groups(decision)
        add_grouped_sheet(workbook, "Decision_agreed_codebook", groups)

    add_sheet(
        workbook, "Final_codebook", codebook_rows(data["Final_codebook"]),
        columns=list(CODE_COLUMNS.values()),
    )
    if "current_num_token" in data:
        add_sheet(workbook, "current_num_token", [data["current_num_token"]])
    return save_workbook(workbook, output_file)


def main():
    parser = argparse.ArgumentParser(description="Convert discussion results from JSON to Excel.")
    parser.add_argument("-i", "--input", required=True, type=Path, help="Input JSON file")
    parser.add_argument("-o", "--output", type=Path, help="Output XLSX file (default: beside input)")
    args = parser.parse_args()
    print(f"Saved: {convert_discuss(args.input, args.output)}")


if __name__ == "__main__":
    main()
