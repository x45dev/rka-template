#!/usr/bin/env bash
set -euo pipefail

# Validate RKA frontmatter for all knowledge/**/*.md files.
# Rules (RFC-003 sections 3, 4, 5 and 8):
#   1. All six required fields present and non-empty: id, title, status, version,
#      date, type (type is OKF's one required field).
#   2. status is one of: draft, active, canonical, archived
#   3. id is non-empty and unique across all governed documents
#   4. id / filename convention:
#      - ADRs (knowledge/adr/): id is ADR-NNNN (4 digits, no slug); filename is
#        ADR-NNNN.md or ADR-NNNN-<kebab-slug>.md; the leading ADR-NNNN token of
#        the filename stem must equal the id.
#      - Every other governed document: id must equal the filename stem.
#   5. adr_status: every document under knowledge/adr/ must carry adr_status,
#      one of proposed, accepted, superseded.
#   6. constitution presence: the tree must contain exactly one document with
#      id "constitution", the one mandatory artifact.
#   7. bundle-index integrity: knowledge/index.md is optional, but WHEN PRESENT
#      it must list every governed document and every entry must resolve.
#   8. extraction record: any document at status "archived" must carry an
#      "Extraction record" heading (RKA RFC-002 section 3). Inside a spec bundle
#      the record lives once, in spec.md, and covers the bundle - which is only
#      safe because rule 9c makes spec.md mandatory.
#   9. spec-bundle lifecycle (RKA ADR-0013). A spec bundle is
#      knowledge/specs/<NNN>-<slug>/<role>.md with <role> one of spec, plan, tasks:
#      9a. every document in one bundle carries the same status;
#      9b. a bundle whose tasks.md holds at least one checkbox and no unchecked
#          checkbox must be at status "archived" - the rule that catches a spec
#          shipped in full and never retired;
#      9c. a bundle directory must contain spec.md (spec.md required, plan.md and
#          tasks.md optional), and every .md in the bundle sits directly in the
#          bundle directory - a file nested deeper would otherwise match neither
#          the role check nor the bundle status set, and escape 9a entirely.
#      Bundle ids are <role>-<NNN>-<slug>, not the filename stem, because three
#      documents share a directory (this is the rule 4 exception).
# The reserved OKF bundle-structure files (index.md, log.md) are not governed
# documents: they are excluded from rules 1-6 and validated only by rule 7.
# Reports every error before exiting non-zero, so one run surfaces all problems
# rather than failing on the first.
# NOTE (template maintainers): this file is rendered by Copier with default
# Jinja delimiters, so it must not contain a "{" immediately followed by "#"
# (Jinja comment open); counts are tracked with explicit counter variables
# instead of parameter-expansion length operators. That construct has two failure
# modes, both proven by seeding it: with no later "#}" the render aborts with
# "Missing end of comment tag", and WITH a later "#}" it renders silently with
# everything between the two deleted. The second is why tests/test_generation.py
# greps this file's SOURCE - by the time output exists, the evidence is gone.

# Normalise away trailing slashes before any path derivation: the bundle-relative
# path below is produced by stripping this prefix, and "knowledge/" would defeat
# the strip, silently disabling rules 9a/9b (a fail-open on exactly the case they
# exist to catch) while spuriously breaking rule 7.
KNOWLEDGE_DIR="${1:-knowledge}"
while [[ "$KNOWLEDGE_DIR" == */ && "$KNOWLEDGE_DIR" != "/" ]]; do
    KNOWLEDGE_DIR="${KNOWLEDGE_DIR%/}"
done
REQUIRED_FIELDS=("id" "title" "status" "version" "date" "type")
LEGAL_STATUSES=("draft" "active" "canonical" "archived")
LEGAL_ADR_STATUSES=("proposed" "accepted" "superseded")
SPEC_ROLES=("spec" "plan" "tasks")

errors=0
declare -A id_to_file
file_count=0
governed_rel=()
governed_count=0
has_constitution=false
declare -A bundle_statuses
declare -A bundle_tasks_file
declare -A bundle_has_spec
declare -A bundle_seen

is_reserved() {
    local base="$1"
    [[ "$base" == "index.md" || "$base" == "log.md" ]]
}

# Slice the leading YAML frontmatter block (between the first `---` and the next
# `---`). Portable: depends only on awk, so it is independent of the yq flavor.
extract_frontmatter() {
    awk 'NR == 1 && $0 != "---" { exit }   # no frontmatter delimiter -> emit nothing
         NR == 1 { next }                  # skip the opening ---
         $0 == "---" { exit }              # stop at the closing ---
         { print }' "$1"
}

