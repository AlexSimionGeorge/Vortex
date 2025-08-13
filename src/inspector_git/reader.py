from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Deque, List, Tuple

from src.inspector_git.data_structures.constants import IGLogConstants
from src.inspector_git.data_structures.models import (
    ChangeDTO,
    ChangeType,
    CommitDTO,
    GitLogDTO,
    HunkDTO,
    LineChangeDTO,
    LineOperation,
)


class IGLogReader:
    def read(self, file_path: str | Path) -> GitLogDTO:
        p = Path(file_path)
        with p.open("r", encoding="utf-8") as f:
            return self.read_stream(p.stem, f)

    def read_stream(self, name: str, stream) -> GitLogDTO:
        current_commit_lines: Deque[str] = deque()
        commits: List[CommitDTO] = []

        first_line = stream.readline()
        ig_log_version: str | None = first_line.rstrip("\n\r") if first_line else None

        while True:
            line = stream.readline()
            if not line:
                break
            line = line.rstrip("\n\r")

            if line.startswith(IGLogConstants.CommitIdPrefix):
                if current_commit_lines:
                    commits.append(self._read_commit(current_commit_lines))
                current_commit_lines = deque()

            current_commit_lines.append(line)

        if current_commit_lines:
            commits.append(self._read_commit(current_commit_lines))

        return GitLogDTO(ig_log_version=ig_log_version, name=name, commits=commits)

    def _read_commit(self, lines: Deque[str]) -> CommitDTO:
        id_line = lines.popleft()
        commit_id = id_line[len(IGLogConstants.CommitIdPrefix) :]
        parent_ids_line = lines.popleft()
        parent_ids = parent_ids_line.split(" ") if parent_ids_line else []
        author_date = lines.popleft()
        author_email = lines.popleft()
        author_name = lines.popleft()

        committer_date = author_date
        committer_email = author_email
        committer_name = author_name

        # Peek next line without removing
        next_line = lines[0] if lines else ""
        if next_line.startswith(IGLogConstants.MessagePrefix):
            message = self._extract_message(lines)
        else:
            committer_date = lines.popleft() if lines else committer_date
            committer_email = lines.popleft() if lines else committer_email
            committer_name = lines.popleft() if lines else committer_name
            message = self._extract_message(lines)

        current_change_lines: Deque[str] = deque()
        changes: List[ChangeDTO] = []
        for line in list(lines):
            if line.startswith(IGLogConstants.ChangePrefix):
                if current_change_lines:
                    changes.append(self._read_change(current_change_lines))
                current_change_lines = deque()
            current_change_lines.append(line)

        if current_change_lines:
            changes.append(self._read_change(current_change_lines))

        return CommitDTO(
            id=commit_id,
            parent_ids=parent_ids,
            author_date=author_date,
            author_email=author_email,
            author_name=author_name,
            committer_date=committer_date,
            committer_email=committer_email,
            committer_name=committer_name,
            message=message,
            changes=changes,
        )

    def _extract_message(self, lines: Deque[str]) -> str:
        parts: List[str] = []
        while lines and lines[0].startswith(IGLogConstants.MessagePrefix):
            next_line = lines.popleft()
            parts.append(next_line[len(IGLogConstants.MessagePrefix) :])
        return "\n".join(parts).strip()

    def _read_change(self, lines: Deque[str]) -> ChangeDTO:
        first = lines.popleft()
        change_type, binary = self._get_change_type(first[1:])  # remove '#'
        parent_commit_id = lines.popleft() if lines else ""
        old_file_name, new_file_name = self._get_file_name(lines, change_type)

        hunks: List[HunkDTO] = []
        if not binary:
            for line in list(lines):
                if line.startswith(IGLogConstants.HunkPrefixLine + "="):
                    hunks.append(self._read_hunk(line[2:]))

        return ChangeDTO(
            old_file_name=old_file_name.strip(),
            new_file_name=new_file_name.strip(),
            type=change_type,
            parent_commit_id=parent_commit_id,
            binary=binary,
            hunks=hunks,
        )

    def _get_change_type(self, line: str) -> Tuple[ChangeType, bool]:
        binary = len(line) > 1
        c = line[0] if line else "M"
        if c == "A":
            return ChangeType.Add, binary
        if c == "D":
            return ChangeType.Delete, binary
        if c == "R":
            return ChangeType.Rename, binary
        return ChangeType.Modify, binary

    def _get_file_name(self, lines: Deque[str], type_: ChangeType) -> Tuple[str, str]:
        file_name = lines.popleft() if lines else ""
        if type_ == ChangeType.Add:
            return IGLogConstants.DevNull, file_name
        if type_ == ChangeType.Delete:
            return file_name, IGLogConstants.DevNull
        if type_ == ChangeType.Rename:
            new_name = lines.popleft() if lines else ""
            return file_name, new_name
        if type_ == ChangeType.Modify:
            return file_name, file_name
        raise ValueError(f"Unknown change type: {type_}")

    def _read_hunk(self, hunk_line: str) -> HunkDTO:
        split = hunk_line.split("|")
        added_ranges = split[0] if len(split) > 0 else "0"
        deleted_ranges = split[1] if len(split) > 1 else "0"
        return HunkDTO(
            added_line_changes=self._parse_line_ranges(added_ranges, LineOperation.Add),
            deleted_line_changes=self._parse_line_ranges(deleted_ranges, LineOperation.Delete),
        )

    def _parse_line_ranges(self, line_ranges: str, line_operation: LineOperation) -> List[LineChangeDTO]:
        tokens = [t for t in line_ranges.split(" ") if t]
        result: List[LineChangeDTO] = []
        for token in tokens:
            parts = token.split(":")
            if len(parts) == 1:
                if parts[0] != "0":
                    result.append(LineChangeDTO(operation=line_operation, number=int(parts[0]), content=None))
                continue
            start = int(parts[0])
            end = int(parts[1])
            for number in range(start, end + 1):
                result.append(LineChangeDTO(operation=line_operation, number=number, content=None))
        return result
