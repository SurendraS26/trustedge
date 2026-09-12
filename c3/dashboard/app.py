import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.alert_log import AlertLog

st.set_page_config(page_title="TrustEdge Audit Log", layout="wide")

PLAIN_TABLE_CSS = """
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 2rem;}
    table {
        width: 100%;
        border-collapse: collapse;
        font-family: monospace;
        font-size: 14px;
    }
    thead th {
        text-align: left;
        border-bottom: 2px solid #333;
        padding: 6px 10px;
    }
    tbody td {
        border-bottom: 1px solid #ddd;
        padding: 6px 10px;
    }
</style>
"""
st.markdown(PLAIN_TABLE_CSS, unsafe_allow_html=True)

st.title("TE Bare/Box Audit Log")

alert_log = AlertLog()

pending = alert_log.list_unresolved_pending()
if pending:
    st.markdown('<meta http-equiv="refresh" content="2">', unsafe_allow_html=True)
    st.subheader(f"Pending approval ({len(pending)})")
    for item in pending:
        with st.container(border=True):
            st.write(f"**{item['action']}** → `{item['target']}`")
            st.caption(item["reasoning"] or "")
            col1, col2 = st.columns(2)
            if col1.button("ALLOW", key=f"allow-{item['id']}"):
                alert_log.resolve_pending(item["id"], "ALLOW")
                st.rerun()
            if col2.button("BLOCK", key=f"block-{item['id']}"):
                alert_log.resolve_pending(item["id"], "BLOCK")
                st.rerun()
    st.divider()

entries = alert_log.recent_entries(limit=500)

if not entries:
    st.write("No audit entries yet. Submit an action from the agent to populate this log.")
else:
    df = pd.DataFrame(entries)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    df = df.rename(columns={
        "id": "ID",
        "timestamp": "Time",
        "action": "Action",
        "target": "Target",
        "reasoning": "Reasoning",
        "classification": "Classification",
        "attested": "Attested",
        "final_decision": "Decision",
        "reason": "Reason",
    })
    columns = ["ID", "Time", "Action", "Target", "Classification", "Attested", "Decision", "Reasoning", "Reason"]
    st.write(df[columns].to_html(index=False), unsafe_allow_html=True)

    st.caption(f"{len(entries)} entries shown (most recent first, limit 500)")

if st.button("Refresh"):
    st.rerun()
