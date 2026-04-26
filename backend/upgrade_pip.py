import os
import subprocess
import sys

def main():
    log_file = os.path.join(os.path.dirname(__file__), "upgrade_log.txt")
    try:
        # Run pip install --upgrade google-generativeai
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "google-generativeai"],
            capture_output=True,
            text=True
        )
        with open(log_file, "w") as f:
            f.write("=== STDOUT ===\n")
            f.write(result.stdout)
            f.write("\n=== STDERR ===\n")
            f.write(result.stderr)
        print("Upgrade finished. Check upgrade_log.txt")
    except Exception as e:
        with open(log_file, "w") as f:
            f.write("ERROR:\n" + str(e))
        print("Error occurred. Check upgrade_log.txt")

if __name__ == "__main__":
    main()
