#!/usr/bin/env python3

import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="TrustEdge Dashboard", layout="wide")

st.title("🛡️ TrustEdge — Audit Logs")
st.markdown("### Security events from AI agent interception")

def load_logs():
    conn = sqlite3.connect("/app/audit.db")
    df = pd.read_sql_query("SELECT timestamp, action, target, reason FROM audit ORDER BY id DESC LIMIT 100", conn)
    conn.close()
    return df

df = load_logs()

if df.empty:
    st.info("No security events logged yet.")
else:
    st.dataframe(df, use_container_width=True)

st.markdown("---")
st.caption("TrustEdge Framework — Developed by SurendraS26")
