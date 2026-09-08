#!/usr/bin/env bash
#
# trustedge-tricks.sh - a winetricks-style zenity front end for TrustEdge.
#
# Everything is a zenity dialog: editing which actions exist, which are
# sensitive vs non-sensitive, denied targets, critical files, the approval
# popup timeout, and resolving pending approvals. It talks to the c3
# framework's admin API (added in main.py: GET/POST /policy, GET /pending,
# POST /approve) rather than editing files inside the container directly.
#
# Run this on the HOST (not inside a container) so zenity has a real X11
# display. Requires: zenity, curl, jq.
#
set -euo pipefail

FRAMEWORK_URL="${FRAMEWORK_URL:-http://localhost:8000}"

check_deps() {
    for bin in zenity curl jq; do
        if ! command -v "$bin" >/dev/null 2>&1; then
            zenity --error --title="TrustEdge Tricks" \
                --text="Missing dependency: $bin\n\nInstall it and re-run this script." 2>/dev/null || \
                echo "Missing dependency: $bin" >&2
            exit 1
        fi
    done
}

fetch_policy() {
    curl -sf "$FRAMEWORK_URL/policy"
}

push_policy() {
    # $1 = full policy JSON
    curl -sf -X POST "$FRAMEWORK_URL/policy" -H "Content-Type: application/json" -d "$1"
}

notify_ok() {
    zenity --info --title="TrustEdge Tricks" --text="$1" --width=300 2>/dev/null || true
}

notify_err() {
    zenity --error --title="TrustEdge Tricks" --text="$1" --width=300 2>/dev/null || true
}

# ---- category: edit a JSON array field with a checklist against the fixed
#      universe of known action types ----
edit_action_classification() {
    local policy current field
    policy=$(fetch_policy) || { notify_err "Could not reach $FRAMEWORK_URL"; return; }

    local all_actions=(read_file write_file run_command network_call delete_file none)
    local checklist_args=()
    for action in "${all_actions[@]}"; do
        local in_sensitive in_nonsensitive mark
        in_sensitive=$(echo "$policy" | jq -r --arg a "$action" '.sensitive_actions | index($a) != null')
        if [ "$in_sensitive" = "true" ]; then
            checklist_args+=(TRUE "$action" "sensitive")
        else
            checklist_args+=(FALSE "$action" "non-sensitive")
        fi
    done

    local result
    result=$(zenity --list --checklist \
        --title="TrustEdge Tricks - Action Sensitivity" \
        --text="Check the actions that should require attestation + operator approval.\nUnchecked actions are auto-allowed with no review." \
        --column="Sensitive?" --column="Action" --column="Currently" \
        "${checklist_args[@]}" \
        --width=520 --height=380 --separator="," 2>/dev/null) || return

    IFS=',' read -ra chosen <<< "$result"
    local sensitive_json non_sensitive_json
    sensitive_json=$(printf '%s\n' "${chosen[@]}" | jq -R . | jq -s .)
    non_sensitive_json=$(printf '%s\n' "${all_actions[@]}" | jq -R . | jq -s --argjson sens "$sensitive_json" \
        '. - $sens')

    policy=$(echo "$policy" | jq --argjson sens "$sensitive_json" --argjson nonsens "$non_sensitive_json" \
        '.sensitive_actions = $sens | .non_sensitive_actions = $nonsens')
    if push_policy "$policy" >/dev/null; then
        notify_ok "Action sensitivity updated."
    else
        notify_err "Failed to push policy update."
    fi
}

edit_allowed_actions() {
    local policy current_csv new_csv
    policy=$(fetch_policy) || { notify_err "Could not reach $FRAMEWORK_URL"; return; }
    current_csv=$(echo "$policy" | jq -r '.allowed_actions | join(",")')

    new_csv=$(zenity --entry --title="TrustEdge Tricks - Allowed Actions" \
        --text="Comma-separated list of action names the agent is permitted to propose at all.\nAnything not listed here is blocked outright, before sensitivity even matters." \
        --entry-text="$current_csv" --width=500 2>/dev/null) || return

    policy=$(echo "$policy" | jq --arg csv "$new_csv" \
        '.allowed_actions = ($csv | split(",") | map(gsub("^\\s+|\\s+$";"")) | map(select(length > 0)))')
    if push_policy "$policy" >/dev/null; then
        notify_ok "Allowed actions updated."
    else
        notify_err "Failed to push policy update."
    fi
}

edit_denied_targets() {
    local policy current_csv new_csv
    policy=$(fetch_policy) || { notify_err "Could not reach $FRAMEWORK_URL"; return; }
    current_csv=$(echo "$policy" | jq -r '.denied_targets | join(",")')

    new_csv=$(zenity --entry --title="TrustEdge Tricks - Denied Targets" \
        --text="Comma-separated substrings. Any action whose target contains one of these is blocked, regardless of classification." \
        --entry-text="$current_csv" --width=500 2>/dev/null) || return

    policy=$(echo "$policy" | jq --arg csv "$new_csv" \
        '.denied_targets = ($csv | split(",") | map(gsub("^\\s+|\\s+$";"")) | map(select(length > 0)))')
    if push_policy "$policy" >/dev/null; then
        notify_ok "Denied targets updated."
    else
        notify_err "Failed to push policy update."
    fi
}

