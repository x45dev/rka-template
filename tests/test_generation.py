"""Generation invariants for the governance-only template.

Fast, pure-Python checks so they run locally on every edit and in CI in seconds.
The deeper "does the render's own validator pass over the render's own knowledge/"
proof lives in CI, because that needs bash, yq and jq.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

# Jinja statement/comment tags must never survive rendering. `{{ ... }}` is NOT
# flagged wholesale: we look for leftover statement tags and for obviously
# unrendered answer variables instead.
_JINJA_STATEMENT = re.compile(r"{%|{#")
_UNRENDERED_VAR = re.compile(r"{{\s*(project_\w+|author_name|description|copyright_year|license)\b")

_TEXT_SUFFIXES = {
    ".py", ".toml", ".yml", ".yaml", ".json", ".md", ".sh", ".ini", ".cfg",
    ".txt", ".bats", "",
}

# Not `.copier-answers.yml`: this template claims a distinct answers file so that
# adopting it into an already-Copier-generated repository does not collide with
# that repository's own (ADR-0004).
ANSWERS_FILE = ".copier-answers.rka-template.yml"

# The complete governance render, MIT arm. Anything outside this set is a leak
# from a layer this template deliberately does not carry.
EXPECTED_FILES = {
    ANSWERS_FILE,
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "LICENSE",
    "README.md",
    "knowledge/PRD.md",
    "knowledge/activeContext.md",
    "knowledge/adr/ADR-0001-adopt-rka.md",
    "knowledge/constitution.md",
    "knowledge/context.md",
    "knowledge/progress.md",
    "scripts/validate-frontmatter.sh",
    "tests/validate-frontmatter.bats",
}


def _iter_text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {".git", "node_modules", ".venv"} for part in path.parts):
            continue
        if path.suffix in _TEXT_SUFFIXES:
            yield path


def _rel_files(root: Path) -> set[str]:
    return {
        str(p.relative_to(root))
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.parts
    }


def _answers(project: Path) -> dict:
    return yaml.safe_load((project / ANSWERS_FILE).read_text())


def _run_shipped_validator(project: Path) -> subprocess.CompletedProcess:
    """Run the render's own validator against the render's own knowledge/."""
    for tool in ("bash", "yq", "jq"):
        if not shutil.which(tool):
            pytest.skip(f"{tool} not on PATH; cannot exercise the shipped validator")
    return subprocess.run(
        ["bash", str(project / "scripts" / "validate-frontmatter.sh"), "knowledge"],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture(scope="module")
def project(generate) -> Path:
    out, proc = generate("governance-default")
    assert proc.returncode == 0, f"generation failed:\n{proc.stderr}"
    return out


def test_generation_succeeds(project: Path) -> None:
    assert any(project.iterdir()), "generated project is empty"


def test_no_unrendered_jinja(project: Path) -> None:
    offenders = []
    for path in _iter_text_files(project):
        text = path.read_text(errors="ignore")
        if _JINJA_STATEMENT.search(text) or _UNRENDERED_VAR.search(text):
            offenders.append(str(path.relative_to(project)))
    assert not offenders, f"unrendered Jinja left in: {offenders}"


def test_shipped_scripts_have_no_jinja_comment_open() -> None:
    """`{` followed by `#` is the Jinja comment open, and every file under `template/`
    renders with default delimiters (`_templates_suffix: ""`). A shipped shell script
    containing it has that code silently *eaten* at render time.

    `test_no_unrendered_jinja` above cannot catch this: it inspects the generated
    project, and by then Jinja has already consumed the construct, so the assertion
    passes over mangled code. This test therefore reads the TEMPLATE SOURCE.

    Scripts are selected by shebang rather than by filename, so a script added at a
    new path is covered without editing this test. Only file CONTENTS are inspected.
    """
    template_root = Path(__file__).resolve().parent.parent / "template"
    offenders = []
    for path in sorted(template_root.rglob("*")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if not text.startswith("#!"):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if "{#" in line:
                rel = path.relative_to(template_root)
                offenders.append(f"{rel}:{lineno}: {line.strip()}")
    assert not offenders, "Jinja comment-open in shipped shell script(s):\n" + "\n".join(offenders)


def test_yaml_files_parse(project: Path) -> None:
    for suffix in ("*.yml", "*.yaml"):
        for path in project.rglob(suffix):
            list(yaml.safe_load_all(path.read_text()))


def test_json_files_parse(project: Path) -> None:
    for path in project.rglob("*.json"):
        json.loads(path.read_text())


def test_render_is_the_governance_layer_and_nothing_else(project: Path) -> None:
    """The whole point of this template: `copier copy` into an existing repository
    must drop in the governance layer and touch nothing else.

    Asserted as an exact file set rather than a list of `is_file()` checks, because
    the failure this guards against is an *extra* file arriving (a `.config/`, a
    CI workflow, an app skeleton), which no positive assertion would notice.
    """
    assert _rel_files(project) == EXPECTED_FILES


def test_adoption_does_not_clobber_an_existing_answers_file(
    plain_template: Path, copier_cmd: list[str], tmp_path: Path
) -> None:
    """Adopting into an already-Copier-generated repository must leave that
    repository's own answers file alone.

    Copier's default answers file is `.copier-answers.yml` for every template, so
    a shared name forces the adopter to choose between keeping the link to their
    original template and having a working `copier update` for this one - and this
    template's whole purpose is adoption into a repository that already exists,
    with a project moving off the predecessor unified template as the named case.
    Hence the distinct `_answers_file` (ADR-0004), asserted here rather than
    inferred from `EXPECTED_FILES`: that set is checked against a render into an
    EMPTY directory, where a collision cannot occur and so cannot be observed.
    """
    foreign = tmp_path / ".copier-answers.yml"
    original = (
        "# This file is managed by Copier for a DIFFERENT template.\n"
        "_commit: v9.9.9\n"
        "_src_path: https://example.invalid/other-template.git\n"
    )
    foreign.write_text(original)

    proc = subprocess.run(
        [
            *copier_cmd, "copy", "--defaults", "--quiet",
            "--data", "project_name=Test Project",
            str(plain_template), str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, f"adoption into a Copier-managed repo failed:\n{proc.stderr}"
    assert foreign.read_text() == original, "the adopter's own answers file was modified"
    assert (tmp_path / ANSWERS_FILE).is_file(), "this template's answers file was not written"


def test_agents_md_carries_no_frontmatter(project: Path) -> None:
    """The agent entry point sits at the root, OUTSIDE `knowledge/`, so it is
    deliberately not a governed document: the validator walks `knowledge/` only, and
    an RKA id must equal its filename stem, which `AGENTS.md` is not. Assert the
    absence of frontmatter so a later move under `knowledge/` fails here rather than
    in a consumer's gate.
    """
    first_line = (project / "AGENTS.md").read_text().splitlines()[0]
    assert first_line != "---", "AGENTS.md must not carry RKA frontmatter"


@pytest.mark.parametrize(
    ("license_value", "expected"),
    [("MIT", True), ("Proprietary", False)],
)
def test_license_ships_unless_proprietary(generate, license_value: str, expected: bool) -> None:
    """LICENSE is a root community file (GitHub convention), shipped unless the
    project chose a Proprietary (all-rights-reserved) license."""
    out, proc = generate(f"license-{license_value.lower()}", license=license_value)
    assert proc.returncode == 0, proc.stderr
    assert (out / "LICENSE").is_file() is expected


def test_shipped_validator_passes_over_the_shipped_knowledge(project: Path) -> None:
    """The seed `knowledge/` the template ships must satisfy the validator the
    template ships beside it. A schema change that lands in one and not the other
    fails here rather than in a consumer's first commit."""
    proc = _run_shipped_validator(project)
    assert proc.returncode == 0, f"validator rejected the shipped seed:\n{proc.stdout}\n{proc.stderr}"


