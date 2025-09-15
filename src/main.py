from pathlib import Path

from src.inspector_git.linker.transformers import GitProjectTransformer
from src.inspector_git.reader.iglog.readers.ig_log_reader import IGLogReader

# 🔹 1. Set the path to a single .iglog file
iglog_path = Path("../test-input/inspector-git/TestInspectorGitRepo.iglog")

# 🔹 2. Read the IGLog file
with open(iglog_path, "r", encoding="utf-8") as f:
    git_log_dto = IGLogReader().read(f)

# 🔹 3. Transform into a project (compute_annotated_lines=True)
transformer = GitProjectTransformer(
    git_log_dto,
    name=iglog_path.stem,
    compute_annotated_lines=True,
)
project = transformer.transform()

# # 🔹 4. Collect annotated lines from all changes
# results = {}
# for commit in project.commit_registry.all:
#     if commit.is_merge_commit:
#         continue
#     for change in commit.changes:
#         results[f"{change.file.path}@{commit.id}"] = {
#             "annotatedLines": [
#                 {
#                     "lineNumber": line.line_number,
#                     "author": line.author,
#                     "commitId": line.commit.id if line.commit else None,
#                 }
#                 for line in change.annotated_lines
#             ]
#         }
#
# # 🔹 5. Save to JSON
# output_path = iglog_path.parent / "output.json"
# with open(output_path, "w", encoding="utf-8") as out:
#     json.dump(results, out, indent=2)
#
# print(f"Results written to {output_path}")
