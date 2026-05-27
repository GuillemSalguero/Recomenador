from typing import List, Any
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from src.clients.chroma_client import get_vectorstore
from src.service.retrieval import retriever as self_query_retriever

vectorstore = get_vectorstore()

def retrieve_parent(query: str, top_k: int) -> dict:
#    print(f"\n--- 🚀 INICIANDO PARENT RETRIEVAL ---")
#    print(f"🔍 Consulta: '{query}'")
    
    child_k = top_k * 4
    p_k = 8

    # 1. Fase de Obtención de Fragmentos (Hijos)
    try:
        self_query_retriever.search_kwargs = {"k": child_k}
        child_docs = self_query_retriever.invoke(query)
        
        # Búsqueda de respaldo para evitar pérdida de palabras clave
        backup_docs = vectorstore.similarity_search(query, k=20)
        child_docs.extend(backup_docs)
        
#        print(f" Fase 1: Recuperados {len(child_docs)} fragmentos (SelfQuery + Similitud)")
    except Exception as e:
#        print(f"⚠️ Fase 1: Fallo en SelfQuery ({e}). Usando solo similitud básica")
        child_docs = vectorstore.similarity_search(query, k=child_k)

    if not child_docs:
        print(" No se encontraron fragmentos.")
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    # 2. Fase de Agrupación por Entidad (Agregación)
    # Usamos un diccionario para rastrear cuántos fragmentos aporta cada película
    stats = {}
    parent_links = []
    seen = set()
    
    for doc in child_docs:
        link = doc.metadata.get("link")
        if link:
            stats[link] = stats.get(link, 0) + 1
            if link not in seen:
                seen.add(link)
                parent_links.append(link)

#    print(f" Fase 2: Identificadas {len(parent_links)} películas candidatas.")
    # Log de las 3 primeras candidatas para ver la distribución
#    for link in parent_links[:3]:
#       print(f"   - [Candidata] {link}: {stats[link]} fragmentos encontrados")

    # 3. Fase de Reconstrucción del Contexto (Consolidación)
#    print(f"  Fase 3: Reconstruyendo context superior (Parent Documents)...")
    parent_documents = []
    
    for link in parent_links:
        # Recuperamos la "familia" completa de fragmentos para esta entidad
        family_docs = vectorstore.similarity_search_with_score(
            query, k=p_k, filter={"link": link}
        )
        if not family_docs:
            continue

        best_score = family_docs[0][1]
        
        # Concatenación de fragmentos para formar el documento padre
        combined_text = f"--- Reseñas combinadas de la película ({link}) --- \n"
        combined_text += "\n".join(f"- {doc.page_content}" for doc, _ in family_docs)

        parent_doc = Document(
            page_content=combined_text,
            metadata={**family_docs[0][0].metadata, "best_score": best_score}
        )
        parent_documents.append((parent_doc, best_score))

    # 4. Ordenación y Selección Final
    # El score de distancia más bajo indica mayor relevancia
    parent_documents.sort(key=lambda x: x[1])
    final = parent_documents[:top_k]

#    print(f"🏆 Fase 4: Selección final finalizada.")
#    for i, (doc, score) in enumerate(final[:5], 1): # Log de los top 5
#        print(f"   {i}. {doc.metadata.get('link')} | Score Relevancia: {score:.4f}")
#
#    print(f"--- PROCESO FINALIZADO ---\n")

    return {
        "documents": [[doc.page_content for doc, _ in final]],
        "metadatas": [[doc.metadata for doc, _ in final]],
        "distances": [[score for _, score in final]]
    }