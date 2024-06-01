import os
import subprocess
import re
from pathlib import Path

exclude = ["./visualize/data/DATA.js", ".visualize/assets/standard_icons"]

files = [val.replace("./visualize", "./build") for sublist in [[os.path.join(i[0], j) for j in i[2]] for i in os.walk('./visualize')] for val in sublist if not [1 for e in exclude if val.startswith(e)]]

#create directory tree
for path in files:
    dir_path = os.path.dirname(path)
    os.makedirs(dir_path, exist_ok=True)

for file in files:
    original = file.replace("./build", "./visualize")
    if not ".min." in file and os.path.getsize(original) < 10**6:
        if file.endswith(".js"):
            continue
            print(file)
            terser = subprocess.check_output(["terser", original, "--c", "--m"]).decode().strip("\n")
            with open(file, "w", encoding="utf-8") as f:
                f.write(terser)
                f.close()
            previous_size = os.path.getsize(file)
            subprocess.call(["roadroller", file, "-o", file], stdout=subprocess.DEVNULL)
            if os.path.getsize(file) > previous_size:
                with open(file, "w", encoding="utf-8") as f:
                    f.write(terser)
                    f.close()
                    
        elif file.endswith(".html"):
            text = re.sub(r"(<!--[^-]*-->|\s|\n)+", r" ", open(original, "r", encoding="utf-8").read())
            text = re.sub(r" (?=<|$)|<\/[tl].>|<.p> *(<[p\/])| ?\/?(>)", r"\1\2", text, flags=re.IGNORECASE)
            with open(file, "w", encoding="utf-8") as f:
                f.write(text)
                f.close()
                
        elif file.endswith(".css"):
            text = re.sub(r"(\/\*[^\*]+?\*\/|\s)+", r" ", open(original, "r", encoding="utf-8").read())
            with open(file, "w", encoding="utf-8") as f:
                f.write(text)
                f.close()