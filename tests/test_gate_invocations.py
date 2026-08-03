"""The gates must render the code under test, not the last release.

Copier's default ref for a git template is its latest *tag*. This repository is
tagged, so `copier copy --defaults --trust . /tmp/rka-render` renders the last
release - and every gate chained off that render then reports on code nobody
just wrote, while passing. CI escapes it only because `actions/checkout` does
not fetch tags by default, which makes the current behaviour accidental rather
than chosen.

A reused destination is the same failure by another route. Copier stops at the
first conflict in a non-interactive run, so a second render into a directory
that already holds one exits 1 having written nothing - and the gates chained
off it are separate commands that will happily examine the render from last
time. Both tests below therefore guard the same contract: the thing the gates
examine is the code in front of you.

So: wherever this repository is named as the template the ref is pinned, and
wherever a render has a fixed destination that destination is cleaned first.
This test reads the documents and the workflow that carry those commands,
because the delivery mechanism for a gate procedure is prose, and prose has no
other gate.
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


def _destination_arg(command: str) -> str | None:
    """The DST of `copier copy [options] SRC DST`, or None if it cannot be read."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None
    positional = []
    skip_next = False
    for token in tokens[2:]:
        if skip_next:
            skip_next = False
            continue
        if token.startswith("-"):
            if token in {"--vcs-ref", "--data", "-a", "--answers-file", "-r"}:
                skip_next = True
            continue
        positional.append(token)
    return positional[1] if len(positional) >= 2 else None


def _unit_containing(text: str, offset: int) -> str:
    """The self-contained chunk a reader would copy to run the command at `offset`.

    A fenced code block is copied whole, so a clean anywhere in it counts. Every
    other carrier - a table cell, a workflow's `run:` - is copied one line at a
    time, so the clean has to be on the line itself.
    """
    fences = [m.start() for m in re.finditer(r"^```", text, re.MULTILINE)]
    for start, end in zip(fences[::2], fences[1::2]):
        if start < offset < end:
            return text[start:end]
    line_start = text.rfind("\n", 0, offset) + 1
    line_end = text.find("\n", offset)
    return text[line_start:] if line_end == -1 else text[line_start:line_end]


def _commands() -> list[tuple[Path, str, str]]:
    found = []
    for path in SOURCES:
        if not path.is_file():
            continue
        text = path.read_text()
        for match in _COPIER_COPY.finditer(text):
            command = match.group(0).strip().rstrip("\\").strip()
            found.append((path, command, _unit_containing(text, match.start())))
    return found


def test_sources_exist() -> None:
    """Guards the guard: a renamed doc must not turn this into a no-op pass."""
    missing = [str(p.relative_to(REPO_ROOT)) for p in SOURCES if not p.is_file()]
    assert not missing, f"gate documentation moved or was deleted: {missing}"
    assert _commands(), "no `copier copy` invocations found; the regex or the docs moved"


@pytest.mark.parametrize(
    ("source", "command", "unit"),
    _commands(),
    ids=[f"{p.name}:{i}" for i, (p, _, _) in enumerate(_commands())],
)
def test_renders_into_a_fixed_destination_clean_it_first(
    source: Path, command: str, unit: str
) -> None:
    """A render into a fixed path must remove that path in the same breath.

    Copier treats an existing destination as an update, conflicts on the first
    file that differs, and in a non-interactive run exits 1 having applied
    nothing. The render is then last run's, and the validator and BATS rows that
    follow are separate commands with no way to know it.

    Destinations under a temporary directory only: the adopter-facing `copier
    copy gh:... .` renders into a repository, where removing the destination is
    the opposite of what anyone wants.
    """
    destination = _destination_arg(command)
    if destination is None or not destination.startswith("/tmp/"):
        return
    assert re.search(rf"rm -rf [^\n]*{re.escape(destination)}(\s|$)", unit), (
        f"{source.relative_to(REPO_ROOT)} renders into {destination} without clearing it "
        f"first, so a second run conflicts and the gates below examine the previous "
        f"render:\n  {command}"
    )


@pytest.mark.parametrize(
    ("source", "command", "unit"),
    _commands(),
    ids=[f"{p.name}:{i}" for i, (p, _, _) in enumerate(_commands())],
)
def test_renders_of_this_repository_pin_the_ref(
    source: Path, command: str, unit: str
) -> None:
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
