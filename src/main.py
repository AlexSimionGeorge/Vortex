from inspector_git.ig_log_reader import IGLogReader


def read_iglog_file():
    """
    Read the zeppelin.iglog file using IGLogReader.
    """
    reader = IGLogReader()
    file_path = "/home/alex/Work/BachelorThesis/Vortex/results/zeppelin-voyager-results/inspector-git/results/zeppelin.iglog"
    git_log = reader.read(file_path)
    print(f"Successfully read {git_log.name} with {len(git_log.commits)} commits")
    return git_log


if __name__ == '__main__':
    git_log = read_iglog_file()
    # You can process the git_log data further here

    print(git_log.commits[0].parent_ids)
    print(git_log.commits[0])


