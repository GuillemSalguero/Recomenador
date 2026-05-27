from supabase import create_client
from src.config import settings

class MovieMeta:
    def __init__(self):
        self.sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

    def get_movie_meta(self, link: str):
        try : 
            res = self.sb.table("Movies").select(
                "movie_title, original_release_date, genres, directors, runtime, tomatometer_rating, tomatometer_count"
            ).eq("rotten_tomatoes_link", link).limit(1).execute()
            return res.data[0] if res.data else {}
        except Exception as e :
            print("Error fetching movie metadata:", e)
            return {}
        