"""
File Minimization and Compression Script

This script minimizes JavaScript, HTML, and CSS files, and compresses the build directory.
"""

import os
import subprocess
import re
import sys

def minimize(*args):
    """
    Minimizes JavaScript, HTML, and CSS files in the visualize directory and copies them to the build directory.

    Args:
        *args: Variable length argument list (not used in the function).
    """
    exclude = ["./visualize/assets/standard_icons"]

    files = [val.replace("./visualize", "./build") for sublist in [[os.path.join(i[0], j) for j in i[2]] for i in os.walk('./visualize')] for val in sublist if not [1 for e in exclude if val.startswith(e)]]

    # Create directory tree
    for path in files:
        dir_path = os.path.dirname(path)
        os.makedirs(dir_path, exist_ok=True)

    for file in files:
        original = file.replace("./build", "./visualize")
        if file.endswith(".js") and os.path.getsize(original) < 40000 and ".min." not in file:
            print(file)
            terser = subprocess.check_output(["terser", original, "--c", "--m", "reserved=['$','DATA', 'SAVE']"]).decode().strip("\n")
            with open(file, "w", encoding="utf-8") as f:
                f.write(terser)
            previous_size = os.path.getsize(file)
            subprocess.call(["roadroller", file, "-o", file], stdout=subprocess.DEVNULL)
            if os.path.getsize(file) > previous_size:
                with open(file, "w", encoding="utf-8") as f:
                    f.write(terser)
        elif file.endswith(".html") and not file.startswith("_"):
            text = re.sub(r"(<!--[^-]*-->|\s|\n)+", r" ", open(original, "r", encoding="utf-8").read())
            text = re.sub(r" (?=<|$)|<\/[tl].>|<.p> *(<[p\/])| ?\/?(>)", r"\1\2", text, flags=re.IGNORECASE)
            with open(file, "w", encoding="utf-8") as f:
                f.write(text)
        elif file.endswith(".css"):
            text = re.sub(r"(\/\*[^\*]+?\*\/|\s)+", r" ", open(original, "r", encoding="utf-8").read())
            with open(file, "w", encoding="utf-8") as f:
                f.write(text)
        elif not file.endswith("data.js"):
            data = open(original, "rb").read()
            with open(file, "wb") as f:
                f.write(data)

def compress(input: str, output: str = None):
    """
    Compresses the input directory into a zip file.

    Args:
        input (str): The input directory to compress.
        output (str, optional): The output zip file name. If not provided, uses input name with .zip extension.
    """
    output = output if output else input + ".zip"
    os.system(f"zip -r {output} {input}")

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 0:
        minimize()
        compress("build")
    else:
        options = ["--minimize", "--zip"]
        for option in options:
            if option in args:
                {"--minimize": minimize, "--zip": compress}[option]("build")