# Transcode YAML on stdin to JSON. Frontmatter is sliced with awk above, so
# extraction is flavor-independent; yq is used only to turn that YAML block into
# JSON, which both common implementations can do:
#   * mikefarah/yq (Go):                     needs `-o=json`.
#   * kislyuk/yq   (Python jq wrapper):      emits JSON by default.
# Probe the capability rather than the `--version` string, so the validator
# works whichever yq is on PATH. If NEITHER form transcodes, no usable yq is
# installed (usually the toolchain was not provisioned) - fail loudly with the
# fix instead of misreporting every document as missing all six fields.
if printf 'probe: 1\n' | yq -o=json '.' > /dev/null 2>&1; then
    yaml_to_json() { yq -o=json '.'; }
elif printf 'probe: 1\n' | yq '.' > /dev/null 2>&1; then
    yaml_to_json() { yq '.'; }
else
    printf 'ERROR: validate-frontmatter.sh needs a working yq (mikefarah Go yq, or the python yq).\n' >&2
    printf '       found: %s\n' "$(yq --version 2>&1 || echo 'no yq on PATH')" >&2
    printf '       fix:   install one - "pip install yq", or the Go yq from\n' >&2
    printf '              https://github.com/mikefarah/yq. This project carries no\n' >&2
    printf '              toolchain manager, so yq and jq come from your environment.\n' >&2
    exit 2
fi

