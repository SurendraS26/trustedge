#!/usr/bin/env bash
DASHBOARD_PATH="${DASHBOARD_PATH:-/data/dashboard.md}"
touch "$DASHBOARD_PATH"
echo "$DASHBOARD_PATH" | entr -c glow "$DASHBOARD_PATH"
