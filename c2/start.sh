#!/bin/bash
TPMSERVE="2321"
TPMCTRL="2322"
echo "[*] starting swtpm"
/usr/bin/swtpm \
	socket \
	--tpm2 \
	--server type=tcp,port=$TPMSERVE,bindaddr=0.0.0.0 \
	--ctrl type=tcp,port=$TPMCTRL,bindaddr=0.0.0.0 \
	--flags not-need-init \
	--tpmstate dir=/var/lib/swtpm/tpmstate
