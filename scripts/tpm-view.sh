#!/usr/bin/env bash
TCTI="swtpm:host=127.0.0.1,port=2321"
tpm2_startup -T $TCTI -c
watch -n 0.1 tpm2_pcrread -T $TCTI sha256
