import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [c1-ingest] %(levelname)s %(message)s",
)
log = logging.getLogger("ingest")

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "mxbai-embed-large")
DATA_DIR = os.environ.get("RAG_DATA_DIR", "./data")
DB_DIR = os.environ.get("RAG_DB_DIR", "./chroma_db")
CHUNK_SIZE = int(os.environ.get("RAG_CHUNK_SIZE", 512))
CHUNK_OVERLAP = int(os.environ.get("RAG_CHUNK_OVERLAP", 64))


def load_documents():
    from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader

    documents = []
    for glob, loader_cls, kwargs in (
        ("**/*.txt", TextLoader, {"encoding": "utf-8"}),
        ("**/*.md", TextLoader, {"encoding": "utf-8"}),
    ):
        loader = DirectoryLoader(DATA_DIR, glob=glob, loader_cls=loader_cls, loader_kwargs=kwargs)
        documents.extend(loader.load())

    pdf_loader = DirectoryLoader(DATA_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader)
    documents.extend(pdf_loader.load())
    return documents


def has_indexable_files():
    if not os.path.isdir(DATA_DIR):
        return False
    for _root, _dirs, files in os.walk(DATA_DIR):
        if any(f.lower().endswith((".txt", ".md", ".pdf")) for f in files):
            return True
    return False


def main():
    if not has_indexable_files():
        log.info("%s has no .txt/.md/.pdf files, skipping - agent runs without RAG context", DATA_DIR)
        return

    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_ollama import OllamaEmbeddings
    from langchain_community.vectorstores import Chroma

    documents = load_documents()
    log.info("loaded %d documents from %s", len(documents), DATA_DIR)
    if not documents:
        return

    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_documents(documents)
    log.info("created %d chunks", len(chunks))

    embeddings = OllamaEmbeddings(model=EMBED_MODEL, base_url=OLLAMA_HOST)
    db = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=DB_DIR)
    db.persist()
    log.info("vector store saved to %s", DB_DIR)


if __name__ == "__main__":
    main()
