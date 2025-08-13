"""Module for reading Git log files in the IGLog format."""

import os
from collections import deque
from typing import List, Tuple, TextIO, BinaryIO, Union, Deque

from  data_structures.inspector_git.models import GitLogDTO, CommitDTO, ChangeDTO, HunkDTO, LineChangeDTO
from  data_structures.inspector_git.enums import ChangeType, LineOperation
from data_structures.inspector_git.constants import IGLogConstants



class IGLogReader:
    """Class for reading Git log files in the IGLog format."""

    def read(self, file_path: str) -> GitLogDTO:
        """
        Read a Git log file from the given file path.

        Args:
            file_path: The path to the Git log file.

        Returns:
            A GitLogDTO object containing the parsed Git log.
        """
        with open(file_path, "r", encoding="utf-8") as file:
            return self.read_from_stream(os.path.splitext(os.path.basename(file_path))[0], file)

    def read_from_stream(self, name: str, stream: Union[TextIO, BinaryIO]) -> GitLogDTO:
        """
        Read a Git log from the given stream.

        Args:
            name: The name of the Git log.
            stream: The stream to read from.

        Returns:
            A GitLogDTO object containing the parsed Git log.
        """
        current_commit_lines: Deque[str] = deque()
        commits: List[CommitDTO] = []

        # If stream is binary, convert it to text
        if hasattr(stream, "read") and not hasattr(stream, "readline"):
            stream = TextIO(stream)

        ig_log_version = None
        if stream.readable():
            line = stream.readline()
            if line:
                ig_log_version = line.strip()

        for line in stream:
            line = line.strip()
            if not line:
                continue

            if line.startswith(IGLogConstants.COMMIT_ID_PREFIX):
                if current_commit_lines:
                    commits.append(self._read_commit(current_commit_lines))
                current_commit_lines = deque()

            current_commit_lines.append(line)

        if current_commit_lines:
            commits.append(self._read_commit(current_commit_lines))

        return GitLogDTO(ig_log_version=ig_log_version, name=name, commits=commits)

    def _read_commit(self, lines: Deque[str]) -> CommitDTO:
        """
        Read a commit from the given lines.

        Args:
            lines: The lines containing the commit information.

        Returns:
            A CommitDTO object containing the parsed commit.
        """
        commit_id = lines.popleft()[len(IGLogConstants.COMMIT_ID_PREFIX):]
        parent_ids = lines.popleft().split(" ")
        author_date = lines.popleft()
        author_email = lines.popleft()
        author_name = lines.popleft()
        committer_date = author_date
        committer_email = author_email
        committer_name = author_name
        message = ""

        if lines and lines[0].startswith(IGLogConstants.MESSAGE_PREFIX):
            message = self._extract_message(lines)
        else:
            committer_date = lines.popleft()
            committer_email = lines.popleft()
            committer_name = lines.popleft()
            message = self._extract_message(lines)

        current_change_lines: Deque[str] = deque()
        changes: List[ChangeDTO] = []

        for line in list(lines):  # Convert to list to avoid modifying while iterating
            if line.startswith(IGLogConstants.CHANGE_PREFIX):
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
        """
        Extract the commit message from the given lines.

        Args:
            lines: The lines containing the commit message.

        Returns:
            The extracted commit message.
        """
        message_lines = []
        while lines and lines[0].startswith(IGLogConstants.MESSAGE_PREFIX):
            message_lines.append(lines.popleft()[len(IGLogConstants.MESSAGE_PREFIX):])
        return "\n".join(message_lines).strip()

    def _read_change(self, lines: Deque[str]) -> ChangeDTO:
        """
        Read a change from the given lines.

        Args:
            lines: The lines containing the change information.

        Returns:
            A ChangeDTO object containing the parsed change.
        """
        change_line = lines.popleft()[1:]  # Remove the leading '#'
        change_type, binary = self._get_change_type(change_line)
        parent_commit_id = lines.popleft()
        old_file_name, new_file_name = self._get_file_name(lines, change_type)

        hunks: List[HunkDTO] = []
        if not binary:
            for line in list(lines):  # Convert to list to avoid modifying while iterating
                if line.startswith(IGLogConstants.HUNK_PREFIX_LINE + "="):
                    hunks.append(self._read_hunk(line[2:]))  # Remove the leading '@='

        return ChangeDTO(
            old_file_name=old_file_name.strip(),
            new_file_name=new_file_name.strip(),
            type=change_type,
            parent_commit_id=parent_commit_id,
            binary=binary,
            hunks=hunks,
        )

    def _get_change_type(self, line: str) -> Tuple[ChangeType, bool]:
        """
        Get the change type and binary flag from the given line.

        Args:
            line: The line containing the change type information.

        Returns:
            A tuple containing the change type and binary flag.
        """
        binary = len(line) > 1
        if line[0] == "A":
            return ChangeType.Add, binary
        elif line[0] == "D":
            return ChangeType.Delete, binary
        elif line[0] == "R":
            return ChangeType.Rename, binary
        else:
            return ChangeType.Modify, binary

    def _get_file_name(self, lines: Deque[str], change_type: ChangeType) -> Tuple[str, str]:
        """
        Get the old and new file names from the given lines based on the change type.

        Args:
            lines: The lines containing the file name information.
            change_type: The type of change.

        Returns:
            A tuple containing the old and new file names.
        """
        file_name = lines.popleft()
        if change_type == ChangeType.Add:
            return IGLogConstants.DEV_NULL, file_name
        elif change_type == ChangeType.Delete:
            return file_name, IGLogConstants.DEV_NULL
        elif change_type == ChangeType.Rename:
            return file_name, lines.popleft()
        elif change_type == ChangeType.Modify:
            return file_name, file_name
        else:
            raise ValueError(f"Unknown change type: {change_type}")

    def _read_hunk(self, hunk_line: str) -> HunkDTO:
        """
        Read a hunk from the given line.

        Args:
            hunk_line: The line containing the hunk information.

        Returns:
            A HunkDTO object containing the parsed hunk.
        """
        split = hunk_line.split("|")
        added_lines_ranges = split[0]
        deleted_lines_ranges = split[1]

        return HunkDTO(
            added_line_changes=self._parse_line_ranges(added_lines_ranges, LineOperation.Add),
            deleted_line_changes=self._parse_line_ranges(deleted_lines_ranges, LineOperation.Delete),
        )

    def _parse_line_ranges(self, line_ranges: str, line_operation: LineOperation) -> List[LineChangeDTO]:
        """
        Parse the line ranges into a list of LineChangeDTO objects.

        Args:
            line_ranges: The line ranges to parse.
            line_operation: The operation (Add or Delete) to apply to the lines.

        Returns:
            A list of LineChangeDTO objects.
        """
        ranges = line_ranges.split(" ")
        result: List[LineChangeDTO] = []

        for range_str in ranges:
            split = range_str.split(":")
            if len(split) == 1:
                if split[0] != "0":
                    result.append(LineChangeDTO(
                        operation=line_operation,
                        number=int(split[0]),
                        content=None,
                    ))
            else:
                start = int(split[0])
                end = int(split[1])
                for number in range(start, end + 1):
                    result.append(LineChangeDTO(
                        operation=line_operation,
                        number=number,
                        content=None,
                    ))

        return result
