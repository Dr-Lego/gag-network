import sys
import subprocess

DATA_STEPS = [
    "create_database.py",
    "transform_icons.py",
    "build.py --data"
]

PRELOAD_STEPS = [
    "build.py --preload",
    "cd frontend && npm run build && cd .."
]

def run_steps(steps):
    for step in steps:
        print(f"Executing: {step}")
        if ".py" in step:
            result = subprocess.run(f"python3 {step}", shell=True, check=False)
        else:
            result = subprocess.run(step, shell=True, check=False)
        if result.returncode != 0:
            print(f"Error: '{step}' failed with return code {result.returncode}")
            sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--data":
            run_steps(DATA_STEPS)
        elif sys.argv[1] == "--preload":
            run_steps(PRELOAD_STEPS)
        else:
            print("Invalid argument. Use --data or --preload.")
    else:
        run_steps(DATA_STEPS)
        run_steps(PRELOAD_STEPS)
    print("All steps completed successfully.")