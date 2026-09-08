#!/usr/bin/env bash
# TrustEdge Policy Editor - a zenity front-end for policy.json and .env.
# Run this on your HOST (not inside a container) - it edits the repo's
# config files directly, then optionally rebuilds and restarts the stack.
set -e

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
POLICY="$REPO/c3/policy.json"
ENVFILE="$REPO/.env"

command -v zenity >/dev/null 2>&1 || { echo "zenity not found - install it first"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "python3 not found - install it first"; exit 1; }
[[ -f "$POLICY" ]] || { echo "can't find $POLICY"; exit 1; }
[[ -f "$ENVFILE" ]] || cp "$REPO/.env.example" "$ENVFILE"

ALL_ACTIONS="read_file write_file run_command network_call delete_file none"

get_list() { # $1 = json key
    python3 -c "import json;print(' '.join(json.load(open('$POLICY')).get('$1', [])))"
}

set_list() { # $1 = json key, $2 = space-separated values
    python3 - "$POLICY" "$1" "$2" <<'PY'
import json, sys
path, key, values = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(path))
d[key] = values.split()
json.dump(d, open(path, "w"), indent=2)
PY
}

edit_actions() {
    current=$(get_list allowed_actions)
    args=()
    for a in $ALL_ACTIONS; do
        state="FALSE"; [[ " $current " == *" $a "* ]] && state="TRUE"
        args+=("$state" "$a")
    done
    selected=$(zenity --list --checklist --width=420 --height=320 \
        --title "Allowed actions" \
        --text "Which actions can the agent ever propose?" \
        --column "Pick" --column "Action" "${args[@]}" --separator=" ") || return
    [[ -z "$selected" ]] && { zenity --error --text "At least one action must stay allowed."; return; }
    set_list allowed_actions "$selected"

    current_sensitive=$(get_list sensitive_actions)
    args=()
    for a in $selected; do
        state="FALSE"; [[ " $current_sensitive " == *" $a "* ]] && state="TRUE"
        args+=("$state" "$a")
    done
    sensitive=$(zenity --list --checklist --width=420 --height=320 \
        --title "Sensitive actions" \
        --text "Which of those need TPM attestation + human ALLOW/BLOCK?" \
        --column "Pick" --column "Action" "${args[@]}" --separator=" ") || sensitive=""
    set_list sensitive_actions "$sensitive"

    non_sensitive=""
    for a in $selected; do
        [[ " $sensitive " == *" $a "* ]] || non_sensitive="$non_sensitive $a"
    done
    set_list non_sensitive_actions "$non_sensitive"
    zenity --info --text "Actions updated in policy.json."
}

edit_denied_targets() {
    tmp=$(mktemp)
    python3 -c "import json;print('\n'.join(json.load(open('$POLICY'))['denied_targets']))" > "$tmp"
    new=$(zenity --text-info --editable --width=500 --height=350 \
        --title "Denied targets (one pattern per line)" --filename "$tmp") || { rm -f "$tmp"; return; }
    rm -f "$tmp"
    python3 - "$POLICY" <<PY
import json
d = json.load(open("$POLICY"))
d["denied_targets"] = [l for l in """$new""".splitlines() if l.strip()]
json.dump(d, open("$POLICY", "w"), indent=2)
PY
    zenity --info --text "Denied targets updated."
}

edit_env() {
    model=$(grep -E '^OLLAMA_MODEL=' "$ENVFILE" | cut -d= -f2-)
    timeout=$(grep -E '^ALERT_TIMEOUT_SECONDS=' "$ENVFILE" | cut -d= -f2-)
    result=$(zenity --forms --title "Runtime settings (.env)" \
        --text "These take effect after Apply." \
        --add-entry="Ollama model" \
        --add-entry="Approval timeout (seconds)" \
        --separator="|" 2>/dev/null) || return
    IFS="|" read -r new_model new_timeout <<< "$result"
    new_model="${new_model:-$model}"
    new_timeout="${new_timeout:-${timeout:-30}}"
    grep -vE '^(OLLAMA_MODEL|ALERT_TIMEOUT_SECONDS)=' "$ENVFILE" > "$ENVFILE.tmp" || true
    { echo "OLLAMA_MODEL=$new_model"; echo "ALERT_TIMEOUT_SECONDS=$new_timeout"; cat "$ENVFILE.tmp"; } > "$ENVFILE"
    rm -f "$ENVFILE.tmp"
    zenity --info --text "Saved to .env."
}

apply_changes() {
    zenity --question --width=400 --text \
        "Rebuild and restart now?\n\nThis also resets the tamper-detection baseline\n(docker compose down -v && up --build -d)." || return
    (cd "$REPO" && docker compose down -v && docker compose up --build -d) \
        | zenity --progress --pulsate --auto-close --title "Applying" --text "Rebuilding containers..."
    zenity --info --text "Done.\nDashboard: http://localhost:8501\nWeb agent: http://localhost:5000"
}

while true; do
    choice=$(zenity --list --width=420 --height=300 \
        --title "TrustEdge Policy Editor" \
        --column "Option" \
        "Edit allowed / sensitive actions" \
        "Edit denied targets" \
        "Edit runtime settings (.env)" \
        "Apply changes (rebuild + reset baseline)" \
        "Quit") || break
    case "$choice" in
        "Edit allowed"*) edit_actions ;;
        "Edit denied"*) edit_denied_targets ;;
        "Edit runtime"*) edit_env ;;
        "Apply changes"*) apply_changes ;;
        *) break ;;
    esac
done
