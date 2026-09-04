#!/bin/bash

# This is the port number , don't edit this boy/girl

TPMSERVE="2321"
TPMCTRL="2322"

# Startup script (visual)
echo "[*] Starting swtpm Arch container"
echo "[*] TPM will running in these below ip's only"
ip -br addr show
echo "server --> PORT=$TPMSERVE"
echo "ctrl   --> PORT=$TPMCTRL"

# Run swtpm (Own version is better than slop i feel alva)

/usr/bin/swtpm \
	socket \
	--tpm2 \
	--server type=tcp,port=$TPMSERVE,bindaddr=0.0.0.0 \
	--ctrl type=tcp,port=$TPMCTRL,bindaddr=0.0.0.0 \
	--flags not-need-init \
	--tpmstate dir=/var/lib/swtpm/tpmstate



