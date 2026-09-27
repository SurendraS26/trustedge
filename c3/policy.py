import re

DENYLIST_PATTERNS = [
    r"\brm\s+-rf\s+/", r"\bmkfs\b", r"\bdd\s+if=", r"\bshutdown\b",
    r"\breboot\b", r"\bhalt\b", r":\(\)\s*\{\s*:\|:&\s*\}\s*;\s*:",
    r"\bchmod\s+777\b", r"\buseradd\b", r"\buserdel\b", r"\bpasswd\b",
    r">\s*/dev/sd", r"\bfdisk\b", r"\bparted\b", r"\bmkswap\b",
    r"\bkillall\b", r"\bpkill\s+-9\b", r"\bchown\s+-R\s+/",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in DENYLIST_PATTERNS]


def classify(script: str) -> dict:
    for pattern in _COMPILED:
        if pattern.search(script):
            return {"decision": "BLOCK", "reason": f"script matches denied pattern: {pattern.pattern}"}
    return {"decision": "REVIEW", "reason": "no denied patterns found, needs confirmation"}