edit_critical_files() {
    local policy current_csv new_csv
    policy=$(fetch_policy) || { notify_err "Could not reach $FRAMEWORK_URL"; return; }
    current_csv=$(echo "$policy" | jq -r '.critical_files | join(",")')

    new_csv=$(zenity --entry --title="TrustEdge Tricks - Critical Files" \
        --text="Comma-separated paths (relative to c3/) whose hashes are baselined and checked before every sensitive action.\nWarning: after saving, these files are re-baselined immediately against their CURRENT on-disk contents." \
        --entry-text="$current_csv" --width=520 2>/dev/null) || return

    policy=$(echo "$policy" | jq --arg csv "$new_csv" \
        '.critical_files = ($csv | split(",") | map(gsub("^\\s+|\\s+$";"")) | map(select(length > 0)))')
    if push_policy "$policy" >/dev/null; then
        notify_ok "Critical files list updated (re-baselined)."
    else
        notify_err "Failed to push policy update."
    fi
}

edit_popup_timeout() {
    local policy current new
    policy=$(fetch_policy) || { notify_err "Could not reach $FRAMEWORK_URL"; return; }
    current=$(echo "$policy" | jq -r '.popup_timeout_seconds // 30')

    new=$(zenity --entry --title="TrustEdge Tricks - Approval Timeout" \
        --text="Seconds to wait for a human ALLOW/BLOCK before the automated decision (ALLOW, since attestation already passed) stands." \
        --entry-text="$current" --width=400 2>/dev/null) || return

    if ! [[ "$new" =~ ^[0-9]+$ ]]; then
        notify_err "Timeout must be a whole number of seconds."
        return
    fi

    policy=$(echo "$policy" | jq --argjson t "$new" '.popup_timeout_seconds = $t')
    if push_policy "$policy" >/dev/null; then
        notify_ok "Approval timeout set to ${new}s."
    else
        notify_err "Failed to push policy update."
    fi
}

view_current_policy() {
    local policy
    policy=$(fetch_policy) || { notify_err "Could not reach $FRAMEWORK_URL"; return; }
    echo "$policy" | jq . | zenity --text-info --title="TrustEdge Tricks - Current Policy" \
        --width=600 --height=500 2>/dev/null || true
}

resolve_pending() {
    local pending count choice id
    pending=$(curl -sf "$FRAMEWORK_URL/pending") || { notify_err "Could not reach $FRAMEWORK_URL"; return; }
    count=$(echo "$pending" | jq 'length')

    if [ "$count" -eq 0 ]; then
        notify_ok "No pending approvals right now."
        return
    fi

    local list_args=()
    while IFS=$'\t' read -r pid paction ptarget preason; do
        list_args+=("$pid" "$paction" "$ptarget" "$preason")
    done < <(echo "$pending" | jq -r '.[] | [.id, .action, .target, .reasoning] | @tsv')

    choice=$(zenity --list --title="TrustEdge Tricks - Pending Approvals" \
        --text="Select an action, then choose ALLOW or BLOCK on the next dialog." \
        --column="ID" --column="Action" --column="Target" --column="Reasoning" \
        --hide-column=1 --print-column=1 \
        "${list_args[@]}" --width=700 --height=300 2>/dev/null) || return

    id="$choice"
    if zenity --question --title="TrustEdge Tricks" \
        --text="Approve this action?\n\nID: $id" \
        --ok-label="ALLOW" --cancel-label="BLOCK" 2>/dev/null; then
        decision="ALLOW"
    else
        decision="BLOCK"
    fi

    if curl -sf -X POST "$FRAMEWORK_URL/approve" -H "Content-Type: application/json" \
        -d "{\"id\": \"$id\", \"decision\": \"$decision\"}" >/dev/null; then
        notify_ok "Recorded: $decision"
    else
        notify_err "Failed to submit decision."
    fi
}

main_menu() {
    while true; do
        choice=$(zenity --list --title="TrustEdge Tricks" \
            --text="Everything here edits the live policy through the framework's admin API - no container shell needed." \
            --column="Category" --column="Description" \
            "Pending Approvals"      "Review and ALLOW/BLOCK actions waiting on a human" \
            "Action Sensitivity"     "Toggle which actions require attestation + approval" \
            "Allowed Actions"        "Which action types the agent may propose at all" \
            "Denied Targets"         "Substrings that are always blocked" \
            "Critical Files"         "Files whose integrity is checked before sensitive actions" \
            "Approval Timeout"       "How long to wait for a human response" \
            "View Raw Policy"        "See the full current policy.json" \
            --width=620 --height=420 2>/dev/null) || break

        case "$choice" in
            "Pending Approvals") resolve_pending ;;
            "Action Sensitivity") edit_action_classification ;;
            "Allowed Actions") edit_allowed_actions ;;
            "Denied Targets") edit_denied_targets ;;
            "Critical Files") edit_critical_files ;;
            "Approval Timeout") edit_popup_timeout ;;
            "View Raw Policy") view_current_policy ;;
            *) break ;;
        esac
    done
}

check_deps
main_menu
