import logging
import time

log = logging.getLogger("interceptor")

REQUIRED_FIELDS = ("action", "target", "reasoning")


class InterceptedRequest:
    def __init__(self, action, target, reasoning, received_at):
        self.action = action
        self.target = target
        self.reasoning = reasoning
        self.received_at = received_at

    def as_dict(self):
        return {
            "action": self.action,
            "target": self.target,
            "reasoning": self.reasoning,
            "received_at": self.received_at,
        }


class Interceptor:
    def capture(self, payload):
        """
        Validate and normalize a raw request payload.

        Returns an InterceptedRequest on success, or raises ValueError with
        a human-readable message if the payload is malformed.
        """
        if not isinstance(payload, dict):
            raise ValueError("request payload must be a JSON object")

        missing = [f for f in REQUIRED_FIELDS if f not in payload]
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")

        action = str(payload["action"]).strip()
        target = str(payload["target"]).strip()
        reasoning = str(payload["reasoning"]).strip()

        if not action:
            raise ValueError("'action' must not be empty")

        request = InterceptedRequest(
            action=action,
            target=target,
            reasoning=reasoning,
            received_at=time.time(),
        )
        log.info("intercepted request: action=%s target=%s", action, target)
        return request
