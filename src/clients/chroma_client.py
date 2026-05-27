import chromadb
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from src.config import settings

embeddings = HuggingFaceEmbeddings(model_name="paraphrase-multilingual-MiniLM-L12-v2")

def get_vectorstore() -> Chroma:
    return Chroma(
        collection_name="reviews",
        embedding_function=embeddings,
        persist_directory=settings.CHROMA_PATH,
    )