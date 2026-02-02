import json
from typing import Optional
from locales import get_text


def format_movie_card(
    movie: dict,
    reason: str = "",
    lang: str = "uk"
) -> str:
    """Format movie details into a nice text card."""
    lines = []

    title = movie.get("title", "Unknown")
    original_title = movie.get("original_title", "")

    # Title with original if different
    if original_title and original_title != title:
        lines.append(f"*{title}*\n_{original_title}_")
    else:
        lines.append(f"*{title}*")

    lines.append("")

    # Year and rating
    info_parts = []
    if movie.get("year"):
        info_parts.append(f"{get_text('movie_year', lang)}: {movie['year']}")
    if movie.get("vote_average"):
        info_parts.append(f"{get_text('movie_rating', lang)}: {movie['vote_average']}/10")
    if movie.get("runtime"):
        info_parts.append(f"{get_text('movie_duration', lang)}: {movie['runtime']} {get_text('minutes', lang)}")

    if info_parts:
        lines.append(" | ".join(info_parts))

    # Genres
    if movie.get("genres"):
        genres_str = ", ".join(movie["genres"][:4])
        lines.append(f"{get_text('movie_genres', lang)}: {genres_str}")

    # Directors
    if movie.get("directors"):
        directors_str = ", ".join(movie["directors"][:2])
        lines.append(f"Режисер: {directors_str}" if lang == "uk" else f"Director: {directors_str}")

    # Cast
    if movie.get("cast"):
        cast_str = ", ".join(movie["cast"][:3])
        lines.append(f"Актори: {cast_str}" if lang == "uk" else f"Cast: {cast_str}")

    lines.append("")

    # Overview
    if movie.get("overview"):
        overview = movie["overview"]
        if len(overview) > 400:
            overview = overview[:397] + "..."
        lines.append(overview)

    # Reason
    if reason:
        lines.append("")
        lines.append(f"_{get_text('why_recommend', lang)}: {reason}_")

    return "\n".join(lines)


def parse_list_from_json(value: Optional[str]) -> list:
    """Parse a JSON string into a list, or return empty list."""
    if not value:
        return []
    try:
        result = json.loads(value)
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def escape_markdown(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text
