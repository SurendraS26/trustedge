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
TPM2TOOLS_TCTI="swtpm:host=127.0.0.1,port=2321"
echo -e ""
echo -e "${NC}${BOLD}SWTPM-Arch-Docker x86_64 Build.${NC}"
echo -e "${NC}Github: ${BOLD}SurendraS26${NC} ${YELLOW}(-_-)${NC}"
echo -e "${BLUE}${BOLD}Checkout${BOLD}${NC} https://github.com/SurendraS26/swtpm-arch-docker"
echo -e ""
echo -e "${CYAN}[*]${NC} Starting swtpm Arch container"
echo -e "${CYAN}[*]${NC} TPM will running in these below ip's only"
ip -br addr show
echo -e "${GREEN}server -->${NC} PORT=$TPMSERVE"
echo -e "${GREEN}ctrl   -->${NC} PORT=$TPMCTRL"
echo -e "${CYAN}To stop container${CYAN} ${NC}'${BOLD}docker stop <eg: swtpm-arch>${BOLD}'${NC}"
/usr/bin/swtpm \
	socket \
	--tpm2 \
	--server type=tcp,port=$TPMSERVE,bindaddr=0.0.0.0 \
	--ctrl type=tcp,port=$TPMCTRL,bindaddr=0.0.0.0 \
	--flags not-need-init \
	--tpmstate dir=/var/lib/swtpm/tpmstate



