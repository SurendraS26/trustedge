#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENVFILE="$REPO/.env"
FRAMEWORK_URL="${FRAMEWORK_URL:-http://localhost:8000}"
DASHBOARD_URL="${DASHBOARD_URL:-http://localhost:8501}"

[[ -f "$ENVFILE" ]] || cp "$REPO/.env.example" "$ENVFILE"

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

check_deps() {
    for bin in zenity curl jq docker; do
        if ! command -v "$bin" >/dev/null 2>&1; then
            zenity --error --title="TrustEdge Tricks" \
                --text="Missing dependency: $bin\n\nInstall it and re-run this script." 2>/dev/null || \
                echo "Missing dependency: $bin" >&2
            exit 1
        fi
    done
}

notify_ok()  { zenity --info  --title="TrustEdge Tricks" --text="$1" --width=320 2>/dev/null || true; }
notify_err() { zenity --error --title="TrustEdge Tricks" --text="$1" --width=320 2>/dev/null || true; }

fetch_policy() { curl -sf "$FRAMEWORK_URL/policy"; }
push_policy() {  # $1 = full policy JSON
    curl -sf -X POST "$FRAMEWORK_URL/policy" -H "Content-Type: application/json" -d "$1"
}

env_get() { grep -E "^$1=" "$ENVFILE" | tail -1 | cut -d= -f2-; }
env_set() { # $1 = key, $2 = value
    if grep -qE "^$1=" "$ENVFILE"; then
        sed -i "s|^$1=.*|$1=$2|" "$ENVFILE"
    else
        echo "$1=$2" >> "$ENVFILE"
    fi
}

# ===========================================================================
# CATEGORY 1: Live Policy  (reads/writes policy.json through the running
# framework's admin API - takes effect immediately, no rebuild)
# ===========================================================================

policy_action_sensitivity() {
    local policy all_actions=(read_file write_file run_command network_call delete_file none)
    policy=$(fetch_policy) || { notify_err "Could not reach $FRAMEWORK_URL.\nIs the stack running?"; return; }

    local checklist_args=()
    for action in "${all_actions[@]}"; do
        local in_sensitive
        in_sensitive=$(echo "$policy" | jq -r --arg a "$action" '.sensitive_actions | index($a) != null')
        if [ "$in_sensitive" = "true" ]; then
            checklist_args+=(TRUE "$action" "sensitive")
        else
            checklist_args+=(FALSE "$action" "non-sensitive")
        fi
    done

    local result
    result=$(zenity --list --checklist \
        --title="Policy - Action Sensitivity" \
        --text="Check the actions that require TPM attestation + operator approval.\nUnchecked actions are auto-allowed with no review." \
        --column="Sensitive?" --column="Action" --column="Currently" \
        "${checklist_args[@]}" \
        --width=520 --height=380 --separator="," 2>/dev/null) || return

    IFS=',' read -ra chosen <<< "$result"
    local sensitive_json non_sensitive_json
    sensitive_json=$(printf '%s\n' "${chosen[@]:-}" | jq -R . | jq -s 'map(select(length > 0))')
    non_sensitive_json=$(printf '%s\n' "${all_actions[@]}" | jq -R . | jq -s --argjson sens "$sensitive_json" '. - $sens')

    policy=$(echo "$policy" | jq --argjson sens "$sensitive_json" --argjson nonsens "$non_sensitive_json" \
        '.sensitive_actions = $sens | .non_sensitive_actions = $nonsens')
    push_policy "$policy" >/dev/null && notify_ok "Action sensitivity updated." || notify_err "Failed to push policy update."
}

policy_allowed_actions() {
    local policy current_csv new_csv
    policy=$(fetch_policy) || { notify_err "Could not reach $FRAMEWORK_URL.\nIs the stack running?"; return; }
    current_csv=$(echo "$policy" | jq -r '.allowed_actions | join(",")')

    new_csv=$(zenity --entry --title="Policy - Allowed Actions" \
        --text="Comma-separated action names the agent may propose at all.\nAnything not listed here is blocked outright, before sensitivity even matters." \
        --entry-text="$current_csv" --width=520 2>/dev/null) || return

    policy=$(echo "$policy" | jq --arg csv "$new_csv" \
        '.allowed_actions = ($csv | split(",") | map(gsub("^\\s+|\\s+$";"")) | map(select(length > 0)))')
    push_policy "$policy" >/dev/null && notify_ok "Allowed actions updated." || notify_err "Failed to push policy update."
}