# A project name that is hostile in every syntax the template interpolates it into:
# an apostrophe (terminates a single-quoted literal), a double quote (JSON, YAML,
# Python), `&` and `<` (HTML/markdown), and a backslash (escape sequences). Kept
# verbatim as regression cover for a real defect in the predecessor template, where a
# punctuation-heavy real-world name rendered an unparseable TypeScript literal.
HOSTILE_NAME = "Quote\"Apos'Amp&Lt<Back\\Slash Triple\"\"\"Quote"


@pytest.fixture(scope="module")
def hostile_project(generate) -> Path:
    out, proc = generate("hostile-name", project_name=HOSTILE_NAME)
    assert proc.returncode == 0, f"generation failed:\n{proc.stderr}"
    return out


def test_hostile_project_name_round_trips_into_prose_targets(hostile_project: Path) -> None:
    """`project_name` lands verbatim in the two prose surfaces that interpolate it.

    Markdown needs no escaping, so the correct behaviour is an exact round trip; an
    over-eager escape would show up here as a mangled name.
    """
    assert HOSTILE_NAME in (hostile_project / "README.md").read_text()
    assert HOSTILE_NAME in (hostile_project / "AGENTS.md").read_text()


def test_hostile_project_name_round_trips_through_the_answers_file(hostile_project: Path) -> None:
    """The answers file is YAML, where the embedded quotes and backslash are
    genuinely dangerous. Parse it with a real parser and check the value survives,
    so an escape that merely looks plausible still fails."""
    answers = _answers(hostile_project)
    assert answers["project_name"] == HOSTILE_NAME


def test_hostile_render_yaml_parses(hostile_project: Path) -> None:
    for suffix in ("*.yml", "*.yaml"):
        for path in hostile_project.rglob(suffix):
            list(yaml.safe_load_all(path.read_text()))


def test_hostile_render_frontmatter_is_still_valid(hostile_project: Path) -> None:
    """Frontmatter is YAML too. Run the SHIPPED validator over the hostile render's
    knowledge/ tree, so a name that broke a frontmatter block fails here."""
    proc = _run_shipped_validator(hostile_project)
    assert proc.returncode == 0, f"validator rejected the hostile render:\n{proc.stdout}\n{proc.stderr}"


def test_hostile_name_derives_a_clean_slug(hostile_project: Path) -> None:
    """`project_slug` is derived from `project_name` and is a real directory name in
    a consumer's hands, so the derivation must strip everything illegal."""
    project_slug = _answers(hostile_project)["project_slug"]
    assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", project_slug), (
        f"project_slug {project_slug!r} is not a clean kebab-case slug"
    )


def test_all_punctuation_project_name_fails_loudly(generate) -> None:
    """A `project_name` that sanitizes to an empty slug must fail generation.

    Regression cover: the derivation chain in copier.yml strips anything outside
    the allowed slug characters, so a name that is entirely punctuation/whitespace
    (e.g. "!!!") collapses to an empty project_slug. Without a validator this
    silently produces an empty directory name instead of failing loudly.
    """
    _, proc = generate("all-punctuation-name", project_name="!!!")
    assert proc.returncode != 0, "generation should fail when project_name sanitizes to an empty slug"
