"""
RAG Service — ChromaDB vector search for clinical triage guidelines.
Uses HuggingFace all-MiniLM-L6-v2 embeddings with persistent Chroma store.
"""
import os
from typing import List

from langchain_community.document_loaders import DirectoryLoader, TextLoader

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        from langchain_community.text_splitter import RecursiveCharacterTextSplitter

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma

from app.core.config import settings

# Module-level cached instances
_embedding_instance = None
_vector_store_instance = None


def get_embedding_model() -> HuggingFaceEmbeddings:
    """Returns or initializes the HuggingFace sentence-transformer embedding model."""
    global _embedding_instance
    if _embedding_instance is None:
        _embedding_instance = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embedding_instance


def initialize_kb(
    data_dir: str = settings.GUIDELINES_DIR,
    persist_dir: str = settings.CHROMA_PERSIST_DIR,
) -> Chroma:
    """
    Load guideline .txt files, chunk them, and build a persistent Chroma vector store.
    """
    global _vector_store_instance

    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        print(f"[RAG] Created guidelines directory: {data_dir}")
        return None

    txt_files = [f for f in os.listdir(data_dir) if f.endswith(".txt")]
    if not txt_files:
        print(f"[RAG] No .txt files found in '{data_dir}'. Skipping KB init.")
        return None

    loader = DirectoryLoader(
        data_dir,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    documents = loader.load()

    if not documents:
        print(f"[RAG] No documents loaded from '{data_dir}'.")
        return None

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = text_splitter.split_documents(documents)
    print(f"[RAG] Loaded {len(documents)} document(s), split into {len(chunks)} chunks.")

    embeddings = get_embedding_model()
    _vector_store_instance = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir,
    )
    print(f"[RAG] Knowledge base initialized → '{persist_dir}'")
    return _vector_store_instance


def get_relevant_context(query: str, k: int = 3) -> List[str]:
    """Search the vector store for top-k relevant guideline chunks."""
    global _vector_store_instance

    if _vector_store_instance is None:
        embeddings = get_embedding_model()
        persist_dir = settings.CHROMA_PERSIST_DIR
        if os.path.exists(persist_dir) and os.listdir(persist_dir):
            _vector_store_instance = Chroma(
                persist_directory=persist_dir,
                embedding_function=embeddings,
            )
        else:
            _vector_store_instance = initialize_kb()

    if _vector_store_instance is None:
        return []

    results = _vector_store_instance.similarity_search(query, k=k)
    return [doc.page_content for doc in results]
