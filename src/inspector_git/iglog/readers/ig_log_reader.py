from src.inspector_git.dto.gitlog.commit_dto import CommitDTO
from src.inspector_git.dto.gitlog.git_log_dto import GitLogDTO
from src.inspector_git.iglog.iglog_constants import IGLogConstants
from src.inspector_git.iglog.readers.ig_commit_reader import IGCommitReader


class IGLogReader:
    def __init__(self, commit_reader: IGCommitReader | None = None):
        self.commit_reader = commit_reader or IGCommitReader()

    def read(self, stream) -> GitLogDTO:
        """
        Citește un stream (InputStream) și returnează un obiect GitLogDTO.
        """
        reader = stream if hasattr(stream, "readline") else open(stream, "r", encoding="utf-8")
        iglog_version = reader.readline().strip()

        current_commit_lines: list[str] = []
        commits: list[CommitDTO] = []

        for line in reader:
            line = line.rstrip("\n")
            if line.startswith(IGLogConstants.commit_id_prefix):
                if current_commit_lines:
                    commits.append(self.commit_reader.read(current_commit_lines))
                current_commit_lines = []
            current_commit_lines.append(line)

        if current_commit_lines:
            commits.append(self.commit_reader.read(current_commit_lines))

        return GitLogDTO(commits)
