import json
from pathlib import Path


def find_missing_fields_depth_1(path_to_json_detailed_issues: str):
    def read(path: str):
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        return data['issues']

    data = read(path_to_json_detailed_issues) #path to json

    key_sets = set()
    for issue in data:
        key_sets.add(frozenset(issue.keys()))
    print(len(key_sets))

    # Sorted intersection
    intersection = set.intersection(*(set(ks) for ks in key_sets))
    print("Intersection:", sorted(intersection))

    # Sorted unique keys for each set
    for i, ks in enumerate(key_sets, start=1):
        unique_keys = ks - intersection
        print(f"Unique keys for set {i}:", sorted(unique_keys))

