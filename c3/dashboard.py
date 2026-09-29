import os
import time
import logstore

DASHBOARD_PATH = os.environ.get("DASHBOARD_PATH", "/data/dashboard.md")


def render():
    entries = logstore.recent(15)

    lines = [
        "```",
        "╺┳┓┏━┓┏━┓╻ ╻┏┓ ┏━┓┏━┓┏━┓╺┳┓",
        " ┃┃┣━┫┗━┓┣━┫┣┻┓┃ ┃┣━┫┣┳┛ ┃┃",
        "╺┻┛╹ ╹┗━┛╹ ╹┗━┛┗━┛╹ ╹╹┗╸╺┻┛",
        "```",
        "",
        "Trustedge C3 Framework Execution logs.",
        "",
        "# trustedge-c3",
        "",
        f"_last updated {time.strftime('%H:%M:%S')}_",
        "",
        "## recent activity",
        "",
        "| time | decision | reason | script |",
        "|---|---|---|---|",
    ]

    if not entries:
        lines.append("| - | - | no activity yet | - |")
    else:
        for e in entries:
            ts = time.strftime("%H:%M:%S", time.localtime(e["timestamp"]))
            script_preview = (e["script"] or "").strip().replace("\n", " ")[:40]
            lines.append(f"| {ts} | **{e['decision']}** | {e['reason'][:50]} | `{script_preview}` |")

    tmp_path = DASHBOARD_PATH + ".tmp"
    with open(tmp_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    os.replace(tmp_path, DASHBOARD_PATH)