policy_denied_targets() {
    local policy current_csv new_csv
    policy=$(fetch_policy) || { notify_err "Could not reach $FRAMEWORK_URL.\nIs the stack running?"; return; }
    current_csv=$(echo "$policy" | jq -r '.denied_targets | join(",")')

    new_csv=$(zenity --entry --title="Policy - Denied Targets" \
        --text="Comma-separated substrings. Any action whose target contains one of these is blocked, regardless of classification." \
        --entry-text="$current_csv" --width=520 2>/dev/null) || return

    policy=$(echo "$policy" | jq --arg csv "$new_csv" \
        '.denied_targets = ($csv | split(",") | map(gsub("^\\s+|\\s+$";"")) | map(select(length > 0)))')
    push_policy "$policy" >/dev/null && notify_ok "Denied targets updated." || notify_err "Failed to push policy update."
}

policy_critical_files() {
    local policy current_csv new_csv
    policy=$(fetch_policy) || { notify_err "Could not reach $FRAMEWORK_URL.\nIs the stack running?"; return; }
    current_csv=$(echo "$policy" | jq -r '.critical_files | join(",")')

    new_csv=$(zenity --entry --title="Policy - Critical Files" \
        --text="Comma-separated paths (relative to c3/) whose hashes are baselined and checked before every sensitive action.\nWarning: after saving, these files are re-baselined immediately against their CURRENT on-disk contents." \
        --entry-text="$current_csv" --width=540 2>/dev/null) || return

    policy=$(echo "$policy" | jq --arg csv "$new_csv" \
        '.critical_files = ($csv | split(",") | map(gsub("^\\s+|\\s+$";"")) | map(select(length > 0)))')
    push_policy "$policy" >/dev/null && notify_ok "Critical files list updated (re-baselined)." || notify_err "Failed to push policy update."
}

policy_approval_timeout() {
    local policy current new
    policy=$(fetch_policy) || { notify_err "Could not reach $FRAMEWORK_URL.\nIs the stack running?"; return; }
    current=$(echo "$policy" | jq -r '.popup_timeout_seconds // 30')

    new=$(zenity --entry --title="Policy - Approval Timeout" \
        --text="Seconds to wait for a human ALLOW/BLOCK before the automated decision\n(ALLOW, since attestation already passed) stands." \
        --entry-text="$current" --width=400 2>/dev/null) || return

    if ! [[ "$new" =~ ^[0-9]+$ ]]; then
        notify_err "Timeout must be a whole number of seconds."
        return
    fi

    policy=$(echo "$policy" | jq --argjson t "$new" '.popup_timeout_seconds = $t')
    push_policy "$policy" >/dev/null && notify_ok "Approval timeout set to ${new}s." || notify_err "Failed to push policy update."
}

policy_view_raw() {
    local policy
    policy=$(fetch_policy) || { notify_err "Could not reach $FRAMEWORK_URL.\nIs the stack running?"; return; }
    echo "$policy" | jq . | zenity --text-info --title="Policy - Raw policy.json" --width=600 --height=500 2>/dev/null || true
}

menu_policy() {
    while true; do
        choice=$(zenity --list --title="TrustEdge Tricks - Live Policy" \
            --text="Edited through the framework's admin API - takes effect immediately, no rebuild." \
            --column="Category" --column="Description" \
            "Allowed Actions"    "Which action types the agent may propose at all" \
            "Action Sensitivity" "Toggle which actions require attestation + approval" \
            "Denied Targets"     "Substrings that are always blocked" \
            "Critical Files"     "Files whose integrity is checked before sensitive actions" \
            "Approval Timeout"   "How long to wait for a human response" \
            "View Raw Policy"    "See the full current policy.json" \
            --width=620 --height=380 2>/dev/null) || break
        case "$choice" in
            "Allowed Actions") policy_allowed_actions ;;
            "Action Sensitivity") policy_action_sensitivity ;;
            "Denied Targets") policy_denied_targets ;;
            "Critical Files") policy_critical_files ;;
            "Approval Timeout") policy_approval_timeout ;;
            "View Raw Policy") policy_view_raw ;;
            *) break ;;
        esac
    done
}

