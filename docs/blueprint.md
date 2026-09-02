```
trustedge/
├── c1/                              # Container 1: Agent + Framework
│   ├── agent/
│   │   ├── ollama_agent.py
│   │   └── Modelfile
│   ├── policy_engine/
│   │   ├── policy_engine.py
│   │   └── policy.json
│   ├── interceptor/
│   │   ├── audit_rules.sh          # sets up auditd watch rules
│   │   ├── interceptor.py          # tails auditd, parses execve events
│   │   └── hash_reader.py          # SHA-256 file hashing utility
│   ├── integrity_monitor/
│   │   ├── integrity_monitor.py
│   │   └── measured_files.json     # list of critical files to hash
│   ├── attestation_manager/
│   │   └── attestation_manager.py
│   ├── verifier/
│   │   └── verifier.py
│   ├── baseline_store/
│   │   ├── baseline_store.py
│   │   └── baseline.db             # created at init time
│   ├── alerts/
│   │   ├── alert_log.py
│   │   └── audit.db                # SQLite audit log
│   ├── Dockerfile
│   └── requirements.txt
│
├── c2/                              # Container 2: swtpm
│   ├── Dockerfile                   # your existing swtpm-arch-docker build
│   └── README.md
│
├── docs/
│   ├── architecture.md
│   └── user_guide.md
│
├── docker-compose.yml
└── README.md
```
