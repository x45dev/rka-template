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
# markup: a backtick, a table cell pipe, a comment, end of line.
_COPIER_COPY = re.compile(r"copier copy [^`|\n#]*")

# Where a shell command ends and the next one begins. `&&` is the house style
# for these rows, so without this the tokens of a *following* command are parsed
# as copier's own argv and the positional extraction below reads whichever bare
# word happens to land at the right index.
#
# The surrounding whitespace is optional because a `;` conventionally attaches
# to the token before it. Splitting too eagerly can only cause a loud false
# failure, never the silent false pass this whole module exists to prevent.
_COMMAND_SEPARATOR = re.compile(r"\s*(?:&&|\|\||;)\s*")

# Shared temporary roots. A render destination underneath one of these is
# disposable and must be cleared; the root itself is never a legitimate
# destination, whatever the machine calls it.
_TEMP_ROOTS = ("/tmp", "/var/tmp", "/private/tmp", "/private/var/tmp")


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


def _temp_root_of(destination: str) -> str | None:
    """The shared temporary root `destination` sits in or is, else None."""
    normalised = destination.rstrip("/") or "/"
    for root in _TEMP_ROOTS:
        if normalised == root or normalised.startswith(root + "/"):
            return root
    return None


def _clean_offsets(unit: str, destination: str) -> list[int]:
    """Where in `unit` the render destination is removed, if anywhere."""
    pattern = rf"rm -rf [^\n]*{re.escape(destination)}(\s|$)"
    return [m.start() for m in re.finditer(pattern, unit)]


def _unit_containing(text: str, offset: int) -> tuple[str, int]:
    """The chunk a reader copies to run the command at `offset`, and where in it.

    A fenced code block is copied whole, so a clean anywhere earlier in it
    counts. Every other carrier - a table cell, a workflow's `run:` - is copied
    one line at a time, so the clean has to be on the line itself.

    Fences are matched with their indentation, because a fenced block nested in
    a list item is still copied whole. Missing that would score the block by its
    single line and reject a document that is not actually defective.
    """
    fences = [m.start() for m in re.finditer(r"^[ \t]*```", text, re.MULTILINE)]
    for start, end in zip(fences[::2], fences[1::2]):
        if start < offset < end:
            return text[start:end], offset - start
    line_start = text.rfind("\n", 0, offset) + 1
    line_end = text.find("\n", offset)
    unit = text[line_start:] if line_end == -1 else text[line_start:line_end]
    return unit, offset - line_start


def _commands() -> list[tuple[Path, str, str, int]]:
    found = []
    for path in SOURCES:
        if not path.is_file():
            continue
        text = path.read_text()
        for match in _COPIER_COPY.finditer(text):
            # Truncate at the next shell command so the argv parsed below is
            # copier's own and nothing else.
            raw = _COMMAND_SEPARATOR.split(match.group(0))[0]
            command = raw.strip().rstrip("\\").strip()
            unit, position = _unit_containing(text, match.start())
            found.append((path, command, unit, position))
    return found


def test_sources_exist() -> None:
    """Guards the guard: a renamed doc must not turn this into a no-op pass."""
    missing = [str(p.relative_to(REPO_ROOT)) for p in SOURCES if not p.is_file()]
    assert not missing, f"gate documentation moved or was deleted: {missing}"
    assert _commands(), "no `copier copy` invocations found; the regex or the docs moved"


@pytest.mark.parametrize(
    ("source", "command", "unit", "position"),
    _commands(),
    ids=[f"{p.name}:{i}" for i, (p, _, _, _) in enumerate(_commands())],
)
def test_renders_never_target_a_shared_temporary_root(
    source: Path, command: str, unit: str, position: int
) -> None:
    """No documented render may write to `/tmp` itself, or any spelling of it.

    The clean-first rule below cannot apply here: the remedy for a reused
    destination is to delete it, and deleting a shared temporary root is the one
    outcome worse than the defect. Such a destination is rejected outright
    rather than exempted, which is how it slipped through - `/tmp` is not a
    prefix of `/tmp/`.
    """
    destination = _destination_arg(command)
    if destination is None:
        return
    assert _temp_root_of(destination) != destination.rstrip("/"), (
        f"{source.relative_to(REPO_ROOT)} renders into the shared temporary root "
        f"{destination}, which cannot be cleared safely; render into a named "
        f"subdirectory of it:\n  {command}"
    )


