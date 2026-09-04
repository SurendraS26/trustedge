#!/bin/bash
# This is the port number , don't edit this man
TPMSERVE="2321"
TPMCTRL="2322"
# Startup script (visual)
echo "[*] Starting swtpm-arch-container...."
echo "[*] TPM running ip: 0.0.0.0"
echo "server --> 0.0.0.0 , PORT=$TPMSERVE"
echo "ctrl   --> 0.0.0.0 , PORT=$TPMCTRL"
# Run swtpm
/usr/bin/swtpm \
	socket \
	--tpm2 \
	--server type=tcp,port=$TPMSERVE,bindaddr=0.0.0.0 \
	--ctrl type=tcp,port=$TPMCTRL,bindaddr=0.0.0.0 \
	--flags not-need-init \
	--tpmstate dir=/var/lib/swtpm/tpmstate



