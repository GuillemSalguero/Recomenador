import httpx
from collections import defaultdict
from typing import Dict, List

def augment_results(chroma_res: Dict, max_results=5, max_runtime=None, auth=None) -> List[Dict]:
    user_watchlist = []
    user_fav_directors = []

    print(Dict)
    
    # 1. Recuperación de datos de usuario (Watchlist y Directores)
    if auth:
        headers = {"Authorization": f"Bearer {auth}"}
        try:
            print("🔐 Recuperando datos de usuario para personalización...")
            with httpx.Client(timeout=1.2) as client:
                # Obtener Watchlist
                resp_wl = client.get("http://localhost:8083/api/movies/watchlist", headers=headers)
                if resp_wl.status_code == 200:
                    data_wl = resp_wl.json()
                    user_watchlist = [
                        item if isinstance(item, str) else item.get("movieLink") 
                        for item in (data_wl if isinstance(data_wl, list) else [])
                    ]
                
                # Obtener Directores Favoritos
                resp_dir = client.get("http://localhost:8083/api/directors/favorites", headers=headers)
                if resp_dir.status_code == 200:
                    data_dir = resp_dir.json()
                    user_fav_directors = data_dir.get("directors") if isinstance(data_dir, dict) else []

            print(f"✅ Datos de usuario recuperados: {len(user_watchlist)} en Watchlist, {len(user_fav_directors)} directores favoritos.")
        except Exception as e:
            print("error ", e)
            pass # Si falla, continuamos con listas vacías

    # ... extracción de metadatos de Chroma ...
    docs, metas, dists = chroma_res["documents"][0], chroma_res["metadatas"][0], chroma_res["distances"][0]
    
    items = []
    for doc, meta, dist in zip(docs, metas, dists):
        items.append({"link": meta.get("link", ""), "sim": float(1 - dist), "snippet": doc[:300], "meta": meta})

    grouped = defaultdict(list)
    for it in items:
        grouped[it["link"]].append(it)

    enriched = []

    
    WATCHLIST_BONUS = 0.25
    DIRECTOR_BONUS = 0.20

    for link, lst in grouped.items():
        sim_avg = sum(x["sim"] for x in lst) / len(lst)
        m = lst[0]["meta"]
        
        # --- Cálculo de Score Base ---
        tomatometer = m.get("tomatometer") or 0
        score = (0.7 * sim_avg) + (0.3 * (tomatometer / 100.0))
        
        # Penalización por Runtime
        runtime = m.get("runtime")
        if max_runtime and runtime and runtime > max_runtime:
            score -= 0.1

        # --- Bonus 1: Watchlist ---
        is_in_watchlist = link in user_watchlist
        if is_in_watchlist:
            print(f"⭐ Aplicando BONUS Watchlist a: {link}")
            score += WATCHLIST_BONUS

        # --- Bonus 2: Directores Favoritos ---
        # Asumiendo que m.get("directors") es una lista o string
        movie_directors = m.get("directors") or []
        if isinstance(movie_directors, str):
            movie_directors = [d.strip() for d in movie_directors.split(",")]
        
        # Si hay coincidencia entre directores de la película y favoritos del usuario
        has_fav_director = any(d in user_fav_directors for d in movie_directors)
        if has_fav_director:
            print(f"Aplicando BONUS Director a: {link} (Director favorito detectado)")
            score += DIRECTOR_BONUS


        # --- Carga de Assets ---
        streaming = []#get_plataformas(link, "es")
        poster = "" #get_poster(link)
        try :
            with httpx.Client(timeout=1.2) as client:
                response = client.post(
                    "http://localhost:8083/api/movies/detail",
                    json={"id": link}
                )

                if response.status_code == 200:
                    poster = response.json().get("posterUrl", "")
        except Exception as e:
            pass
        
        movie_directors = m.get("directors") or []

        if isinstance(movie_directors, str):
            movie_directors = [d.strip() for d in movie_directors.split(",")]

        movie_directors = [d.strip() for d in movie_directors if d]

        enriched.append({
            "link": link,
            "score": score,
            "sim_avg": sim_avg,
            "title": m.get("movie_title") or link,
            "year": str(m.get("year", ""))[:4],
            "genres": m.get("genres"),
            "directors": movie_directors,
            "runtime": runtime,
            "tomatometer": tomatometer,
            "tomatometer_count": None,
            "snippets": [x["snippet"] for x in sorted(lst, key=lambda z: z["sim"], reverse=True)[:2]],
            "streaming_availability": streaming,
            "posterUrl": poster,
            "is_in_watchlist": is_in_watchlist,
            "has_fav_director": has_fav_director
        })

    enriched.sort(key=lambda x: x["score"], reverse=True)
    return enriched[:max_results]