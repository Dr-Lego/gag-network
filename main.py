import os

steps = [
    "create_database.py",
    "transform_icons.py",
    "build.py",
    "minimize_build.py",
]

for step in steps:
    os.system(f"python3 {step}")