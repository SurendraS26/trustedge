import json
import os

RULES_PATH = os.path.join(os.path.dirname(__file__), "policy_rules.json")


def _load_rules() -> dict:
    with open(RULES_PATH, "r") as f:
        return json.load(f)


def classify(action_type: str) -> dict:
    config = _load_rules()
    for rule in config["rules"]:
        if rule["action_type"] == action_type:
            return {"sensitive": rule["sensitive"], "urgency": rule["urgency"]}
    return config["default"]
