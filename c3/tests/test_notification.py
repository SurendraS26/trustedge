"""
Exercise the notification path directly: sends a dummy action through
AlertLog.prompt_operator and reports whether Zenity or notify-send fired,
and what the operator chose (if anything).

This test requires a human to actually click ALLOW or BLOCK when the
Zenity popup appears, so it is not run automatically by pytest's default
collection assumptions - run it directly:

    python tests/test_notification.py

Or, to also assert it under pytest, pass --run-interactive:
    pytest tests/test_notification.py --run-interactive
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SQLITE_PATH", "/tmp/trustedge-test.db")

from modules.alert_log import AlertLog


def run_notification_check():
    alert_log = AlertLog()

    print("Sending a dummy sensitive action to trigger a notification.")
    print(f"zenity available: {alert_log._zenity_available()}")
    print(f"notify-send available: {alert_log._notify_send_available()}")

    if alert_log._zenity_available():
        print("A Zenity popup should appear now with ALLOW/BLOCK buttons")
        print("and a 30 second timeout. Please respond to it.")
    elif alert_log._notify_send_available():
        print("No X11 display detected. Falling back to a plain notify-send")
        print("notification (informational only, no ALLOW/BLOCK response).")
    else:
        print("Neither zenity nor notify-send is available in this environment.")

    choice = alert_log.prompt_operator(
        action="write_file",
        target="/app/test_output.txt",
        reasoning="test_notification.py dummy action",
    )

    if choice is None:
        print("Result: no interactive response captured (fallback or timeout).")
    else:
        print(f"Result: operator responded with {choice}")

    return choice


def test_notification_path_runs_without_error():
    """Smoke test: the notification path should never raise, regardless of
    whether a display is available."""
    choice = run_notification_check()
    assert choice in ("ALLOW", "BLOCK", None)


if __name__ == "__main__":
    run_notification_check()
    print("test_notification: completed")
