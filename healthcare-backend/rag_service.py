import os
from typing import List

# Document Loaders & Splitters
from langchain_community.document_loaders import DirectoryLoader, TextLoader

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        from langchain_community.text_splitter import RecursiveCharacterTextSplitter

# Embeddings & Vector Stores
try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
except ImportError:
    from langchain_huggingface import HuggingFaceEmbeddings

try:
    from langchain_community.vectorstores import Chroma
except ImportError:
    from langchain_chroma import Chroma


# Configuration Constants
DATA_DIR = os.path.join(".", "data", "guidelines")
PERSIST_DIR = os.path.join(".", "data", "chroma_db")
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Module-level cached instances
_embedding_instance = None
_vector_store_instance = None


def get_embedding_model():
    """Returns or initializes the Hugging Face sentence transformer embedding model."""
    global _embedding_instance
    if _embedding_instance is None:
        _embedding_instance = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embedding_instance


def initialize_kb(data_dir: str = DATA_DIR, persist_dir: str = PERSIST_DIR) -> Chroma:
    """
    Reads text guidelines from data_dir, chunks the text using RecursiveCharacterTextSplitter,
    and populates a local persistent Chroma vector store using all-MiniLM-L6-v2.
    """
    global _vector_store_instance

    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        raise FileNotFoundError(f"Guidelines directory '{data_dir}' was empty/created. Please add guideline .txt files.")

    # 1. Load document text files from guidelines directory
    loader = DirectoryLoader(
        data_dir,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    documents = loader.load()

    if not documents:
        print(f"Warning: No .txt documents found in '{data_dir}'.")
        return None

    # 2. Chunk text using RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Loaded {len(documents)} document(s) and split into {len(chunks)} chunks.")

    # 3. Create persistent vector store using Chroma & all-MiniLM-L6-v2 embeddings
    embeddings = get_embedding_model()

    _vector_store_instance = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir,
    )
    
    print(f"Knowledge base successfully initialized and persisted to '{persist_dir}'.")
    return _vector_store_instance


def get_relevant_context(query: str, k: int = 3, persist_dir: str = PERSIST_DIR) -> List[str]:
    """
    Searches the vector store for the query and returns top k (default 3) relevant context chunks.
    """
    global _vector_store_instance

    if _vector_store_instance is None:
        embeddings = get_embedding_model()
        if os.path.exists(persist_dir) and os.listdir(persist_dir):
            _vector_store_instance = Chroma(
                persist_directory=persist_dir,
                embedding_function=embeddings,
            )
        else:
            # If database doesn't exist yet, initialize it
            _vector_store_instance = initialize_kb(persist_dir=persist_dir)

    if _vector_store_instance is None:
        return []

    # Search for top 3 relevant chunks
    results = _vector_store_instance.similarity_search(query, k=k)
    return [doc.page_content for doc in results]


if __name__ == "__main__":
    print("--- Initializing Knowledge Base ---")
    initialize_kb()
    
    sample_query = "What should I do if a patient has a severe thunderclap headache with a stiff neck?"
    print(f"\n--- Testing Query: '{sample_query}' ---")
    context_chunks = get_relevant_context(sample_query, k=3)
    for i, chunk in enumerate(context_chunks, 1):
        print(f"\n[Chunk {i}]\n{chunk}")