while IFS= read -r -d '' file; do
    # Reserved OKF bundle-structure files are not governed documents.
    if is_reserved "$(basename "$file")"; then
        continue
    fi
    file_count=$((file_count + 1))
    rel="$file"
    rel="${rel/#"$KNOWLEDGE_DIR"\//}"
    governed_rel+=("$rel")
    governed_count=$((governed_count + 1))

    # Rule 9: identify a spec-bundle document. Anything under specs/ that is not
    # exactly specs/<bundle>/<role>.md is rejected here rather than falling
    # through to the generic stem convention, which would let it escape 9a.
    spec_bundle=""
    spec_role=""
    if [[ "$rel" =~ ^specs/([^/]+)/(.+)\.md$ ]]; then
        spec_bundle="${BASH_REMATCH[1]}"
        spec_role="${BASH_REMATCH[2]}"
        bundle_seen["$spec_bundle"]=1
        if [[ "$spec_role" == */* ]]; then
            printf 'ERROR: %s: a spec-bundle document must sit directly in the bundle directory (%s/specs/%s/), not in a subdirectory\n' \
                "$file" "$KNOWLEDGE_DIR" "$spec_bundle" >&2
            errors=$((errors + 1))
            spec_bundle=""
            spec_role=""
        else
            valid_role=false
            for legal in "${SPEC_ROLES[@]}"; do
                [[ "$spec_role" == "$legal" ]] && valid_role=true && break
            done
            if [[ "$valid_role" == false ]]; then
                printf 'ERROR: %s: "%s.md" is not a known spec-bundle role (must be one of: spec, plan, tasks)\n' \
                    "$file" "$spec_role" >&2
                errors=$((errors + 1))
            fi
            [[ "$spec_role" == "spec" ]] && bundle_has_spec["$spec_bundle"]=1
            [[ "$spec_role" == "tasks" ]] && bundle_tasks_file["$spec_bundle"]="$file"
        fi
    fi

    block=$(extract_frontmatter "$file")
    if [[ -z "$block" ]]; then
        # No frontmatter at all: fall through so every required field is reported
        # missing (a governed document must carry frontmatter).
        fm="{}"
    else
        fm=$(printf '%s\n' "$block" | yaml_to_json 2> /dev/null) || fm=""
        if [[ -z "$fm" || "$fm" == "null" ]]; then
            # Frontmatter is present but did not parse: a toolchain or YAML-syntax
            # problem, not a missing field. Report it as such instead of masking it.
            printf 'ERROR: %s: frontmatter block present but could not be parsed as YAML (check syntax, or that yq is installed)\n' "$file" >&2
            errors=$((errors + 1))
            continue
        fi
    fi

    for field in "${REQUIRED_FIELDS[@]}"; do
        val=$(printf '%s' "$fm" | jq -r --arg f "$field" '.[$f] // ""')
        if [[ -z "$val" || "$val" == "null" ]]; then
            printf 'ERROR: %s: missing required field "%s"\n' "$file" "$field" >&2
            errors=$((errors + 1))
        fi
    done

    status=$(printf '%s' "$fm" | jq -r '.status // ""')
    if [[ -n "$status" && "$status" != "null" ]]; then
        valid_status=false
        for legal in "${LEGAL_STATUSES[@]}"; do
            [[ "$status" == "$legal" ]] && valid_status=true && break
        done
        if [[ "$valid_status" == false ]]; then
            printf 'ERROR: %s: invalid status "%s" (must be one of: draft, active, canonical, archived)\n' \
                "$file" "$status" >&2
            errors=$((errors + 1))
        fi
        # Rule 9a input: accumulate this bundle's statuses for the post-loop check.
        if [[ -n "$spec_bundle" ]]; then
            bundle_statuses["$spec_bundle"]="${bundle_statuses[$spec_bundle]:-} $status"
        fi
    fi

    # Rule 8: an archived document must carry its extraction record. Inside a spec
    # bundle the record lives once, in spec.md, so plan.md and tasks.md are exempt
    # - safe only because rule 9c guarantees a spec.md exists.
    if [[ "$status" == "archived" ]]; then
        if [[ -n "$spec_bundle" && "$spec_role" != "spec" ]]; then
            :
        elif ! grep -qiE '^#{1,6}[[:space:]]+extraction record[[:space:]]*$' "$file"; then
            printf 'ERROR: %s: archived document has no "Extraction record" section (RKA RFC-002 section 3)\n' \
                "$file" >&2
            errors=$((errors + 1))
        fi
    fi

    # Rule 5: ADRs must carry a legal adr_status.
    if [[ "$(basename "$(dirname "$file")")" == "adr" ]]; then
        adr_status=$(printf '%s' "$fm" | jq -r '.adr_status // ""')
        if [[ -z "$adr_status" || "$adr_status" == "null" ]]; then
            printf 'ERROR: %s: missing required field "adr_status" for an ADR\n' "$file" >&2
            errors=$((errors + 1))
        else
            valid_adr_status=false
            for legal in "${LEGAL_ADR_STATUSES[@]}"; do
                [[ "$adr_status" == "$legal" ]] && valid_adr_status=true && break
            done
            if [[ "$valid_adr_status" == false ]]; then
                printf 'ERROR: %s: invalid adr_status "%s" (must be one of: proposed, accepted, superseded)\n' \
                    "$file" "$adr_status" >&2
                errors=$((errors + 1))
            fi
        fi
    fi

    id=$(printf '%s' "$fm" | jq -r '.id // ""')
    if [[ -n "$id" && "$id" != "null" ]]; then
        [[ "$id" == "constitution" ]] && has_constitution=true
        if [[ -v id_to_file["$id"] ]]; then
            printf 'ERROR: %s: duplicate id "%s" (first seen in %s)\n' \
                "$file" "$id" "${id_to_file[$id]}" >&2
            errors=$((errors + 1))
        else
            id_to_file["$id"]="$file"
        fi

        # Rule 4: type-keyed id / filename convention.
        stem=$(basename "$file" .md)
        parent=$(basename "$(dirname "$file")")
        if [[ "$parent" == "adr" ]]; then
            if [[ ! "$id" =~ ^ADR-[0-9]{4}$ ]]; then
                printf 'ERROR: %s: ADR id "%s" must be ADR-NNNN (4 digits, no slug)\n' \
                    "$file" "$id" >&2
                errors=$((errors + 1))
            fi
            if [[ ! "$stem" =~ ^ADR-[0-9]{4}(-[a-z0-9]+)*$ ]]; then
                printf 'ERROR: %s: ADR filename must be ADR-NNNN.md or ADR-NNNN-<kebab-slug>.md\n' \
                    "$file" >&2
                errors=$((errors + 1))
            elif [[ "$id" =~ ^ADR-[0-9]{4}$ && "$stem" =~ ^(ADR-[0-9]{4}) ]]; then
                lead="${BASH_REMATCH[1]}"
                if [[ "$lead" != "$id" ]]; then
                    printf 'ERROR: %s: ADR filename prefix "%s" does not match id "%s"\n' \
                        "$file" "$lead" "$id" >&2
                    errors=$((errors + 1))
                fi
            fi
        elif [[ -n "$spec_bundle" ]]; then
            # Rule 4 exception: a bundle's documents share a directory, so the
            # filename carries the role and the id carries role plus bundle.
            expected_id="$spec_role-$spec_bundle"
            if [[ "$id" != "$expected_id" ]]; then
                printf 'ERROR: %s: spec-bundle id must be "%s" (got "%s")\n' \
                    "$file" "$expected_id" "$id" >&2
                errors=$((errors + 1))
            fi
        else
            if [[ "$stem" != "$id" ]]; then
                printf 'ERROR: %s: id "%s" does not match filename stem "%s"\n' \
                    "$file" "$id" "$stem" >&2
                errors=$((errors + 1))
            fi
        fi
    fi
done < <(find "$KNOWLEDGE_DIR" -name "*.md" -print0 | sort -z)

# Rule 9c: every spec bundle must hold a spec.md. Without this, an archived
# bundle of plan.md + tasks.md alone would carry no extraction record anywhere and
# rule 8's intra-bundle exemption would pass it - the fail-open case.
for bundle in "${!bundle_seen[@]}"; do
    if [[ -z "${bundle_has_spec[$bundle]:-}" ]]; then
        printf 'ERROR: %s/specs/%s: spec bundle has no spec.md (spec.md is required; plan.md and tasks.md are optional)\n' \
            "$KNOWLEDGE_DIR" "$bundle" >&2
        errors=$((errors + 1))
    fi
done

# Rule 9a: a spec bundle has one lifecycle, so its documents share a status.
# Distinct values are counted with `wc -l`, never an array-length expansion: the
# "{" + "#" that would introduce is the Jinja comment open (see the note above).
for bundle in "${!bundle_statuses[@]}"; do
    read -ra bundle_status_list <<< "${bundle_statuses[$bundle]}"
    distinct=$(printf '%s\n' "${bundle_status_list[@]}" | sort -u)
    distinct_count=$(printf '%s\n' "$distinct" | wc -l)
    if ((distinct_count > 1)); then
        printf 'ERROR: %s/specs/%s: spec bundle has mixed status values (%s); a bundle shares one lifecycle\n' \
            "$KNOWLEDGE_DIR" "$bundle" "$(printf '%s' "$distinct" | tr '\n' ' ' | sed 's/ $//')" >&2
        errors=$((errors + 1))
    fi
done

# Rule 9b: a bundle whose tasks are all complete must be archived. A bundle with
# no tasks.md, or a tasks.md carrying no checkboxes, is out of scope: tasks.md is
# optional (RKA ADR-0013 clause 5).
for bundle in "${!bundle_tasks_file[@]}"; do
    tasks_file="${bundle_tasks_file[$bundle]}"
    total=$(grep -cE '^[[:space:]]*[-*][[:space:]]+\[[ xX]\]' "$tasks_file" || true)
    ((total == 0)) && continue
    open_boxes=$(grep -cE '^[[:space:]]*[-*][[:space:]]+\[[[:space:]]\]' "$tasks_file" || true)
    ((open_boxes > 0)) && continue
    read -ra bundle_status_list <<< "${bundle_statuses[$bundle]:-}"
    for s in "${bundle_status_list[@]}"; do
        if [[ "$s" != "archived" ]]; then
            printf 'ERROR: %s/specs/%s: all tasks complete but status is "%s"; a shipped spec is archived after extraction (RKA RFC-002 section 3)\n' \
                "$KNOWLEDGE_DIR" "$bundle" "$s" >&2
            errors=$((errors + 1))
            break
        fi
    done
done

# Rule 6: the mandatory constitution must be present.
if [[ "$has_constitution" == false ]]; then
    printf 'ERROR: %s: no constitution found (a document with id "constitution" is the one mandatory artifact)\n' \
        "$KNOWLEDGE_DIR" >&2
    errors=$((errors + 1))
fi

# Rule 7: bundle-index integrity. The index is optional; validated only when
# present.
index_file="$KNOWLEDGE_DIR/index.md"
if [[ -f "$index_file" ]]; then
    declare -A index_targets
    while IFS= read -r target; do
        [[ -z "$target" ]] && continue
        [[ "$target" == *"://"* ]] && continue
        target="${target%%\#*}"
        [[ -z "$target" ]] && continue
        index_targets["$target"]=1
    done < <(grep -oE '\]\([^)]+\)' "$index_file" | sed -e 's/^](//' -e 's/)$//')

    # Every governed document must be listed in the index.
    if ((governed_count > 0)); then
        for rel in "${governed_rel[@]}"; do
            if [[ -z "${index_targets[$rel]:-}" ]]; then
                printf 'ERROR: %s: governed document "%s" is not listed in the bundle index\n' \
                    "$index_file" "$rel" >&2
                errors=$((errors + 1))
            fi
        done
    fi

    # Every index entry must resolve to an existing file under the bundle root.
    for target in "${!index_targets[@]}"; do
        if [[ ! -f "$KNOWLEDGE_DIR/$target" ]]; then
            printf 'ERROR: %s: index entry "%s" does not resolve to an existing file\n' \
                "$index_file" "$target" >&2
            errors=$((errors + 1))
        fi
    done
fi

if ((errors > 0)); then
    printf 'Frontmatter validation failed: %d error(s) across %d file(s).\n' "$errors" "$file_count" >&2
    exit 1
fi

printf 'Frontmatter OK: %d file(s) validated.\n' "$file_count"
