"""
TrustEdge Dashboard

Utilitarian Minimalist Streamlit view of the audit log: a single, clean
table with proper column headers and structured rows. No charts, no
colors beyond a plain ALLOW/BLOCK/REVIEW text marker, no clutter.
"""

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

st.title("TrustEdge Audit Log")

alert_log = AlertLog()
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
