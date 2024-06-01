import json

with open("miscellaneous/test.js", "w", encoding="utf-8") as f:
    f.write("const test = " + json.dumps({"nodäs": 1, "edßes": 2, "möta": "ü"}, separators=(",", ":"), ensure_ascii=False))
    f.close()