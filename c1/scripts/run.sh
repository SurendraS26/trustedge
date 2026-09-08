#!/bin/bash
echo "[*] Executing start_swtpm-arch-container...."
docker run -p 2321-2322:2321-2322 trustedge-c1
echo "[*] Shutdown complete (*_*)"
