"""The gate procedure has one definition, and CI runs that one.

Two traps make a gate examine code nobody just wrote. Copier's default ref for
a git template is its latest *tag*, so an unpinned `copier copy ... .` renders
the last release; and Copier reads an existing destination as an update,
conflicting on the first changed file and exiting non-zero having written
nothing, so a repeated render leaves the previous one for later gates to read.
Both pass while reporting on the wrong code.

This file used to hold those properties by parsing the commands back out of
`AGENTS.md`, `README.md` and the workflow, because each document restated them.
Three rounds of adversarial review found twelve holes in that parser and none
in the documents. A guard over prose fails silently by construction: a hole in
it is indistinguishable from a document with no defect, and the input domain -
arbitrary markdown - has no edge.

So the duplication was removed instead of policed (ADR-0005). `dev/gates.sh`
holds the commands once, CI calls it, and what remains here are the few checks
that the arrangement itself still holds. The parser is gone.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
GATE_SCRIPT = REPO_ROOT / "dev" / "gates.sh"
WORKFLOWS = sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml"))

# Documents that instruct a human or an agent, as opposed to running anything.
PROSE = [REPO_ROOT / "AGENTS.md", REPO_ROOT / "README.md"]

# A render into a fixed scratch destination: the shape that has to live in the
# script rather than in prose.
_RENDER_INTO_TMP = re.compile(r"copier copy [^\n`]*?/tmp/")

# A render of the PUBLISHED template, by URL. `README.md` documents one of
# these in Brownfield adoption, where an adopter renders a release into a
# scratch directory to diff against their own repository. That is an
# instruction to someone else about a different repository, not a gate on this
# one, so `dev/gates.sh` neither owns it nor could run it.
_RENDERS_THE_PUBLISHED_TEMPLATE = re.compile(r"gh:|https?://")


def _gate_renders(text: str) -> list[str]:
    """Render commands in a shell script, ignoring commented-out prose.

    Backslash continuations are joined first, because a command split across
    lines is still one command and reading half of it would report a render as
    unpinned when the pin is on the next line.

    Comments are dropped, because `dev/gates.sh` explains both traps in its own
    prose, and a comment quoting the wrong command in order to warn about it is
    not the script doing the wrong thing.
    """
    joined = re.sub(r"\\\n\s*", " ", text)
    return [
        line
        for line in joined.splitlines()
        if "copier copy" in line and not line.lstrip().startswith("#")
    ]


def test_the_gate_script_exists_and_is_executable() -> None:
    """Guards the guard: every check below is vacuous without this."""
    assert GATE_SCRIPT.is_file(), "dev/gates.sh is missing"
    assert GATE_SCRIPT.stat().st_mode & 0o111, "dev/gates.sh is not executable"


@pytest.mark.parametrize("document", PROSE, ids=lambda p: p.name)
def test_prose_does_not_restate_the_render(document: Path) -> None:
    """The commands live in the script, so a document must not carry a copy.

    A second copy is what the deleted parser existed to police. Rather than
    checking that the copies agree - which needs a parser, and a parser over
    prose has no bottom - there is one copy and this asserts there are no
    others.
    """
    restated = [
        command
        for command in _RENDER_INTO_TMP.findall(document.read_text())
        if not _RENDERS_THE_PUBLISHED_TEMPLATE.search(command)
    ]
    assert not restated, (
        f"{document.relative_to(REPO_ROOT)} restates a render command:\n"
        f"  {restated}\n"
        f"Put it in dev/gates.sh and point at it instead; a second copy is a "
        f"copy that can drift."
    )


@pytest.mark.parametrize("workflow", WORKFLOWS, ids=lambda p: p.name)
def test_ci_calls_the_script_rather_than_the_commands(workflow: Path) -> None:
    """CI running its own copy would be the same duplication by another name.

    This is the property that makes the arrangement work: because CI executes
    the script, a wrong command in it fails loudly and immediately, which is
    the enforcement the prose parser was standing in for.
    """
    text = workflow.read_text()
    assert not _RENDER_INTO_TMP.findall(text), (
        f"{workflow.relative_to(REPO_ROOT)} renders directly instead of "
        f"calling dev/gates.sh, so CI and the documented procedure can drift"
    )
    assert "dev/gates.sh" in text, (
        f"{workflow.relative_to(REPO_ROOT)} does not call dev/gates.sh"
    )


def test_the_script_renders_the_code_under_test() -> None:
    """The two traps, asserted against the one file that can now carry them.

    Checking a single known-shape script is tractable in a way that checking
    arbitrary prose was not, which is the whole reason this file is short now.
    """
    text = GATE_SCRIPT.read_text()

    assert 'rm -rf "${RENDER_DIR}"' in text, (
        "the render destination is not cleared, so a repeated render conflicts "
        "and every later gate reads the previous render"
    )

    renders = _gate_renders(text)
    assert renders, "dev/gates.sh no longer renders anything"
    for render in renders:
        pins_ref = "--vcs-ref" in render
        renders_a_copy = "SOURCE_DIR" in render
        assert pins_ref or renders_a_copy, (
            "dev/gates.sh renders this repository without pinning --vcs-ref "
            "and without going through the plain-copy directory, so it renders "
            f"the latest tag rather than the code under test:\n  {render}"
        )


def test_a_skipped_gate_is_reported_rather_than_counted_as_passing() -> None:
    """A tool that is absent must not read as a gate that passed.

    `bats` is the live case: it is absent from many machines and is not a pip
    package, so this is the difference between an honest local report and a
    green one.
    """
    text = GATE_SCRIPT.read_text()
    assert "SKIPPED" in text, "dev/gates.sh does not track gates that did not run"
    assert "--strict" in text, (
        "dev/gates.sh has no --strict mode, so CI cannot make a missing tool "
        "fatal and the suite could silently stop running"
    )
