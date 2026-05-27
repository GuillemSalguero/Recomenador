from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM
from langchain_classic.retrievers.self_query.base import SelfQueryRetriever
from langchain_classic.chains.query_constructor.base import AttributeInfo, load_query_constructor_runnable
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from src.clients.chroma_client import get_vectorstore
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_groq import ChatGroq
from src.config import settings

# --- Metadatos ---
metadata_field_info = [
    AttributeInfo(
        name="genres",
        description="Movie genres. Examples: 'Science Fiction & Fantasy', 'Drama', 'Action & Adventure', 'Comedy', 'Horror', 'Romance'",
        type="string",
    ),
    AttributeInfo(
        name="year",
        description="Release year of the movie as an integer. Example: 1994, 2010, 2023",
        type="integer",
    ),
    AttributeInfo(
        name="directors",
        description="Name of the movie director(s). Example: 'Christopher Nolan'",
        type="string",
    ),
    AttributeInfo(
        name="runtime",
        description="Movie duration in minutes as an integer. Example: 120",
        type="integer",
    ),
    AttributeInfo(
        name="tomatometer",
        description="Critics score on Rotten Tomatoes from 0 to 100. Example: 85",
        type="float",
    ),
]

examples = [
    {
        "i": "1",
        "data_source": "Rotten Tomatoes movie critic reviews",
        "user_query": "80s horror movies",
        "structured_request": '{{\n    "query": "horror suspense terror",\n    "filter": "and(eq(\\"genres\\", \\"Horror\\"), gte(\\"year\\", 1980), lt(\\"year\\", 1990))"\n}}'
    },
    {
        "i": "2",
        "data_source": "Rotten Tomatoes movie critic reviews",
        "user_query": "80s science fiction about artificial intelligence",
        "structured_request": '{{\n    "query": "artificial intelligence robots future",\n    "filter": "and(eq(\\"genres\\", \\"Science Fiction & Fantasy\\"), gte(\\"year\\", 1980), lt(\\"year\\", 1990))"\n}}'
    },
    {
        "i": "3",
        "data_source": "Rotten Tomatoes movie critic reviews",
        "user_query": "well-rated romantic dramas",
        "structured_request": '{{\n    "query": "romance love relationship drama",\n    "filter": "and(eq(\\"genres\\", \\"Romance\\"), gte(\\"tomatometer\\", 80))"\n}}'
    },
    {
        "i": "4",
        "data_source": "Rotten Tomatoes movie critic reviews",
        "user_query": "short action movies",
        "structured_request": '{{\n    "query": "action adventure fight",\n    "filter": "and(eq(\\"genres\\", \\"Action & Adventure\\"), lt(\\"runtime\\", 100))"\n}}'
    },
]
#llama-3.1-8b-instant""llama-3.3-70b-versatile"
llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0, api_key=settings.GROQ_API_KEY)

vectorstore = get_vectorstore()

query_constructor = load_query_constructor_runnable(
    llm=llm,
    document_contents="Reseñas de críticos de cine de Rotten Tomatoes",
    attribute_info=metadata_field_info,
    examples=examples,
)

retriever = SelfQueryRetriever(
    query_constructor=query_constructor,
    vectorstore=vectorstore,
    verbose=True,
    enable_limit=True,
)

def retrieve(query: str, top_k: int) -> dict:
    retriever.search_kwargs = {"k": top_k}
    try:
        results = retriever.invoke(query)
    except Exception:
        results = vectorstore.similarity_search(query, k=top_k)

    documents = []
    metadatas = []
    distances = []

    for doc in results:
        documents.append(doc.page_content)
        metadatas.append(doc.metadata)
        distances.append(0.0)

    return {
        "documents": [documents],
        "metadatas": [metadatas],
        "distances": [distances]
    }

vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 20})

def build_hybrid_retriever(docs, top_k: int):
    """
    Construye el retriever híbrido combinando BM25 + vectores.
    BM25 necesita los documentos en memoria.
    """
    bm25_retriever = BM25Retriever.from_documents(docs)
    bm25_retriever.k = top_k

    vector_ret = vectorstore.as_retriever(search_kwargs={"k": top_k})

    ensemble = EnsembleRetriever(
        retrievers=[bm25_retriever, vector_ret],
        weights=[0.5, 0.5]  
    )
    return ensemble

def retrieve_hybrid(query: str, top_k: int) -> dict:
    candidates = vectorstore.similarity_search(query, k=200)

    retriever = build_hybrid_retriever(candidates, top_k)
    results = retriever.invoke(query)

    documents = []
    metadatas = []
    distances = []

    for doc in results[:top_k]:
        documents.append(doc.page_content)
        metadatas.append(doc.metadata)
        distances.append(0.0)

    return {
        "documents": [documents],
        "metadatas": [metadatas],
        "distances": [distances]
    }