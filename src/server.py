import io
import sys
import traceback
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from src.inspector_git.reader.iglog.readers.ig_log_reader import IGLogReader
from src.inspector_git.linker.transformers import GitProjectTransformer
from src.jira_miner.reader_dto.loader import JiraJsonLoader
from src.jira_miner.linker.transformers import JiraProjectTransformer
from src.github_miner.reader_dto.loader import GithubJsonLoader
from src.github_miner.linker.transformers import GitHubProjectTransformer
from src.common.project_linkers import ProjectLinker


class CodeRequest(BaseModel):
    code: str


graph_data = {}


def build_projects():
    """Builds the projects once and links them together."""
    base_path = Path(__file__).parent.parent / "test-input"

    # InspectorGit
    iglog_file = base_path / "inspector-git" / "zeppelin.iglog"
    with open(iglog_file, "r", encoding="utf-8") as f:
        git_log_dto = IGLogReader().read(f)

    git_project = GitProjectTransformer(
        git_log_dto,
        name=iglog_file.stem,
        compute_annotated_lines=False,  # no blame
    ).transform()

    # Jira
    jira_loader = JiraJsonLoader(str(base_path / "jira-miner" / "ZEPPELIN-detailed-issues.json"))
    jira_data = jira_loader.load()
    jira_project = JiraProjectTransformer(jira_data, name="Jira Project").transform()

    # GitHub
    github_loader = GithubJsonLoader(str(base_path / "github-miner" / "githubProject.json"))
    github_data = github_loader.load()
    github_project = GitHubProjectTransformer(github_data, name="GitHub Project").transform()

    # Link
    ProjectLinker.link_projects(github_project, jira_project, jira_data)
    ProjectLinker.link_projects(jira_project, git_project)
    ProjectLinker.link_projects(github_project, git_project)

    return {
        "git": git_project,
        "jira": jira_project,
        "github": github_project,
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    global graph_data
    graph_data = build_projects()
    print("✅ Graph built and stored in memory.")
    try:
        yield
    finally:
        graph_data.clear()
        print("🛑 Graph cleared, shutdown complete.")


app = FastAPI(lifespan=lifespan)


@app.post("/execute")
async def execute_code(request: CodeRequest):
    code = request.code
    stdout = io.StringIO()
    try:
        sys_stdout = sys.stdout
        sys.stdout = stdout

        # Execute code with limited scope
        exec_globals = {"graph_data": graph_data}
        exec(code, exec_globals)

        output = stdout.getvalue()
        return JSONResponse({"output": output})
    except Exception:
        tb = traceback.format_exc()
        return JSONResponse({"error": tb}, status_code=400)
    finally:
        sys.stdout = sys_stdout