@pytest.mark.parametrize(
    ("source", "command", "unit", "position"),
    _commands(),
    ids=[f"{p.name}:{i}" for i, (p, _, _, _) in enumerate(_commands())],
)
def test_renders_into_a_fixed_destination_clean_it_first(
    source: Path, command: str, unit: str, position: int
) -> None:
    """A render into a fixed path must remove that path first, in the same breath.

    Copier treats an existing destination as an update, conflicts on the first
    file that differs, and in a non-interactive run exits 1 having applied
    nothing. The render is then last run's, and the validator and BATS rows that
    follow are separate commands with no way to know it.

    Destinations under a temporary root only: the adopter-facing `copier copy
    gh:... .` renders into a repository, where removing the destination is the
    opposite of what anyone wants. Every shared root is recognised, because the
    exemption is what keeps a real destination unguarded and `/var/tmp` is one
    spelling away from `/tmp`.

    The clean must precede the render. A `rm -rf` afterwards leaves exactly the
    window this guards - the render reads the previous one and only then is the
    evidence destroyed.
    """
    destination = _destination_arg(command)
    if destination is None or _temp_root_of(destination) is None:
        return
    cleans = _clean_offsets(unit, destination)
    assert cleans, (
        f"{source.relative_to(REPO_ROOT)} renders into {destination} without clearing it, "
        f"so a second run conflicts and the gates below examine the previous "
        f"render:\n  {command}"
    )
    assert min(cleans) < position, (
        f"{source.relative_to(REPO_ROOT)} clears {destination} only AFTER rendering into "
        f"it, which is the same defect: the render still reads the previous one:\n  {command}"
    )


@pytest.mark.parametrize(
    ("source", "command", "unit", "position"),
    _commands(),
    ids=[f"{p.name}:{i}" for i, (p, _, _, _) in enumerate(_commands())],
)
def test_renders_of_this_repository_pin_the_ref(
    source: Path, command: str, unit: str, position: int
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


# The guard is the only mechanism holding a procedure that ships as prose, so a
# hole in it is silent by construction: it keeps passing. These exercise the
# extraction directly, on inputs the documents do not currently contain. Each
# one failed before the fix it describes.


@pytest.mark.parametrize(
    ("destination", "expected"),
    [
        ("/tmp/rka-render", "/tmp"),
        ("/tmp/", "/tmp"),
        ("/tmp", "/tmp"),
        ("/var/tmp/rka-render", "/var/tmp"),
        ("/private/tmp/rka-render", "/private/tmp"),  # macOS resolves /tmp here
        ("/tmpfile", None),  # a prefix match is not a path match
        ("/home/dev/render", None),
        (".", None),
    ],
)
def test_temp_root_detection_is_by_path_not_by_prefix(
    destination: str, expected: str | None
) -> None:
    assert _temp_root_of(destination) == expected


@pytest.mark.parametrize(
    ("text", "expected_src", "expected_dst"),
    [
        # Both positionals present: truncating changes nothing, because the
        # extraction is by index and the indices happen to line up.
        (
            "copier copy --defaults /tmp/src /tmp/dst && bash /tmp/dst/scripts/x.sh",
            "/tmp/src",
            "/tmp/dst",
        ),
        # One positional: without truncation the chained command donates the
        # bare words that the index lands on, and `&&` is read as a destination.
        ("copier copy . && echo done", None, None),
        ("copier copy /tmp/src; ls /tmp/dst", None, None),
    ],
)
def test_a_chained_command_is_not_parsed_as_copier_argv(
    text: str, expected_src: str | None, expected_dst: str | None
) -> None:
    """`&&` is the house style for these rows, so the argv must stop at it.

    The two-positional case is the one the documents use today and it survives
    either way; the one-positional cases are where index luck runs out.
    """
    raw = _COMMAND_SEPARATOR.split(_COPIER_COPY.search(text).group(0))[0]
    assert _destination_arg(raw) == expected_dst
    assert _template_arg(raw) == expected_src


def test_an_indented_fence_is_still_read_as_one_block() -> None:
    """A fenced block inside a list item is copied whole, like any other."""
    text = "1. Render:\n\n   ```bash\n   rm -rf /tmp/dst\n   copier copy . /tmp/dst\n   ```\n"
    unit, position = _unit_containing(text, text.index("copier copy"))
    assert "rm -rf /tmp/dst" in unit, "the enclosing block was not recognised"
    assert unit.index("rm -rf") < position


def test_a_clean_after_the_render_does_not_satisfy_the_guard() -> None:
    """The window this guards is open until the render happens, not after it.

    A trailing `rm -rf` looks like hygiene and is not: the render has already
    read the previous one by the time it runs.
    """
    unit = "copier copy --defaults . /tmp/dst && rm -rf /tmp/dst"
    position = unit.index("copier copy")
    cleans = _clean_offsets(unit, "/tmp/dst")
    assert cleans, "the fixture no longer models a clean at all"
    assert min(cleans) > position, "the guard would accept a clean that runs too late"
