import logging
from langchain_core.prompts import PromptTemplate
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from langchain_groq import ChatGroq
from src.clients.chroma_client import get_vectorstore
from src.config import settings

logging.basicConfig()
logging.getLogger("langchain_classic.retrievers.multi_query").setLevel(logging.INFO)

vectorstore = get_vectorstore()

llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0, api_key=settings.GROQ_API_KEY)


QUERY_PROMPT = PromptTemplate(
    input_variables=["question"],
    template="""You are an AI language model assistant. Your task is to generate five
    different versions of the given user question to retrieve relevant documents from a vector
    database. By generating multiple perspectives on the user query, your goal is to help
    the user overcome some of the limitations of the distance-based similarity search.
    Provide these alternative questions separated by newlines.
    
    Original question: {question}
    
    Output (at least 4 lines):""",
)

retriever = MultiQueryRetriever.from_llm(
    retriever=vectorstore.as_retriever(search_kwargs={"k": 10}),
    llm=llm,
    prompt=QUERY_PROMPT
)

def retrieve_multiquery(query: str, top_k: int) -> dict:
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