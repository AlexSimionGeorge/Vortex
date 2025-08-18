import json
from pprint import pprint
from jira_miner.loader import LoadModels

def analyze_dicts(dict_list):
    if not dict_list:
        print("Empty list.")
        return

    # Step 1: Collect all key sets
    key_sets = set()
    for d in dict_list:
        key_sets.add(frozenset(d.keys()))

    # Step 2: Intersection of keys across all dicts
    intersection = set.intersection(*(set(s) for s in key_sets))

    print("Intersection keys:", intersection)
    print("="*40)

    # Step 3: Unique keys for each dict
    for i, keys in enumerate(key_sets, 1):
        unique = keys - intersection
        print(f"Dict {i} unique keys:", unique)


def main():
    statuses, types_, issues, users = LoadModels.read(
        "/home/alex/Work/BachelorThesis/Vortex/test-input/jira-miner/ZEPPELIN-detailed-issues.json"
    )

    # print("\n--- Issue Statuses ---")
    # pprint([status.model_dump() for status in statuses])
    #
    # print("\n--- Issue Types ---")
    # pprint([it.model_dump() for it in types_])

    print("\n--- Issues ---")
    pprint(users[0].model_dump())





if __name__ == "__main__":
        main()
