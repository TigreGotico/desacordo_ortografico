"""benchmark/publish_hf.py creates the dataset repo only when it does not exist.

Each ``create_repo`` call counts against the Hugging Face account's daily
repo-creation limit, also with ``exist_ok=True`` on a repo that exists.
"""
import importlib.util
import sys
import types
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "benchmark" / "publish_hf.py"
REPO = "TigreGotico/desacordo_ortografico"


class StubApi:
    def __init__(self, existing):
        self.existing = existing
        self.calls = []

    def repo_exists(self, repo_id, *, repo_type=None):
        self.calls.append(("repo_exists", repo_id, repo_type))
        return repo_id in self.existing

    def create_repo(self, repo_id, *, repo_type=None, private=None, exist_ok=False):
        self.calls.append(("create_repo", repo_id, repo_type))

    def upload_folder(self, *, repo_id, folder_path, repo_type=None, commit_message=None):
        self.calls.append(("upload_folder", repo_id, repo_type))


def _publish(monkeypatch, existing):
    api = StubApi(existing)
    monkeypatch.setitem(sys.modules, "huggingface_hub",
                        types.SimpleNamespace(HfApi=lambda: api))
    monkeypatch.setattr(sys, "argv", ["publish_hf.py", "--repo", REPO])
    spec = importlib.util.spec_from_file_location("publish_hf", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "_load", lambda name: [])
    module.main()
    return api.calls


@pytest.mark.parametrize("existing, expected", [
    ({REPO}, [("repo_exists", REPO, "dataset"), ("upload_folder", REPO, "dataset")]),
    (set(), [("repo_exists", REPO, "dataset"), ("create_repo", REPO, "dataset"),
             ("upload_folder", REPO, "dataset")]),
], ids=["repo exists", "repo missing"])
def test_create_repo_only_for_a_missing_repo(monkeypatch, existing, expected):
    assert _publish(monkeypatch, existing) == expected
