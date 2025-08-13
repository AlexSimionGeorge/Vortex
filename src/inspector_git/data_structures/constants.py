from __future__ import annotations


class IGLogConstants:
    CommitIdPrefix = "ig#"
    MessagePrefix = "$"
    GitLogMessageEnd = "#{Glme}"  # not used by the reference C# reader but kept for completeness
    ChangePrefix = "#"
    HunkPrefixLine = "@"
    GitLogDiffLineStart = "diff --git"
    DevNull = "/dev/null"
