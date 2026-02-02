import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database import Database
from locales import get_text
from keyboards import get_recommendation_keyboard, get_main_menu_keyboard
from services import TMDBService, AIService
from services.tmdb import TMDB_GENRE_IDS
from utils.helpers import format_movie_card, parse_list_from_json

router = Router()
logger = logging.getLogger(__name__)

tmdb_service = TMDBService()
ai_service = AIService()


def get_genre_ids_from_profile(genres: list[str]) -> list[int]:
    """Convert genre names to TMDB genre IDs."""
    ids = []
    for genre in genres:
        genre_key = genre.lower()
        if genre_key in TMDB_GENRE_IDS:
            ids.append(TMDB_GENRE_IDS[genre_key])
    return ids


async def generate_and_show_recommendation(
    message: Message,
    db: Database,
    user_id: int,
    session_id: int,
    dynamic_answers: dict,
    lang: str
):
    """Generate and display a movie recommendation."""
    # Get user's base profile
    base_profile = await db.get_base_profile(user_id)
    if not base_profile:
        await message.edit_text(get_text("error_occurred", lang))
        return

    # Parse JSON fields in base profile
    profile_dict = {
        "emotions_like": parse_list_from_json(base_profile.get("emotions_like")),
        "emotions_dislike": parse_list_from_json(base_profile.get("emotions_dislike")),
        "complexity": base_profile.get("complexity", "any"),
        "favorite_movies": base_profile.get("favorite_movies", ""),
        "disliked_movies": base_profile.get("disliked_movies", ""),
        "genres_like": parse_list_from_json(base_profile.get("genres_like")),
        "genres_dislike": parse_list_from_json(base_profile.get("genres_dislike")),
        "visual_style": base_profile.get("visual_style", "any"),
        "characters_like": parse_list_from_json(base_profile.get("characters_like")),
        "characters_dislike": parse_list_from_json(base_profile.get("characters_dislike")),
        "taboo": base_profile.get("taboo", ""),
        "afterfeel": parse_list_from_json(base_profile.get("afterfeel")),
    }

    # Get excluded movie IDs
    excluded_ids = await db.get_shown_movie_ids(user_id)

    tmdb_language = "uk-UA" if lang == "uk" else "en-US"
    movie_data = None

    # Try AI recommendations first
    try:
        recommendations = await ai_service.generate_recommendations(
            profile_dict,
            dynamic_answers,
            excluded_ids,
            count=5,
            lang=lang
        )

        if recommendations:
            # Find movie in TMDB
            for rec in recommendations:
                title = rec.get("title", "")
                year = rec.get("year")

                # Search in TMDB
                search_results = await tmdb_service.search_movie(title, tmdb_language)

                for result in search_results:
                    result_year = result.get("release_date", "")[:4]
                    if year and result_year and str(year) != result_year:
                        continue

                    tmdb_id = result.get("id")
                    if tmdb_id in excluded_ids:
                        continue

                    # Get full movie details
                    movie_data = await tmdb_service.get_movie_details(tmdb_id, tmdb_language)
                    if movie_data:
                        movie_data["ai_reason"] = rec.get("reason", "")
                        break

                if movie_data:
                    break

    except Exception as e:
        logger.error(f"AI recommendation failed: {e}")

    # Fallback: use TMDB discover based on user's preferred genres
    if not movie_data:
        logger.info("Using TMDB fallback for recommendations")
        genre_ids = get_genre_ids_from_profile(profile_dict.get("genres_like", []))

        if genre_ids:
            # Discover movies by user's genres
            discovered = await tmdb_service.discover_movies(
                genres=genre_ids[:3],  # Top 3 genres
                vote_average_min=6.5,
                language=tmdb_language
            )
        else:
            # Fallback to popular movies
            discovered = await tmdb_service.get_popular_movies(language=tmdb_language)

        for movie in discovered:
            if movie.get("id") not in excluded_ids:
                movie_data = await tmdb_service.get_movie_details(movie["id"], tmdb_language)
                if movie_data:
                    # Generate a simple reason based on mood
                    mood = dynamic_answers.get("mood", "")
                    mood_reasons = {
                        "happy": "Цей фільм підійде для гарного настрою!" if lang == "uk" else "This movie is great for a good mood!",
                        "sad": "Цей фільм допоможе відволіктися." if lang == "uk" else "This movie will help distract you.",
                        "stressed": "Розслабся і насолоджуйся переглядом." if lang == "uk" else "Relax and enjoy watching.",
                        "bored": "Цей фільм точно не дасть тобі нудьгувати!" if lang == "uk" else "This movie won't let you get bored!",
                        "romantic": "Ідеально для романтичного вечора." if lang == "uk" else "Perfect for a romantic evening.",
                        "adventurous": "Приготуйся до пригод!" if lang == "uk" else "Get ready for adventure!",
                        "thoughtful": "Цей фільм дасть тобі про що подумати." if lang == "uk" else "This movie will give you something to think about.",
                        "tired": "Легкий для перегляду після важкого дня." if lang == "uk" else "Easy to watch after a hard day.",
                    }
                    movie_data["ai_reason"] = mood_reasons.get(mood, "")
                    break

    if not movie_data:
        await message.edit_text(get_text("error_occurred", lang))
        return

    # Save recommendation to DB
    rec_id = await db.add_recommendation(
        session_id,
        movie_data["id"],
        movie_data["title"]
    )

    # Get trailer URL
    trailer_url = await tmdb_service.get_movie_trailer(movie_data["id"], tmdb_language)

    # Check if movie is saved
    is_saved = await db.is_movie_saved(user_id, movie_data["id"])

    # Format and send movie card
    card_text = format_movie_card(
        movie_data,
        reason=movie_data.get("ai_reason", ""),
        lang=lang
    )

    keyboard = get_recommendation_keyboard(
        lang,
        movie_data["id"],
        session_id,
        is_saved,
        trailer_url
    )

    # Send with poster if available
    if movie_data.get("poster_url"):
        try:
            await message.delete()
            await message.answer_photo(
                photo=movie_data["poster_url"],
                caption=f"{get_text('recommendation_title', lang)}\n\n{card_text}",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            # Fallback to text only
            try:
                await message.edit_text(
                    f"{get_text('recommendation_title', lang)}\n\n{card_text}",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            except Exception:
                await message.answer(
                    f"{get_text('recommendation_title', lang)}\n\n{card_text}",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
    else:
        try:
            await message.edit_text(
                f"{get_text('recommendation_title', lang)}\n\n{card_text}",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception:
            await message.answer(
                f"{get_text('recommendation_title', lang)}\n\n{card_text}",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )


@router.callback_query(F.data.startswith("rec:save:"))
async def save_movie(callback: CallbackQuery, db: Database):
    """Save movie to user's list."""
    parts = callback.data.split(":")
    tmdb_id = int(parts[2])
    session_id = int(parts[3])

    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uk"
    tmdb_language = "uk-UA" if lang == "uk" else "en-US"

    # Check if already saved
    if await db.is_movie_saved(callback.from_user.id, tmdb_id):
        await callback.answer(get_text("btn_saved_mark", lang))
        return

    # Get movie details
    movie_data = await tmdb_service.get_movie_details(tmdb_id, tmdb_language)
    if movie_data:
        await db.save_movie(
            callback.from_user.id,
            tmdb_id,
            movie_data["title"],
            movie_data.get("poster_url", "")
        )

        # Update keyboard to show "Saved"
        trailer_url = await tmdb_service.get_movie_trailer(tmdb_id, tmdb_language)
        new_keyboard = get_recommendation_keyboard(
            lang,
            tmdb_id,
            session_id,
            is_saved=True,
            trailer_url=trailer_url
        )

        try:
            await callback.message.edit_reply_markup(reply_markup=new_keyboard)
        except Exception:
            pass
        await callback.answer(get_text("movie_saved", lang))
    else:
        await callback.answer(get_text("error_occurred", lang))


@router.callback_query(F.data.startswith("rec:next:"))
async def next_recommendation(callback: CallbackQuery, db: Database):
    """Show next recommendation in current session."""
    session_id = int(callback.data.split(":")[2])

    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uk"

    # Get session data
    session = await db.get_session(session_id)
    if not session:
        await callback.answer(get_text("error_occurred", lang))
        return

    # Show loading
    try:
        await callback.message.delete()
    except Exception:
        pass

    loading_msg = await callback.message.answer(get_text("searching_movie", lang))

    # Generate new recommendation
    await generate_and_show_recommendation(
        loading_msg,
        db,
        callback.from_user.id,
        session_id,
        session["dynamic_answers"],
        lang
    )
    await callback.answer()


@router.callback_query(F.data == "rec:new_request")
async def new_request(callback: CallbackQuery, db: Database):
    """Start new dynamic survey for fresh recommendations."""
    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uk"

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        get_text("main_menu", lang),
        reply_markup=get_main_menu_keyboard(lang)
    )
    await callback.answer()
