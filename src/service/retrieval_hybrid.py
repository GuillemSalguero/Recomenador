from typing import List, Any
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from src.clients.chroma_client import get_vectorstore

vectorstore = get_vectorstore()


def reciprocal_rank_fusion(doc_lists, weights, c=60):
    rrf_scores = {}
    doc_map = {}

    for docs, weight in zip(doc_lists, weights):
        if not docs:
            continue
        for rank, doc in enumerate(docs, start=1):
            doc_id = f"{doc.metadata.get('title','')}_{doc.metadata.get('year','')}"

            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = 0.0
                doc_map[doc_id] = doc

            rrf_scores[doc_id] += weight / (rank + c)

    sorted_docs = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    return [doc_map[doc_id] for doc_id in sorted_docs]


def retrieve_hybrid(query: str, top_k: int) -> dict:
    try:
        candidates = vectorstore.similarity_search(query, k=200)

        if not candidates:
            return {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]]
            }

        clean_docs = [
            Document(
                page_content=doc.page_content,
                metadata=doc.metadata
            )
            for doc in candidates if doc.page_content
        ]

        bm25_retriever = BM25Retriever.from_documents(clean_docs)
        bm25_retriever.preprocess_func = lambda x: x.lower().split()

        bm25_retriever.k = top_k * 2  
        bm25_results = bm25_retriever.invoke(query) or []

        vector_ret = vectorstore.as_retriever(search_kwargs={"k": top_k})
        vector_results = vector_ret.invoke(query) or []

        fused_docs = reciprocal_rank_fusion(
            [bm25_results, vector_results],
            weights=[0.3, 0.7]
        )

        documents = []
        metadatas = []
        distances = []
        seen = set()

        for doc in fused_docs:
            doc_id = f"{doc.metadata.get('title','')}_{doc.metadata.get('year','')}"

            if doc_id not in seen:
                seen.add(doc_id)
                documents.append(doc.page_content)
                metadatas.append(doc.metadata)
                distances.append(0.0)

            if len(documents) >= top_k:
                break

        return {
            "documents": [documents],
            "metadatas": [metadatas],
            "distances": [distances]
        }

    except Exception as e:
        print(f" Error en retrieve_hybrid: {e}")
        return {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }
