from pathlib import Path
from langchain_community.document_loaders import TextLoader

SUPPORTED_FILES = {".txt", ".md"}



def load_doc(path: Path):

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"{path} file does not exist")

    if not path.is_file():
        raise ValueError(f"Expected a file: {path}")

    if path.suffix.lower() not in SUPPORTED_FILES:
        raise ValueError(f"Unsupported file format: {path.suffix}")

    loader = TextLoader(str(path), encoding= "utf-8")
    docs = loader.load()

    for doc in docs:
        doc.metadata.setdefault("source", str(path.resolve()))
        doc.metadata.setdefault("title", path.stem)
        doc.metadata["document_name"] = path.name

    return docs