# ===========================================================================
# CATEGORY 2: Pending Approvals
# ===========================================================================

menu_pending() {
    local pending count list_args=() choice id decision
    pending=$(curl -sf "$FRAMEWORK_URL/pending") || { notify_err "Could not reach $FRAMEWORK_URL.\nIs the stack running?"; return; }
    count=$(echo "$pending" | jq 'length')

    if [ "$count" -eq 0 ]; then
        notify_ok "No pending approvals right now."
        return
    fi

    while IFS=$'\t' read -r pid paction ptarget preason; do
        list_args+=("$pid" "$paction" "$ptarget" "$preason")
    done < <(echo "$pending" | jq -r '.[] | [.id, .action, .target, .reasoning] | @tsv')

    choice=$(zenity --list --title="TrustEdge Tricks - Pending Approvals" \
        --text="Select an action, then choose ALLOW or BLOCK on the next dialog." \
        --column="ID" --column="Action" --column="Target" --column="Reasoning" \
        --hide-column=1 --print-column=1 \
        "${list_args[@]}" --width=720 --height=320 2>/dev/null) || return

    id="$choice"
    if zenity --question --title="TrustEdge Tricks" --text="Approve this action?\n\nID: $id" \
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

# ===========================================================================
# CATEGORY 3: Runtime Settings  (.env - written to disk, needs "Apply
# changes" from the Stack Control menu to take effect)
# ===========================================================================

runtime_agent() {
    local result
    result=$(zenity --forms --title="Runtime - Agent (c1)" \
        --text="Ollama model and where the agent finds the framework." \
        --add-entry="Ollama model" \
        --add-entry="Ollama host" \
        --separator="|" \
        2>/dev/null) || return
    IFS="|" read -r model host <<< "$result"
    [[ -n "$model" ]] && env_set OLLAMA_MODEL "$model"
    [[ -n "$host" ]] && env_set OLLAMA_HOST "$host"
    notify_ok "Saved to .env. Use \"Apply Changes\" in Stack Control to rebuild."
}

runtime_rag() {
    local current_model current_k result
    current_model=$(env_get EMBED_MODEL)
    current_k=$(env_get RAG_TOP_K)
    result=$(zenity --forms --title="Runtime - RAG (c1)" \
        --text="Local document grounding. Drop .txt/.md/.pdf files in c1/data - they're\nindexed automatically on every container boot." \
        --add-entry="Embedding model" \
        --add-entry="Chunks retrieved per task (top-k)" \
        --separator="|" \
        2>/dev/null) || return
    IFS="|" read -r model k <<< "$result"
    [[ -n "$model" ]] && env_set EMBED_MODEL "$model"
    if [[ -n "$k" ]]; then
        if [[ "$k" =~ ^[0-9]+$ ]]; then
            env_set RAG_TOP_K "$k"
        else
            notify_err "Top-k must be a whole number - not saved."
        fi
    fi
    notify_ok "Saved to .env. Use \"Apply Changes\" in Stack Control to rebuild."
}

runtime_tpm() {
    local result
    result=$(zenity --forms --title="Runtime - TPM (c2)" \
        --text="Ports swtpm listens on inside the c2 container." \
        --add-entry="TPM server port" \
        --add-entry="TPM control port" \
        --separator="|" \
        2>/dev/null) || return
    IFS="|" read -r sport cport <<< "$result"
    [[ -n "$sport" ]] && env_set TPM_SERVER_PORT "$sport"
    [[ -n "$cport" ]] && env_set TPM_CTRL_PORT "$cport"
    notify_ok "Saved to .env. Use \"Apply Changes\" in Stack Control to rebuild."
}

runtime_framework() {
    local result
    result=$(zenity --forms --title="Runtime - Framework (c3)" \
        --text="API/dashboard ports and where the audit database lives." \
        --add-entry="Framework (API) port" \
        --add-entry="Dashboard port" \
        --add-entry="SQLite path" \
        --add-entry="Approval timeout (seconds)" \
        --separator="|" \
        2>/dev/null) || return
    IFS="|" read -r fport dport sqlite timeout <<< "$result"
    [[ -n "$fport" ]] && env_set FRAMEWORK_PORT "$fport"
    [[ -n "$dport" ]] && env_set DASHBOARD_PORT "$dport"
    [[ -n "$sqlite" ]] && env_set SQLITE_PATH "$sqlite"
    if [[ -n "$timeout" ]]; then
        if [[ "$timeout" =~ ^[0-9]+$ ]]; then
            env_set ALERT_TIMEOUT_SECONDS "$timeout"
        else
            notify_err "Approval timeout must be a whole number - not saved."
        fi
    fi
    notify_ok "Saved to .env. Use \"Apply Changes\" in Stack Control to rebuild."
}

runtime_display() {
    local current new
    current=$(env_get DISPLAY)
    new=$(zenity --entry --title="Runtime - X11 Display" \
        --text="Display for zenity popups from inside the c3 container (Linux host only).\nLeave empty to force the notify-send fallback." \
        --entry-text="$current" --width=400 2>/dev/null) || return
    env_set DISPLAY "$new"
    notify_ok "Saved to .env. Use \"Apply Changes\" in Stack Control to rebuild."
}

runtime_view() {
    zenity --text-info --title="Runtime - Current .env" --filename="$ENVFILE" --width=560 --height=440 2>/dev/null || true
}

menu_runtime() {
    while true; do
        choice=$(zenity --list --title="TrustEdge Tricks - Runtime Settings (.env)" \
            --text="Written to .env on disk. Apply from Stack Control to rebuild and pick these up." \
            --column="Category" --column="Description" \
            "Agent (c1)"     "Ollama model and host" \
            "RAG (c1)"       "Embedding model and how many chunks ground each task" \
            "TPM (c2)"       "swtpm server/control ports" \
            "Framework (c3)" "API/dashboard ports, DB path, approval timeout" \
            "X11 Display"    "Display used for zenity popups from c3" \
            "View .env"      "See the full current file" \
            --width=580 --height=400 2>/dev/null) || break
        case "$choice" in
            "Agent (c1)") runtime_agent ;;
            "RAG (c1)") runtime_rag ;;
            "TPM (c2)") runtime_tpm ;;
            "Framework (c3)") runtime_framework ;;
            "X11 Display") runtime_display ;;
            "View .env") runtime_view ;;
            *) break ;;
        esac
    done
}

