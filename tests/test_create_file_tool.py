from pathlib import Path

from orion.tools.create_file import CreateFileTool


def test_create_file_in_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tool = CreateFileTool()
    result = tool.execute(filename="demo/hello.txt", content="ok")
    assert "Created file" in result
    assert (Path("workspace") / "demo" / "hello.txt").exists()
