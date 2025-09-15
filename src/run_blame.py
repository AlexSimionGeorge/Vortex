import subprocess
import os

# ========= CONFIG =========
project_name = "TestInspectorGitRepo"  # set your project name here
repo_path = "/home/vortex/Work/BachelorThesis/TestInspectorGitRepo"  # path to the repo (NOT the .git folder, just the root)
# ==========================

def run_git_command(args):
    """Run a git command inside the repo and return stdout."""
    result = subprocess.run(
        ["git", "-C", repo_path] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Git command failed: {' '.join(args)}\n{result.stderr}")
    return result.stdout.strip()

def is_binary_file(filepath):
    """Check if Git considers a file binary."""
    result = subprocess.run(
        ["git", "-C", repo_path, "check-attr", "binary", "--", filepath],
        stdout=subprocess.PIPE,
        text=True
    )
    return "binary: set" in result.stdout

import re

def parse_blame_file(path):
    results = {}

    current_file = None
    line_pattern = re.compile(
        r'^\^?([0-9a-f]+)\s+\((.*?)\s*<(.*?)>.*?(\d+)\)'
    )

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")

            # Detect new file section
            if line.endswith("~~~>"):
                current_file = line.replace(" ~~~>", "").strip()
                results[current_file] = []
                continue

            if not line or current_file is None:
                continue

            match = line_pattern.match(line)
            if match:
                sha, name, email, line_idx = match.groups()
                sha = sha.lstrip("^")  # strip caret if present
                results[current_file].append({
                    "sha": sha,
                    "email": email.strip(),
                    "line_index": int(line_idx)
                })

    return results


def main():
    # Output file path (next to this script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, f"{project_name}_blame.txt")

    with open(output_file, "w", encoding="utf-8") as out:
        # List tracked files
        files = run_git_command(["ls-files"]).splitlines()

        for f in files:
            if is_binary_file(f):
                continue  # skip binary files

            out.write(f"{f} ~~~>\n")

            blame_output = run_git_command(["blame", "--show-email", f])
            out.write(blame_output + "\n\n")

    print(f"Blame output saved to {output_file}")

if __name__ == "__main__":
    main()
