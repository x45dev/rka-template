#!/usr/bin/env bash
#
# Shared logging for this repository's developer scripts.
#
# This is developer tooling for the template repository itself. It is not
# under template/, so it ships to nobody: ADR-0001 point 4 keeps a tooling
# preset out of what adopters receive, and says nothing about how this
# repository runs its own gates.

# Colour only when stdout is a terminal, so CI logs stay plain.
if [[ -t 1 ]]; then
    readonly _C_INFO=$'\033[0;36m'
    readonly _C_WARN=$'\033[0;33m'
    readonly _C_ERROR=$'\033[0;31m'
    readonly _C_OFF=$'\033[0m'
else
    readonly _C_INFO=""
    readonly _C_WARN=""
    readonly _C_ERROR=""
    readonly _C_OFF=""
fi

info() {
    printf '%s==>%s %s\n' "${_C_INFO}" "${_C_OFF}" "$*"
}

warn() {
    printf '%sWARN%s %s\n' "${_C_WARN}" "${_C_OFF}" "$*" >&2
}

error() {
    printf '%sERROR%s %s\n' "${_C_ERROR}" "${_C_OFF}" "$*" >&2
}

# Fail with a message rather than letting `set -o nounset` produce a bare
# line number for a missing dependency.
require_command() {
    local command_name="$1"
    local reason="$2"
    if ! command -v "${command_name}" > /dev/null 2>&1; then
        error "${command_name} is not installed; it is needed for ${reason}"
        return 1
    fi
}
