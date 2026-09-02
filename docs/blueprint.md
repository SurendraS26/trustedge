```
trustedge/
├── c1/                              # Container 1: agent + framework
│   ├── agent/
│   │   ├── ollama_agent.py
│   │   └── Modelfile
│   ├── policy_engine/
│   │   ├── policy_engine.py
│   │   └── policy.json
│   ├── interceptor/
│   │   ├── audit_rules.sh          # Auditctl rules
│   │   ├── interceptor.py          # Auditctl command line script but in python
│   │   └── hash_reader.py          # sha256 hashing tool for reading
│   ├── integrity_monitor/
│   │   ├── integrity_monitor.py
│   │   └── measured_files.json     # it will list hashes
│   ├── attestation_manager/
│   │   └── attestation_manager.py
│   ├── verifier/
│   │   └── verifier.py
│   ├── baseline_store/
│   │   ├── baseline_store.py       
│   │   └── baseline.db             # database baseline
│   ├── alerts/
│   │   ├── alert_log.py
│   │   └── audit.db                # sqlite store audit log
│   ├── Dockerfile
│   └── requirements.txt
│
├── c2/                              # Container 2: swtpm-arch-docker
│   ├── Dockerfile                   # we clone from my existing swtpm-arch-docker build
│   └── README.md
│
├── docs/
│   ├── architecture.md
│   └── user_guide.md
│
├── docker-compose.yml
└── README.md
```
