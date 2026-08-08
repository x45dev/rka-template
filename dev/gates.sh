#!/usr/bin/env bash
#
# The gate procedure for this repository, held in one place.
#
# Every gate used to be written out again in AGENTS.md, README.md and the CI
# workflow, and a test parsed those documents back out of prose to check the
# copies had not drifted. Three rounds of review found twelve holes in that
# parser, none of them in the documents themselves - a guard over prose fails
# silently, because a hole in it reads exactly like a document with no defect.
# So the commands live here once and CI calls this script rather than
# restating them. Drift is now impossible rather than policed. (ADR-0005)
#
# Usage:
#   bash dev/gates.sh                  # every gate, against the working tree
#   bash dev/gates.sh pytest render    # only the named gates
#   bash dev/gates.sh --ref HEAD       # render a committed ref instead
#   bash dev/gates.sh --strict         # a gate that cannot run is a failure
#
# Gate names: pytest render validate-render validate-self bats em-dash

set -o errexit
set -o nounset
set -o pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly REPO_ROOT

# shellcheck source=dev/helpers.sh
source "${REPO_ROOT}/dev/helpers.sh"

readonly RENDER_DIR="${GATES_RENDER_DIR:-/tmp/rka-render}"
readonly SOURCE_DIR="${GATES_SOURCE_DIR:-/tmp/rka-src}"
readonly ALL_GATES=(
    pytest render validate-render validate-self bats em-dash
)

VCS_REF=""
STRICT=0
declare -a FAILED=()
declare -a SKIPPED=()

# Render the code in front of you, not the last release and not last run.
#
# Two traps are closed here, and both cost a session to find. Copier's default
# ref for a git template is its latest TAG, so a bare `copier copy ... .`
# renders the last release; the working-tree form therefore copies the sources
# into a plain directory, which is the only shape that sees uncommitted edits.
# And Copier reads an existing destination as an update, conflicting on the
# first changed file and exiting non-zero having written nothing, so the
# destination is cleared first or every later gate reads the previous render.
gate_render() {
    require_command copier "rendering the template" || return 1
    rm -rf "${RENDER_DIR}"
    if [[ -n "${VCS_REF}" ]]; then
        info "rendering ${VCS_REF} into ${RENDER_DIR}"
        copier copy --defaults --trust --vcs-ref "${VCS_REF}" \
            "${REPO_ROOT}" "${RENDER_DIR}" > /dev/null
    else
        info "rendering the working tree into ${RENDER_DIR}"
        rm -rf "${SOURCE_DIR}"
        mkdir -p "${SOURCE_DIR}"
        cp -a "${REPO_ROOT}/copier.yml" "${REPO_ROOT}/template" \
            "${SOURCE_DIR}/"
        copier copy --defaults --trust \
            "${SOURCE_DIR}" "${RENDER_DIR}" > /dev/null
    fi
}

gate_pytest() {
    require_command python3 "the generation suite" || return 1
    info "generation invariants"
    (cd "${REPO_ROOT}" && python3 -m pytest tests/ -q)
}

# The render's own seed knowledge, checked by the render's own validator.
gate_validate_render() {
    _require_render || return 1
    info "shipped validator, over the render"
    (cd "${RENDER_DIR}" && bash scripts/validate-frontmatter.sh knowledge)
}

# This repository's knowledge, checked by the SHIPPED validator rather than a
# copy of it, so a change to the shipped schema has to migrate these documents
# in the same change.
gate_validate_self() {
    _require_render || return 1
    info "self-governance"
    (cd "${REPO_ROOT}" &&
        bash "${RENDER_DIR}/scripts/validate-frontmatter.sh" knowledge)
}

gate_bats() {
    _require_render || return 1
    if ! command -v bats > /dev/null 2>&1; then
        warn "bats is not installed; the shipped suite did NOT run"
        warn "install it with apt install bats, npm install -g bats, or a"
        warn "bats-core clone - it is not a pip package"
        SKIPPED+=("bats")
        return 0
    fi
    info "shipped BATS suite"
    bats "${RENDER_DIR}/tests/validate-frontmatter.bats"
}

# U+2014. Written as an escape so this file can be grepped by the gate it
# implements without matching itself.
gate_em_dash() {
    info "em dash"
    # Match the UTF-8 bytes, not a PCRE code point, and never read an error as a
    # clean run. Both halves of that were live defects.
    #
    # `grep -rPn '\x{2014}'` is only valid when grep is in UTF-8 mode. Under a
    # non-UTF-8 locale - LANG and LC_ALL unset, which is the default in a bare
    # container and in several CI images - PCRE rejects the escape as out of
    # range, grep exits 2, and the `if grep ...; then` that used to wrap it read
    # that failure as "no match found". The gate then passed on a file
    # containing an em dash, which is the one outcome a gate must never produce.
    # Reproduced by running this gate over a file holding U+2014 with LANG
    # unset: no output, exit 0, gate green.
    #
    # -F over the literal bytes has no locale dependency at all, so the fix does
    # not rest on a particular locale being installed. The pattern is built with
    # printf rather than written literally to keep this file's own source ASCII.
    local em_dash output status
    em_dash=$(printf '\xe2\x80\x94')
    output=$(grep -rnF --include='*.md' -e "${em_dash}" "${REPO_ROOT}") && status=0 || status=$?
    case "${status}" in
        0)
            printf '%s\n' "${output}"
            error "em dash found; use a plain dash instead"
            return 1
            ;;
        1)
            return 0
            ;;
        *)
            error "the em-dash grep exited ${status}; this gate did not run"
            return 1
            ;;
    esac
}

_require_render() {
    if [[ ! -d "${RENDER_DIR}" ]]; then
        error "${RENDER_DIR} does not exist; run the render gate first"
        return 1
    fi
}

run_gate() {
    local name="$1"
    local function_name="gate_${name//-/_}"
    if ! declare -F "${function_name}" > /dev/null; then
        error "unknown gate: ${name}"
        return 1
    fi
    if ! "${function_name}"; then
        FAILED+=("${name}")
    fi
}

main() {
    local -a requested=()
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --ref)
                VCS_REF="${2:-}"
                if [[ -z "${VCS_REF}" ]]; then
                    error "--ref needs a value"
                    return 2
                fi
                shift 2
                ;;
            --strict)
                STRICT=1
                shift
                ;;
            -h | --help)
                sed -n '3,20p' "${BASH_SOURCE[0]}"
                return 0
                ;;
            -*)
                error "unknown option: $1"
                return 2
                ;;
            *)
                requested+=("$1")
                shift
                ;;
        esac
    done

    if [[ ${#requested[@]} -eq 0 ]]; then
        requested=("${ALL_GATES[@]}")
    fi

    local gate
    for gate in "${requested[@]}"; do
        run_gate "${gate}"
    done

    if [[ ${#SKIPPED[@]} -gt 0 ]]; then
        warn "gates that did NOT run: ${SKIPPED[*]}"
        warn "a gate that could not run is not a gate that passed"
        if [[ ${STRICT} -eq 1 ]]; then
            error "--strict: treating a skipped gate as a failure"
            return 1
        fi
    fi

    if [[ ${#FAILED[@]} -gt 0 ]]; then
        error "failed: ${FAILED[*]}"
        return 1
    fi

    info "all gates that ran, passed"
}

main "$@"
