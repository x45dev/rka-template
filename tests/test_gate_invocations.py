"""The gates must render the code under test, not the last release.

Copier's default ref for a git template is its latest *tag*. This repository is
tagged, so `copier copy --defaults --trust . /tmp/rka-render` renders the last
release - and every gate chained off that render then reports on code nobody
just wrote, while passing. CI escapes it only because `actions/checkout` does
not fetch tags by default, which makes the current behaviour accidental rather
than chosen.

So: wherever this repository is named as the template, the ref is pinned. This
test reads the documents and the workflow that carry those commands, because the
delivery mechanism for a gate procedure is prose, and prose has no other gate.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Files that tell a human or an agent how to render this template.
SOURCES = [
    REPO_ROOT / "AGENTS.md",
    REPO_ROOT / "README.md",
    *sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml")),
]

# A `copier copy ...` command, stopping at whatever ends it in the surrounding
# markup: a backtick, a table cell pipe, a shell `&&`, a comment, end of line.
_COPIER_COPY = re.compile(r"copier copy [^`|\n#]*")


def _template_arg(command: str) -> str | None:
    """The SRC of `copier copy [options] SRC DST`, or None if it cannot be read."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None
    positional = []
    skip_next = False
    for token in tokens[2:]:  # drop "copier copy"
        if skip_next:
            skip_next = False
            continue
        if token.startswith("-"):
            # Options that take a separate value; everything else here is a flag.
            if token in {"--vcs-ref", "--data", "-a", "--answers-file", "-r"}:
                skip_next = True
            continue
        positional.append(token)
    return positional[0] if len(positional) >= 2 else None


def _commands() -> list[tuple[Path, str]]:
    found = []
    for path in SOURCES:
        if not path.is_file():
            continue
        for match in _COPIER_COPY.finditer(path.read_text()):
            found.append((path, match.group(0).strip().rstrip("\\").strip()))
    return found


def test_sources_exist() -> None:
    """Guards the guard: a renamed doc must not turn this into a no-op pass."""
    missing = [str(p.relative_to(REPO_ROOT)) for p in SOURCES if not p.is_file()]
    assert not missing, f"gate documentation moved or was deleted: {missing}"
    assert _commands(), "no `copier copy` invocations found; the regex or the docs moved"


@pytest.mark.parametrize(
    ("source", "command"),
    [(p, c) for p, c in _commands()],
    ids=[f"{p.name}:{i}" for i, (p, _) in enumerate(_commands())],
)
def test_renders_of_this_repository_pin_the_ref(source: Path, command: str) -> None:
    """A `copier copy` whose template is `.` must pin `--vcs-ref`.

    Invocations that name a URL (the adopter-facing usage) or a plain directory
    (the working-tree render) are untouched: neither resolves a tag in this
    repository, so neither can silently fall back to the last release.
    """
    if _template_arg(command) != ".":
        return
    assert "--vcs-ref" in command, (
        f"{source.relative_to(REPO_ROOT)} renders this repository without --vcs-ref, "
        f"so it renders the latest tag rather than the code under test:\n  {command}"
    )
