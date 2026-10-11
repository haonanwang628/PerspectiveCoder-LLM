import pandas as pd
import json
import ast

codes = pd.read_csv(r"F:\Work\Debate\MultiAgentDabateDataAnnotation1\Data\StorySeeker\orgin\codes.csv")
id, code = codes['Id'].tolist(), codes['Short Name'].tolist()

codes_dict = {}
for i in zip(id, code):
    codes_dict[i[0]] = i[1]

df = pd.read_csv(r"F:\Work\Debate\MultiAgentDabateDataAnnotation1\Data\StorySeeker\orgin\pc.csv")
col1, col2, col3 = df['goal'].tolist(), df['goal_codes'].tolist(), df['user'].tolist()
col4, col5 = df['rationale'].tolist(), df['rationale_codes'].tolist()
for i in range(len(col2)):
    col2[i] = ast.literal_eval(col2[i])
    for j in range(len(col2[i])):
        col2[i][j] = codes_dict[col2[i][j].replace("*", "").replace("!", "")]

for i in range(len(col5)):
    col5[i] = ast.literal_eval(col5[i])
    for j in range(len(col5[i])):
        col5[i][j] = codes_dict[col5[i][j].replace("*", "").replace("!", "")]

datas_goal, datas_rationale = [], []
for i in range(len(col1)):
    datas_goal.append({"participant": col3[i], "data_chunk": col1[i], "code": col2[i]})
for i in range(len(col4)):
    datas_rationale.append({"participant": col3[i], "data_chunk": col4[i], "code": col5[i]})
with open(r"F:\Work\Debate\MultiAgentDabateDataAnnotation1\Data\StorySeeker\processed\goal.json", "w",
          encoding="utf-8") as f:
    json.dump(datas_goal, f, indent=4)
with open(r"F:\Work\Debate\MultiAgentDabateDataAnnotation1\Data\StorySeeker\processed\rationale.json", "w",
          encoding="utf-8") as f:
    json.dump(datas_rationale, f, indent=4)
