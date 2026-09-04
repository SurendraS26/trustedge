#!/bin/bash

# Shitty colors

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'

# This is the port number , don't edit this boy/girl

TPMSERVE="2321"
TPMCTRL="2322"

# Startup script (visual)

echo "[*] Starting swtpm-arch-container...."
echo "[*] TPM running ip: 0.0.0.0"
echo "server --> 0.0.0.0 , PORT=$TPMSERVE"
echo "ctrl   --> 0.0.0.0 , PORT=$TPMCTRL"

# Run swtpm (Own version is better than slop i feel alva)

/usr/bin/swtpm \
	socket \
	--tpm2 \
	--server type=tcp,port=$TPMSERVE,bindaddr=0.0.0.0 \
	--ctrl type=tcp,port=$TPMCTRL,bindaddr=0.0.0.0 \
	--flags not-need-init \
	--tpmstate dir=/var/lib/swtpm/tpmstate



