from src.inspector_git.iglog.readers.ig_log_reader import IGLogReader

def main():
    path_inspector_git = "../test-input/inspector-git/zeppelin.iglog"

    reader = IGLogReader()

    with open(path_inspector_git, "r", encoding="utf-8") as stream:
        git_log = reader.read(stream)

    print(f"Număr commit-uri citite: {len(git_log.commits)}")
    for idx, commit in enumerate(git_log.commits[:5], start=1):  # afișăm doar primele 5 pentru test
        print(f"\nCommit {idx}:")
        print(f"  ID: {commit.id}")
        print(f"  Author: {commit.author_name} <{commit.author_email}>")
        print(f"  Date: {commit.author_date}")
        print(f"  Message: {commit.message.strip() if commit.message else ''}")

if __name__ == "__main__":
    main()
