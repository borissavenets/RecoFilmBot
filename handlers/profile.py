from aiogram import Router
from aiogram.types import CallbackQuery

from database import Database
from locales import get_text
from keyboards import get_back_keyboard
from utils.helpers import parse_list_from_json

router = Router()


async def show_user_profile(callback: CallbackQuery, db: Database):
    """Display user's profile information."""
    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uk"

    profile = await db.get_base_profile(callback.from_user.id)

    if not profile:
        await callback.message.edit_text(
            get_text("error_occurred", lang),
            reply_markup=get_back_keyboard(lang)
        )
        await callback.answer()
        return

    # Build profile text
    lines = [f"*{get_text('your_profile', lang)}*", ""]

    # Emotions like
    emotions_like = parse_list_from_json(profile.get("emotions_like"))
    if emotions_like:
        emo_texts = [get_text(f"emo_{e}", lang) for e in emotions_like]
        lines.append(f"*{get_text('profile_emotions_like', lang)}:*")
        lines.append(", ".join(emo_texts))
        lines.append("")

    # Emotions dislike
    emotions_dislike = parse_list_from_json(profile.get("emotions_dislike"))
    if emotions_dislike:
        emo_texts = [get_text(f"emo_{e}", lang) for e in emotions_dislike]
        lines.append(f"*{get_text('profile_emotions_dislike', lang)}:*")
        lines.append(", ".join(emo_texts))
        lines.append("")

    # Complexity
    complexity = profile.get("complexity")
    if complexity:
        lines.append(f"*{get_text('profile_complexity', lang)}:*")
        lines.append(get_text(f"complexity_{complexity}", lang))
        lines.append("")

    # Favorite movies
    favorite = profile.get("favorite_movies")
    if favorite:
        lines.append(f"*{get_text('profile_favorite_movies', lang)}:*")
        lines.append(favorite)
        lines.append("")

    # Genres like
    genres_like = parse_list_from_json(profile.get("genres_like"))
    if genres_like:
        genre_texts = [get_text(f"genre_{g}", lang) for g in genres_like]
        lines.append(f"*{get_text('profile_genres_like', lang)}:*")
        lines.append(", ".join(genre_texts))
        lines.append("")

    # Genres dislike
    genres_dislike = parse_list_from_json(profile.get("genres_dislike"))
    if genres_dislike:
        genre_texts = [get_text(f"genre_{g}", lang) for g in genres_dislike]
        lines.append(f"*{get_text('profile_genres_dislike', lang)}:*")
        lines.append(", ".join(genre_texts))
        lines.append("")

    # Visual style
    visual = profile.get("visual_style")
    if visual:
        lines.append(f"*{get_text('profile_visual', lang)}:*")
        lines.append(get_text(f"visual_{visual}", lang))
        lines.append("")

    # Characters like
    chars_like = parse_list_from_json(profile.get("characters_like"))
    if chars_like:
        char_texts = [get_text(f"char_{c}", lang) for c in chars_like]
        lines.append(f"*{get_text('profile_characters_like', lang)}:*")
        lines.append(", ".join(char_texts))
        lines.append("")

    # Taboo
    taboo = profile.get("taboo")
    if taboo:
        lines.append(f"*{get_text('profile_taboo', lang)}:*")
        lines.append(taboo)
        lines.append("")

    # Afterfeel
    afterfeel = parse_list_from_json(profile.get("afterfeel"))
    if afterfeel:
        after_texts = [get_text(f"after_{a}", lang) for a in afterfeel]
        lines.append(f"*{get_text('profile_afterfeel', lang)}:*")
        lines.append(", ".join(after_texts))

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=get_back_keyboard(lang),
        parse_mode="Markdown"
    )
    await callback.answer()
