from policy import classify


def intercept(script: str) -> dict:
    if script is None or not script.strip():
        return {"decision": "BLOCK", "reason": "empty or missing script"}
    return classify(script)