# ===========================================================================
# CATEGORY 4: Stack Control  (docker compose lifecycle)
# ===========================================================================

stack_apply() {
    zenity --question --width=420 --text \
        "Rebuild and restart now?\n\nThis also resets the tamper-detection baseline\n(docker compose down -v && up --build -d)." 2>/dev/null || return
    ( cd "$REPO" && docker compose down -v && docker compose up --build -d ) 2>&1 | \
        zenity --progress --pulsate --auto-close --no-cancel --title="Applying" --text="Rebuilding containers..." 2>/dev/null || true
    notify_ok "Done.\nAPI:       ${FRAMEWORK_URL}\nDashboard: ${DASHBOARD_URL}"
}

stack_start() {
    ( cd "$REPO" && docker compose up -d ) 2>&1 | \
        zenity --progress --pulsate --auto-close --no-cancel --title="Starting" --text="Starting the stack..." 2>/dev/null || true
    notify_ok "Stack started."
}

stack_stop() {
    zenity --question --width=380 --text="Stop all TrustEdge containers?" 2>/dev/null || return
    ( cd "$REPO" && docker compose stop ) 2>&1 | \
        zenity --progress --pulsate --auto-close --no-cancel --title="Stopping" --text="Stopping the stack..." 2>/dev/null || true
    notify_ok "Stack stopped."
}

