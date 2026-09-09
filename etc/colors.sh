#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${GREEN}[✓]${NC} ${BOLD}${CYAN}TrustEdge${NC} — Starting..."
echo -e "${YELLOW}[!]${NC} ${BOLD}Warning:${NC} This is a test"
echo -e "${RED}[✗]${NC} ${BOLD}Error:${NC} Something failed"
echo -e "${BLUE}[i]${NC} ${BOLD}Info:${NC} System ready"
echo -e "${PURPLE}[*]${NC} ${BOLD}Processing...${NC}"
