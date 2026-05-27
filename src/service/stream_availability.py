from fastapi import FastAPI
import requests
import re
from src.service.extractTMDBiD import get_imdb_id_from_rt

app = FastAPI()

RAPIDAPI_KEY = "b79fb37159msh4e4fe1f6c7c743dp1d199djsn0899c4280eb5"
TMDB_API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIxZWNiMzM0ZGExZTRhOGVlMWU1YjczMDQ1OWM4MGU5NSIsIm5iZiI6MTc2NDc4MTQxMS44MTksInN1YiI6IjY5MzA2ZDYzNmI1Y2YyMDNjOGEzZGQ5NSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.5SNczz7cghQ0sQhLl1nB35URInRO2oMOUFegYQp0qYY"


def get_plataformas(rt_url: str, pais: str = "es", year: str = None) -> list:
    print(f"\n🎬 Iniciando búsqueda de plataformas para: {rt_url}")
    imdb_id = get_imdb_id_from_rt(rt_url, year=year)
        
    if not imdb_id:
        print("❌ No se encontró IMDB ID. Cancelando búsqueda en RapidAPI.")
        return []
        
    print(f"✅ IMDB ID obtenido: {imdb_id}. Consultando RapidAPI para el país: '{pais}'...")
    try:
        res = requests.get(
            f"https://streaming-availability.p.rapidapi.com/shows/{imdb_id}",
            headers={
                "X-RapidAPI-Key": RAPIDAPI_KEY, # Asegúrate de que esta variable esté definida arriba
                "X-RapidAPI-Host": "streaming-availability.p.rapidapi.com"
            },
            params={"country": pais},
            timeout=5
        )
        
        print(f"📡 Status Code de RapidAPI: {res.status_code}")
        
        if res.status_code == 200:
            datos_json = res.json()
            
            # Navegamos directamente a las opciones del país
            opciones_pais = datos_json.get("streamingOptions", {}).get(pais, [])
            print(f"📦 Opciones en bruto encontradas en el JSON: {len(opciones_pais)}")
            
            plataformas = []
            nombres_vistos = set() # Para evitar duplicados
            
            for opcion in opciones_pais:
                nombre_servicio = opcion.get("service", {}).get("name")
                
                # Si encontramos el nombre y no lo hemos añadido ya a la lista
                if nombre_servicio and nombre_servicio not in nombres_vistos:
                    print(f"   📺 Plataforma detectada: {nombre_servicio}")
                    nombres_vistos.add(nombre_servicio)
                    
                    plataformas.append({
                        "nombre": nombre_servicio,
                        "tipo": opcion.get("type"),
                        "link": opcion.get("link")
                    })
                    
            print(f"✅ Lista final limpia devuelta: {[p['nombre'] for p in plataformas]}")
            return plataformas
        else:
            print(f"⚠️ La API no devolvió 200. Respuesta: {res.text}")
            
    except Exception as e:
        print(f"💥 Excepción procesando la búsqueda de plataformas: {e}")
        
    return []