stack_restart() {
    ( cd "$REPO" && docker compose restart ) 2>&1 | \
        zenity --progress --pulsate --auto-close --no-cancel --title="Restarting" --text="Restarting the stack..." 2>/dev/null || true
    notify_ok "Stack restarted."
}

stack_status() {
    ( cd "$REPO" && docker compose ps ) | zenity --text-info --title="Stack Status" --width=700 --height=300 2>/dev/null || true
}

stack_logs() {
    local service
    service=$(zenity --list --title="View Logs" --text="Pick a container." \
        --column="Container" "c1-agent" "c2-tpm" "c3-framework" --width=360 --height=260 2>/dev/null) || return
    ( cd "$REPO" && docker compose logs --tail=200 "$service" ) | \
        zenity --text-info --title="Logs - $service" --width=800 --height=500 2>/dev/null || true
}

stack_reindex() {
    zenity --question --width=420 --text \
        "Reindex documents in c1/data now?\n\nRuns ingest.py inside the running c1 container - no restart needed." 2>/dev/null || return
    ( cd "$REPO" && docker compose exec c1-agent python ingest.py ) 2>&1 | \
        zenity --text-info --title="Reindexing" --width=700 --height=400 2>/dev/null || true
}

stack_open_dashboard() {
    xdg-open "$DASHBOARD_URL" >/dev/null 2>&1 &
    notify_ok "Opening $DASHBOARD_URL"
}

stack_health() {
    local resp
    if resp=$(curl -sf "$FRAMEWORK_URL/health"); then
        notify_ok "Framework is up:\n$resp"
    else
        notify_err "Could not reach $FRAMEWORK_URL/health.\nIs the stack running?"
    fi
}

menu_stack() {
    while true; do
        choice=$(zenity --list --title="TrustEdge Tricks - Stack Control" \
            --text="Manage the docker compose lifecycle." \
            --column="Category" --column="Description" \
            "Start"           "docker compose up -d" \
            "Stop"            "docker compose stop" \
            "Restart"         "docker compose restart" \
            "Apply Changes"   "Rebuild + reset baseline (needed after editing .env)" \
            "Status"          "docker compose ps" \
            "View Logs"       "Tail logs for one container" \
            "Reindex Documents" "Re-run RAG ingestion on c1/data without a restart" \
            "Open Dashboard"  "Open the audit log / approval queue in a browser" \
            "Health Check"    "Ping the framework's /health endpoint" \
            --width=620 --height=440 2>/dev/null) || break
        case "$choice" in
            "Start") stack_start ;;
            "Stop") stack_stop ;;
            "Restart") stack_restart ;;
            "Apply Changes") stack_apply ;;
            "Status") stack_status ;;
            "View Logs") stack_logs ;;
            "Reindex Documents") stack_reindex ;;
            "Open Dashboard") stack_open_dashboard ;;
            "Health Check") stack_health ;;
            *) break ;;
        esac
    done
}

# ===========================================================================
# main menu
# ===========================================================================

main_menu() {
    while true; do
        choice=$(zenity --list --title="TrustEdge Tricks" \
            --text="Everything TrustEdge is configured through here - no container shell, no hand-edited files." \
            --column="Category" --column="Description" \
            "Live Policy"        "Actions, sensitivity, denied targets, critical files, timeout" \
            "Pending Approvals"  "Review and ALLOW/BLOCK actions waiting on a human" \
            "Runtime Settings"   "Edit .env: ports, model, DB path, display" \
            "Stack Control"      "Start, stop, rebuild, logs, dashboard, health" \
            --width=620 --height=340 2>/dev/null) || break
        case "$choice" in
            "Live Policy") menu_policy ;;
            "Pending Approvals") menu_pending ;;
            "Runtime Settings") menu_runtime ;;
            "Stack Control") menu_stack ;;
            *) break ;;
        esac
    done
}

check_deps
main_menu
