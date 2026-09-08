#!/bin/bash
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'
TPMSERVE="2321"
TPMCTRL="2322"
TPM2TOOLS_TCTI="swtpm:host=trustedge-c2,port=2321"
echo "Developed by **SurendraS26** (-_-) "
echo "Checkout: https://github.com/SurendraS26/swtpm-arch-docker"
echo "[*] Starting swtpm Arch container"
echo "[*] TPM will running in these below ip's only"
ip -br addr show
echo "server --> PORT=$TPMSERVE"
echo "ctrl   --> PORT=$TPMCTRL"
/usr/bin/swtpm \
	socket \
	--tpm2 \
	--server type=tcp,port=$TPMSERVE,bindaddr=0.0.0.0 \
	--ctrl type=tcp,port=$TPMCTRL,bindaddr=0.0.0.0 \
	--flags not-need-init \
	--tpmstate dir=/var/lib/swtpm/tpmstate



