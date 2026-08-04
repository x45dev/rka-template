"""Test harness for the template itself.

These tests generate projects from the *working tree* (not a committed ref) and
assert structural invariants, so a template edit is validated here - before a user
ever generates from it.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent


def _copier_cmd() -> list[str]:
    """Resolve a copier invocation: the CLI if on PATH, else `python -m copier`."""
    if shutil.which("copier"):
        return ["copier"]
    return [sys.executable, "-m", "copier"]


@pytest.fixture(scope="session")
def copier_cmd() -> list[str]:
    """The resolved copier invocation, for tests that drive their own output dir
    rather than taking one from the `generate` factory."""
    return _copier_cmd()


@pytest.fixture(scope="session")
def plain_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A plain (non-git) copy of the template.

    copier renders a git template at a committed ref; copying `copier.yml` +
    `template/` into a plain directory makes it render the *working tree* instead,
    so the suite validates uncommitted edits with no commit-then-test round trip.
    """
    dst = tmp_path_factory.mktemp("template-src")
    shutil.copytree(TEMPLATE_ROOT / "template", dst / "template")
    shutil.copy(TEMPLATE_ROOT / "copier.yml", dst / "copier.yml")
    return dst


@pytest.fixture(scope="session")
def generate(plain_template: Path, tmp_path_factory: pytest.TempPathFactory):
    """Return a factory that generates a project and returns (path, CompletedProcess).

    Generation is expected to succeed for valid answers; callers that test the
    failure path inspect the returned CompletedProcess.returncode.
    """

    def _generate(name: str, **data: object) -> tuple[Path, subprocess.CompletedProcess]:
        out = tmp_path_factory.mktemp(name)
        args = [*_copier_cmd(), "copy", "--defaults", "--quiet"]
        data = {"project_name": "Test Project", **data}
        for key, value in data.items():
            args += ["--data", f"{key}={_fmt(value)}"]
        args += [str(plain_template), str(out)]
        proc = subprocess.run(args, capture_output=True, text=True, check=False)
        return out, proc

    return _generate


def _fmt(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)
