from shopeasy.rag.loader import load_doc, SUPPORTED_FILES
from shopeasy.rag.vectorstore import create_vector_db, save_vector_db
from shopeasy.rag.splitter import split_docs
from pathlib import Path
def ingest_file(path: Path):

        
    print(f"Ingesting: {path}")

    docs = load_doc(path)
    print(f"Documents loaded: {len(docs)}")

    chunks = split_docs(docs)
    print(f"Chunks generated: {len(chunks)}")

    vector_db = create_vector_db(chunks)

    save_vector_db(vector_db)

    print("Ingestion completed successfully!")

    return vector_db


def ingest_dir(dir: Path):
    total = 0

    if not dir.exists():
        raise FileNotFoundError(f"Document directory does not exist: {dir}")
    if not dir.is_dir():
        raise NotADirectoryError(f"Document path is not a directory: {dir}")

    for path in sorted(dir.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_FILES:
            ingest_file(path)
            total += 1 
    return total




if __name__ == "__main__":
    p = Path("C:/serious-projects/shopeasy/data")
    ingest_dir(p)