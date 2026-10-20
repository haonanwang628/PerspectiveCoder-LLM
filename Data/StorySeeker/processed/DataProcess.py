import pandas as pd
import json
import ast
from pathlib import Path

processed_dir = Path(__file__).resolve().parent
source_dir = processed_dir.parent / "orgin"

codes = pd.read_csv(source_dir / "codes.csv")
id, code = codes['Id'].tolist(), codes['Short Name'].tolist()

codes_dict = {}
for i in zip(id, code):
    codes_dict[i[0]] = i[1]

def decode_code(code):
    # Preserve negation while retaining the existing handling of "*".
    code_id = code.replace("*", "")
    is_negative = code_id.startswith("!")
    if is_negative:
        code_id = code_id[1:]
    code_name = codes_dict[code_id]
    return f"NOT_{code_name}" if is_negative else code_name


df = pd.read_csv(source_dir / "pc.csv")
col1, col2, col3 = df['goal'].tolist(), df['goal_codes'].tolist(), df['user'].tolist()
col4, col5 = df['rationale'].tolist(), df['rationale_codes'].tolist()
for i in range(len(col2)):
    col2[i] = ast.literal_eval(col2[i])
    for j in range(len(col2[i])):
        # col2[i][j] = codes_dict[col2[i][j].replace("*", "").replace("!", "")]
        col2[i][j] = decode_code(col2[i][j])

for i in range(len(col5)):
    col5[i] = ast.literal_eval(col5[i])
    for j in range(len(col5[i])):
        # col5[i][j] = codes_dict[col5[i][j].replace("*", "").replace("!", "")]
        col5[i][j] = decode_code(col5[i][j])

datas_goal, datas_rationale = [], []
for i in range(len(col1)):
    datas_goal.append({"participant": col3[i], "data_chunk": col1[i], "code": col2[i]})
for i in range(len(col4)):
    datas_rationale.append({"participant": col3[i], "data_chunk": col4[i], "code": col5[i]})
# Preserve the existing JSON files' CRLF line endings.
with open(processed_dir / "goal.json", "w",
          encoding="utf-8", newline="\r\n") as f:
    json.dump(datas_goal, f, indent=4)
with open(processed_dir / "rationale.json", "w",
          encoding="utf-8", newline="\r\n") as f:
    json.dump(datas_rationale, f, indent=4)
