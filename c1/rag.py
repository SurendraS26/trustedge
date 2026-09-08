"""
TrustEdge - Container 1: RAG retriever

Called from main.py right before the model is asked for a decision. Pulls
the top-k most relevant chunks out of the local ChromaDB store built by
ingest.py and folds them into the task prompt as grounding context, so
the agent's proposed action can reference your own docs/runbooks instead
of only the model's training data.

Fails soft on purpose: if no store has been built yet, or Ollama/Chroma
aren't reachable, build_prompt() just returns the task unchanged. RAG is
an enrichment step here, never a precondition for the agent to run - and
it never talks to c3 or executes anything itself, so it sits entirely
before the policy gate.
"""

import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [c1-rag] %(levelname)s %(message)s",
)
log = logging.getLogger("rag")

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "mxbai-embed-large")
DB_DIR = os.environ.get("RAG_DB_DIR", "./chroma_db")
TOP_K = int(os.environ.get("RAG_TOP_K", 4))

_db = None
_load_attempted = False


def _get_db():
    global _db, _load_attempted
    if _db is not None or _load_attempted:
        return _db
    _load_attempted = True

    if not os.path.isdir(DB_DIR):
        log.info("no vector store at %s yet, running without RAG context", DB_DIR)
        return None

    try:
        from langchain_ollama import OllamaEmbeddings
        from langchain_community.vectorstores import Chroma

        embeddings = OllamaEmbeddings(model=EMBED_MODEL, base_url=OLLAMA_HOST)
        _db = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
        return _db
    except Exception as exc:  # noqa: BLE001
        log.warning("could not load vector store, continuing without it: %s", exc)
        return None


def build_prompt(task_description):
    """Return task_description, prefixed with retrieved local context when available."""
    db = _get_db()
    if db is None:
        return task_description

    try:
        hits = db.similarity_search(task_description, k=TOP_K)
    except Exception as exc:  # noqa: BLE001
        log.warning("retrieval failed, continuing without context: %s", exc)
        return task_description

    if not hits:
        return task_description

    context = "\n\n".join(
        f"[{hit.metadata.get('source', 'doc')}]\n{hit.page_content}" for hit in hits
    )
    return (
        "Relevant context from local documents:\n"
        f"{context}\n\n"
        "Task:\n"
        f"{task_description}"
    )
