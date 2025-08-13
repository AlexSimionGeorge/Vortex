"""Constants used in the IGLogReader."""

class IGLogConstants:
    """Constants used in the IGLogReader for parsing the log file."""
    
    # Prefix for commit IDs
    COMMIT_ID_PREFIX = "ig#"
    
    # Prefix for commit messages
    MESSAGE_PREFIX = "$"
    
    # End marker for Git log messages
    GIT_LOG_MESSAGE_END = "#{Glme}"
    
    # Prefix for changes
    CHANGE_PREFIX = "#"
    
    # Prefix for hunk lines
    HUNK_PREFIX_LINE = "@"
    
    # Start marker for Git diff lines
    GIT_LOG_DIFF_LINE_START = "diff --git"
    
    # Represents a non-existent file (used for add/delete operations)
    DEV_NULL = "/dev/null"