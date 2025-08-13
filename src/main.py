from __future__ import annotations

from pathlib import Path
import sys

from src.inspector_git import IGLogReader, to_pretty_json

DEFAULT_PATH = "/home/alex/Work/BachelorThesis/Vortex/test_input/inspector_git/zeppelin.iglog"


def main() -> int:
    path = Path(DEFAULT_PATH)
    if not path.exists():
        print(f"Error: file not found: {path}")
        return 1

    reader = IGLogReader()
    try:
        gitlog = reader.read(path)
    except Exception as e:
        print(f"Error while reading {path}: {e}")
        return 2

    commits = gitlog.commits
    if not commits:
        print("No commits found in the .iglog file.")
        return 0

    # Print the first object (example)
    print(to_pretty_json(commits[0]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
