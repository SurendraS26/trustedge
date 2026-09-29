#!/usr/bin/env bash
# Open the agent prompt (instant, no docker attach).
# Ctrl-C only closes the prompt, the containers keep running.
exec docker exec -it trustedge-c1 python /app/agent.py
