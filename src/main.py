from __future__ import annotations
import json
from pathlib import Path
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

    i = 0
    while i < len(gitlog.commits):
        commit = gitlog.commits[i]
        if len(commit.parent_ids) >= 2:
            break
        i += 1

    output_path = Path(f"commit_{i}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        print(to_pretty_json(gitlog.commits[i]), file=f)

    print(f"Full gitlog data written to {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
