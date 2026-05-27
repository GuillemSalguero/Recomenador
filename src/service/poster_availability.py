import requests
from src.service.extractTMDBiD import get_imdb_id_from_rt

TMDB_API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIxZWNiMzM0ZGExZTRhOGVlMWU1YjczMDQ1OWM4MGU5NSIsIm5iZiI6MTc2NDc4MTQxMS44MTksInN1YiI6IjY5MzA2ZDYzNmI1Y2YyMDNjOGEzZGQ5NSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.5SNczz7cghQ0sQhLl1nB35URInRO2oMOUFegYQp0qYY"


def get_poster(rt_url: str, year: str = None) -> str:
    print(f"\n🎬 Buscando poster para: {rt_url}")

    imdb_id = get_imdb_id_from_rt(rt_url, year=year)

    if not imdb_id:
        print("❌ No se encontró IMDB ID.")
        return None

    print(f"✅ IMDB ID obtenido: {imdb_id}")

    try:
        res = requests.get(
            f"https://api.themoviedb.org/3/find/{imdb_id}",
            headers={
                "Authorization": f"Bearer {TMDB_API_KEY}",
                "accept": "application/json"
            },
            params={
                "external_source": "imdb_id"
            },
            timeout=5
        )

        print(f"📡 Status Code TMDB: {res.status_code}")

        if res.status_code == 200:
            data = res.json()

            result = (
                data.get("movie_results", []) or
                data.get("tv_results", [])
            )

            if not result:
                print("⚠️ No se encontraron resultados.")
                return None

            poster_path = result[0].get("poster_path")

            if not poster_path:
                print("⚠️ No hay poster disponible.")
                return None

            poster_url = f"https://image.tmdb.org/t/p/original{poster_path}"

            print(f"🖼️ Poster encontrado: {poster_url}")

            return poster_url

        else:
            print(f"⚠️ Error TMDB: {res.text}")

    except Exception as e:
        print(f"💥 Excepción obteniendo poster: {e}")

    return None
