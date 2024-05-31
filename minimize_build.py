import os
import subprocess
from pathlib import Path

files = [val for sublist in [[os.path.join(i[0], j) for j in i[2]] for i in os.walk('./visualize')] for val in sublist]

for path in files:
    dir_path = os.path.dirname(path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    open(path, 'w').close() # Create an empty file

for file in files:
    if file.endswith(".js"):
        with open("build/js/script.js", "w") as f:
            f.write(subprocess.check_output(["terser", "./visualize/js/script.js", "--c", "--m"]).decode().strip("\n"))
            f.close()
    
        print(subprocess.check_output(["roadroller", "./visualize/js/script.js"]))