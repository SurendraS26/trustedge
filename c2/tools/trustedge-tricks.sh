#!/usr/bin/env bash
set -e

APP_DIR="/app"
ENV_FILE="${APP_DIR}/.env"
POLICY_RULES="${APP_DIR}/framework/policy_rules.json"
MEASURED_FILES="${APP_DIR}/framework/measured_files.json"

get_env() { grep "^$1=" "${ENV_FILE}" | cut -d '=' -f2-; }
set_env() {
    local key="$1" val="$2"
    if grep -q "^${key}=" "${ENV_FILE}"; then
        sed -i "s|^${key}=.*|${key}=${val}|" "${ENV_FILE}"
    else
        echo "${key}=${val}" >> "${ENV_FILE}"
    fi
}

menu_main() {
    zenity --list --title="TrustEdge Tricks" --width=420 --height=420 \
        --column="Category" \
        "Policy Engine" \
        "Integrity Monitor" \
        "Baseline Store" \
        "Attestation Manager" \
        "Verifier" \
        "Popup Layer" \
        "Audit Log" \
        "Runtime Settings"
}

menu_policy_engine() {
    gedit --wait "${POLICY_RULES}"
}

menu_integrity_monitor() {
    gedit --wait "${MEASURED_FILES}"
}

menu_baseline_store() {
    zenity --question --text="Re-initialize the trusted baseline now?" \
        --ok-label="Re-initialize" --cancel-label="Cancel" \
    && python3 -c "from framework.baseline_store import reinitialize; reinitialize()"
}

menu_attestation_manager() {
    local pcr
    pcr=$(get_env PCR_RANGE)
    pcr=$(zenity --entry --title="PCR Range" --text="PCR index range" --entry-text="${pcr}")
    [ -n "${pcr}" ] && set_env PCR_RANGE "${pcr}"
}

menu_verifier() {
    local choice
    choice=$(zenity --list --radiolist --title="On verification failure" \
        --column="" --column="Behavior" \
        FALSE "deny_alert" FALSE "deny_halt" FALSE "deny_manual_override")
    [ -n "${choice}" ] && set_env VERIFIER_FAILURE_MODE "${choice}"
}

menu_popup_layer() {
    local timeout
    timeout=$(get_env POPUP_TIMEOUT_SECONDS)
    timeout=$(zenity --entry --title="Popup timeout (seconds)" --entry-text="${timeout}")
    [ -n "${timeout}" ] && set_env POPUP_TIMEOUT_SECONDS "${timeout}"
}

menu_audit_log() {
    zenity --text-info --title="Audit Log" --filename="${APP_DIR}/audit/audit_log.db" --width=600 --height=400 || true
}

menu_runtime_settings() {
    local model
    model=$(get_env OLLAMA_MODEL)
    model=$(zenity --entry --title="Ollama Model" --entry-text="${model}")
    [ -n "${model}" ] && set_env OLLAMA_MODEL "${model}"
}

CHOICE=$(menu_main)
case "${CHOICE}" in
    "Policy Engine") menu_policy_engine ;;
    "Integrity Monitor") menu_integrity_monitor ;;
    "Baseline Store") menu_baseline_store ;;
    "Attestation Manager") menu_attestation_manager ;;
    "Verifier") menu_verifier ;;
    "Popup Layer") menu_popup_layer ;;
    "Audit Log") menu_audit_log ;;
    "Runtime Settings") menu_runtime_settings ;;
esac
