import httpx
from typing import Optional
from config import TMDB_API_KEY, TMDB_BASE_URL, TMDB_IMAGE_BASE_URL


class TMDBService:
    def __init__(self):
        self.api_key = TMDB_API_KEY
        self.base_url = TMDB_BASE_URL
        self.image_base_url = TMDB_IMAGE_BASE_URL

    async def _request(self, endpoint: str, params: dict = None) -> dict:
        if params is None:
            params = {}
        params["api_key"] = self.api_key

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{endpoint}",
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def search_movie(self, title: str, language: str = "uk-UA") -> list[dict]:
        """Search for movies by title."""
        data = await self._request(
            "/search/movie",
            {"query": title, "language": language}
        )
        return data.get("results", [])

    async def get_movie_details(self, tmdb_id: int, language: str = "uk-UA") -> Optional[dict]:
        """Get detailed movie information."""
        try:
            data = await self._request(
                f"/movie/{tmdb_id}",
                {"language": language, "append_to_response": "credits"}
            )

            return {
                "id": data.get("id"),
                "title": data.get("title"),
                "original_title": data.get("original_title"),
                "overview": data.get("overview"),
                "release_date": data.get("release_date"),
                "year": data.get("release_date", "")[:4] if data.get("release_date") else None,
                "runtime": data.get("runtime"),
                "vote_average": round(data.get("vote_average", 0), 1),
                "poster_path": data.get("poster_path"),
                "poster_url": f"{self.image_base_url}{data.get('poster_path')}" if data.get("poster_path") else None,
                "genres": [g["name"] for g in data.get("genres", [])],
                "tagline": data.get("tagline"),
                "budget": data.get("budget"),
                "revenue": data.get("revenue"),
                "production_countries": [c["name"] for c in data.get("production_countries", [])],
                "directors": [
                    c["name"] for c in data.get("credits", {}).get("crew", [])
                    if c.get("job") == "Director"
                ],
                "cast": [
                    c["name"] for c in data.get("credits", {}).get("cast", [])[:5]
                ],
            }
        except Exception:
            return None

    async def get_movie_trailer(self, tmdb_id: int, language: str = "uk-UA") -> Optional[str]:
        """Get YouTube trailer URL for a movie."""
        try:
            # Try Ukrainian first
            data = await self._request(
                f"/movie/{tmdb_id}/videos",
                {"language": language}
            )
            videos = data.get("results", [])

            # If no Ukrainian videos, try English
            if not videos and language != "en-US":
                data = await self._request(
                    f"/movie/{tmdb_id}/videos",
                    {"language": "en-US"}
                )
                videos = data.get("results", [])

            # Find trailer
            for video in videos:
                if video.get("type") == "Trailer" and video.get("site") == "YouTube":
                    return f"https://www.youtube.com/watch?v={video.get('key')}"

            # Fallback to any YouTube video
            for video in videos:
                if video.get("site") == "YouTube":
                    return f"https://www.youtube.com/watch?v={video.get('key')}"

            return None
        except Exception:
            return None

    async def discover_movies(
        self,
        genres: list[int] = None,
        year_from: int = None,
        year_to: int = None,
        vote_average_min: float = None,
        sort_by: str = "popularity.desc",
        page: int = 1,
        language: str = "uk-UA"
    ) -> list[dict]:
        """Discover movies by various filters."""
        params = {
            "language": language,
            "sort_by": sort_by,
            "page": page,
            "include_adult": False
        }

        if genres:
            params["with_genres"] = ",".join(map(str, genres))
        if year_from:
            params["primary_release_date.gte"] = f"{year_from}-01-01"
        if year_to:
            params["primary_release_date.lte"] = f"{year_to}-12-31"
        if vote_average_min:
            params["vote_average.gte"] = vote_average_min

        data = await self._request("/discover/movie", params)
        return data.get("results", [])

    async def get_popular_movies(self, page: int = 1, language: str = "uk-UA") -> list[dict]:
        """Get popular movies."""
        data = await self._request(
            "/movie/popular",
            {"language": language, "page": page}
        )
        return data.get("results", [])

    async def get_genre_list(self, language: str = "uk-UA") -> dict[int, str]:
        """Get mapping of genre IDs to names."""
        data = await self._request(
            "/genre/movie/list",
            {"language": language}
        )
        return {g["id"]: g["name"] for g in data.get("genres", [])}


# Genre ID mapping for TMDB
TMDB_GENRE_IDS = {
    "action": 28,
    "adventure": 12,
    "animation": 16,
    "comedy": 35,
    "crime": 80,
    "documentary": 99,
    "drama": 18,
    "family": 10751,
    "fantasy": 14,
    "history": 36,
    "horror": 27,
    "music": 10402,
    "mystery": 9648,
    "romance": 10749,
    "scifi": 878,
    "thriller": 53,
    "war": 10752,
    "western": 37,
}
