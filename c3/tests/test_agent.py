"""
Verify the agent in c1 can produce a valid JSON decision from its Ollama
model. Requires the c1 container's Ollama server to be reachable (default:
http://c1-agent:11434 on the trustedge-net docker network). Run with:
    pytest tests/test_agent.py
"""

import os
import sys

C1_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "c1")
sys.path.insert(0, C1_DIR)

os.environ.setdefault("OLLAMA_HOST", "http://c1-agent:11434")

import main as agent_main  # noqa: E402


def test_ollama_is_reachable():
    assert agent_main.wait_for_ollama(max_wait_seconds=30), (
        f"could not reach ollama at {agent_main.OLLAMA_HOST}"
    )


def test_agent_produces_valid_decision():
    decision = agent_main.get_agent_decision(
        "Read the contents of /app/README.md so you can summarize it."
    )
    assert decision is not None, "agent did not return a parsable JSON decision"
    assert "action" in decision
    assert "target" in decision
    assert "reasoning" in decision


if __name__ == "__main__":
    test_ollama_is_reachable()
    test_agent_produces_valid_decision()
    print("test_agent: all tests passed")
