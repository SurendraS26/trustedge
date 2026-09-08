#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
POLICY_RULES="${ROOT_DIR}/c2/framework/policy_rules.json"
MEASURED_FILES="${ROOT_DIR}/c2/framework/measured_files.json"

get_env() {
    grep "^$1=" "${ENV_FILE}" | cut -d '=' -f2-
}

set_env() {
    local key="$1" val="$2"
    if grep -q "^${key}=" "${ENV_FILE}"; then
        sed -i "s|^${key}=.*|${key}=${val}|" "${ENV_FILE}"
    else
        echo "${key}=${val}" >> "${ENV_FILE}"
    fi
}

restart_prompt() {
    local service="$1"
    if zenity --question --title="Restart required" \
        --text="This change needs '${service}' restarted to take effect. Restart now?"; then
        (cd "${ROOT_DIR}" && docker compose restart "${service}")
        zenity --info --text="${service} restarted."
    fi
}

edit_policy_rules() {
    gedit --wait "${POLICY_RULES}"
    zenity --info --text="policy_rules.json saved.\nPolicy Engine re-reads it live -- no restart needed."
}

edit_measured_files() {
    gedit --wait "${MEASURED_FILES}"
    zenity --info --text="measured_files.json saved.\nRun 'Re-initialize baseline' next, or the next attestation will fail for any newly added file."
}

reinitialize_baseline() {
    if zenity --question --text="This re-trusts the current state of all measured files as the new baseline. Continue?"; then
        docker compose exec c2-framework python -c \
            "from framework.baseline_store import reinitialize; print(reinitialize())"
        zenity --info --text="Baseline re-initialized."
    fi
}

view_baseline() {
    local out
    out=$(docker compose exec c2-framework python -c \
        "from framework.baseline_store import get_baseline; import json; print(json.dumps(get_baseline(), indent=2))")
    echo "${out}" | zenity --text-info --title="Current Baseline" --width=600 --height=400
}

select_model() {
    local model
    model=$(zenity --list --title="Select Ollama Model" --column="Model" \
        "qwen2.5:3b" "llama3.2:3b" "custom...")
    if [ "${model}" = "custom..." ]; then
        model=$(zenity --entry --title="Custom Model" --text="Enter Ollama model tag:")
    fi
    [ -n "${model}" ] && set_env "OLLAMA_MODEL" "${model}" && restart_prompt "c1-agent"
}

toggle_gpu() {
    zenity --info --text="GPU passthrough is set in docker-compose.yml under c1-agent's 'deploy.resources' block.\nComment/uncomment that block manually, then restart c1."
}

popup_timeout_settings() {
    local seconds
    seconds=$(zenity --entry --title="Popup Timeout" \
        --text="Seconds before an unanswered popup times out:" \
        --entry-text="$(get_env POPUP_TIMEOUT_SECONDS)")
    [ -n "${seconds}" ] && set_env "POPUP_TIMEOUT_SECONDS" "${seconds}"

    local action
    action=$(zenity --list --title="Timeout Behavior" --column="Action" \
        "deny" "allow")
    [ -n "${action}" ] && set_env "POPUP_TIMEOUT_ACTION" "${action}"

    restart_prompt "c2-framework"
}

audit_log_settings() {
    local mode
    mode=$(zenity --list --title="Audit Log Mode" --column="Mode" \
        "allow_and_deny" "deny_only")
    [ -n "${mode}" ] && set_env "AUDIT_LOG_MODE" "${mode}"

    local days
    days=$(zenity --entry --title="Retention" --text="Retention (days):" \
        --entry-text="$(get_env AUDIT_LOG_RETENTION_DAYS)")
    [ -n "${days}" ] && set_env "AUDIT_LOG_RETENTION_DAYS" "${days}"

    restart_prompt "c2-framework"
}

docker_controls() {
    local choice
    choice=$(zenity --list --title="Docker Compose Stack" --column="Action" \
        "Start all" "Stop all" "Restart c1-agent" "Restart c2-framework" "View c1 logs" "View c2 logs")
    case "${choice}" in
        "Start all") (cd "${ROOT_DIR}" && docker compose up -d) ;;
        "Stop all") (cd "${ROOT_DIR}" && docker compose down) ;;
        "Restart c1-agent") (cd "${ROOT_DIR}" && docker compose restart c1-agent) ;;
        "Restart c2-framework") (cd "${ROOT_DIR}" && docker compose restart c2-framework) ;;
        "View c1 logs") (cd "${ROOT_DIR}" && docker compose logs --tail=200 c1-agent) | zenity --text-info --width=700 --height=500 ;;
        "View c2 logs") (cd "${ROOT_DIR}" && docker compose logs --tail=200 c2-framework) | zenity --text-info --width=700 --height=500 ;;
    esac
}

main_menu() {
    CHOICE=$(zenity --list --title="TrustEdge Tricks" \
        --text="Select a category:" \
        --column="Category" --height=420 --width=420 \
        "Policy Engine" \
        "Integrity Monitor" \
        "Baseline Store" \
        "Zenity Popup Layer" \
        "Audit Log" \
        "Docker Compose Stack" \
        ".env Runtime Settings")

    case "${CHOICE}" in
        "Policy Engine") edit_policy_rules ;;
        "Integrity Monitor") edit_measured_files ;;
        "Baseline Store")
            sub=$(zenity --list --title="Baseline Store" --column="Action" \
                "Re-initialize baseline" "View current baseline")
            [ "${sub}" = "Re-initialize baseline" ] && reinitialize_baseline
            [ "${sub}" = "View current baseline" ] && view_baseline
            ;;
        "Zenity Popup Layer") popup_timeout_settings ;;
        "Audit Log") audit_log_settings ;;
        "Docker Compose Stack") docker_controls ;;
        ".env Runtime Settings")
            sub=$(zenity --list --title=".env Settings" --column="Setting" \
                "Select Ollama model" "GPU passthrough info")
            [ "${sub}" = "Select Ollama model" ] && select_model
            [ "${sub}" = "GPU passthrough info" ] && toggle_gpu
            ;;
    esac
}

main_menu
