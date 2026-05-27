import json
import re
from langchain_ollama import OllamaLLM
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from langchain_core.documents import Document
from src.clients.chroma_client import get_vectorstore
from typing import List, Any
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun, AsyncCallbackManagerForRetrieverRun
from langchain_groq import ChatGroq
from src.config import settings

vectorstore = get_vectorstore()
#llama-3.3-70b-versatile
llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0, api_key=settings.GROQ_API_KEY)
'''
Aquest implementa el self_query 
'''
# --- Nuestro extractor blindado con Regex ---
def extract_filters(query: str) -> dict:
    prompt = f"""
    Extract filters from this query: "{query}"
    
    Return ONLY a JSON with this exact format:
    {{
        "year_gte": 1980, 
        "year_lte": 1989, 
        "genre": "Science Fiction", 
        "search_text": "artificial intelligence robots"
    }}
    If there is no year or genre, use null. Do NOT write anything else.
    """
    try:
        response = llm.invoke(prompt)

        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        
        # Default fallback if no JSON is found
        return {"search_text": query, "year_gte": None, "year_lte": None, "genre": None}
    except Exception as e:
        print(f"Filter error: {e}")
        return {"search_text": query, "year_gte": None, "year_lte": None, "genre": None}

class CustomFilterRetriever(BaseRetriever):
    vectorstore: Any
    k: int = 10

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        
        if "Here are" in query or "Here is" in query or "versions" in query:
            return []

        filters_dict = extract_filters(query)
        search_text = filters_dict.get("search_text", query)
        
        where_clause = {}
        conditions = []
        
        if filters_dict.get("year_gte"):
            conditions.append({"year": {"$gte": int(filters_dict["year_gte"])}})
        if filters_dict.get("year_lte"):
            conditions.append({"year": {"$lte": int(filters_dict["year_lte"])}})
            
        if filters_dict.get("genre"):
            search_text = f"{filters_dict['genre']} {search_text}"
            
        if len(conditions) == 1:
            where_clause = conditions[0]
        elif len(conditions) > 1:
            where_clause = {"$and": conditions}
            
        #print(f" Buscando en BD: '{search_text}' | Filtros estables: {where_clause}")
        
        try:
            if where_clause:
                return self.vectorstore.similarity_search(search_text, k=self.k, filter=where_clause)
            else:
                return self.vectorstore.similarity_search(search_text, k=self.k)
        except Exception as e:
            print(f"⚠️ Error en Chroma: {e}")
            return self.vectorstore.similarity_search(query, k=self.k)

    async def _aget_relevant_documents(
        self, query: str, *, run_manager: AsyncCallbackManagerForRetrieverRun
    ) -> List[Document]:
        return self._get_relevant_documents(query, run_manager=None)


def retrieve_combined(query: str, top_k: int) -> dict:
    
    # Inicialitza el recuperador personalitzat que aplica els filtres extrets
    custom_retriever = CustomFilterRetriever(
        vectorstore=vectorstore,
        k=top_k
    )

    # Genera múltiples variants de la consulta per millorar la precisió de la cerca
    combined_retriever = MultiQueryRetriever.from_llm(
        retriever=custom_retriever,
        llm=llm,
    )
    
    results = combined_retriever.invoke(query)

    seen = set()
    documents = []
    metadatas = []
    distances = []

    for doc in results:
        # Elimina duplicats basant-se en el contingut del text
        if doc.page_content not in seen:
            seen.add(doc.page_content)
            documents.append(doc.page_content)
            metadatas.append(doc.metadata)
            distances.append(0.0)# Valor per defecte ja que MultiQuery no sempre retorna distàncies
        
        # Limita els resultats al valor top_k definit
        if len(documents) >= top_k:
            break

    return {
        "documents": [documents],
        "metadatas": [metadatas],
        "distances": [distances]
    }