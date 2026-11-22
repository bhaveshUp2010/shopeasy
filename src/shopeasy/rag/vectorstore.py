from langchain_community.vectorstores import FAISS
from shopeasy.rag.embeddings import get_embeddings
from pathlib import Path

INDEX_PATH = Path(__file__).resolve().parent.parent.parent / "faiss-index"

def create_vector_db(chunks):
    if not chunks:
        raise ValueError("chunks are needed to make vector db")
    embeddings = get_embeddings()

    vector_db = FAISS.from_documents(
        chunks,
        embeddings
    )
    return vector_db


def save_vector_db(vector_db):
    INDEX_PATH.mkdir(parents= True, exist_ok=True)
    vector_db.save_local(str(INDEX_PATH))

def get_vector_store():

    if not INDEX_PATH.exists():
        raise FileNotFoundError("FAISS index does not exist. Ingest documents first.")

    embeddings = get_embeddings()

    return FAISS.load_local(
        str(INDEX_PATH),
        embeddings,
        allow_dangerous_deserialization=True
    )

def get_retriever():

    vector_db = get_vector_store()

    return vector_db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}
    )