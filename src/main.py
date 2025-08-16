import json
from pathlib import Path
from pprint import pprint

from jira_miner.loader import LoadModels


def main():
    statuses, types_, issues = LoadModels.read(
        "/home/alex/Work/BachelorThesis/Vortex/test-input/jira-miner/ZEPPELIN-detailed-issues.json"
    )

    # print("\n--- Issue Statuses ---")
    # pprint([status.model_dump() for status in statuses])
    #
    # print("\n--- Issue Types ---")
    # pprint([it.model_dump() for it in types_])

    print("\n--- Issues ---")
    # print(type(issues[0].subTasks))
    # pprint(issues[0].subTasks)


    for issue in issues:
        if issue.parent and len(issue.parent) > 16:
            # print(type(issue.creatorId))
            pprint(issue.parent)





if __name__ == "__main__":
    if False:
        helper("/home/alex/Work/BachelorThesis/Vortex/test-input/jira-miner/ZEPPELIN-detailed-issues.json", "comments")
    else:
        main()

