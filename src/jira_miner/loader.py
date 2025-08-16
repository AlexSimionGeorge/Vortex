import json
from pathlib import Path
from typing import List, Tuple
from .models import IssueStatus, IssueType, Issue, JsonFileFormat


class LoadModels:
    @staticmethod
    def read(path: str) -> Tuple[List[IssueStatus], List[IssueType], List[Issue]]:
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        parsed = JsonFileFormat.model_validate(data)
        return parsed.issueStatuses, parsed.issueTypes, parsed.issues
