#!/usr/bin/env bash
# Starts all four containers in the background. Then use:
#   ./scripts/agent.sh       - talk to the agent
#   ./scripts/dashboard.sh   - live dashboard
set -e
cd "$(dirname "$0")"
./create-network.sh
./run-c2.sh
./run-c4.sh
./run-c3.sh
./run-c1.sh
echo ""
echo "started: trustedge-c1 c2 c3 c4"
echo "desktop:  http://localhost:6080/vnc.html  (password: trustedge)"
echo "model status: docker logs -f trustedge-c1   (wait for '[c1] ready')"
