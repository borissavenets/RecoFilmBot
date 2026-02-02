from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import Database
from locales import get_text
from keyboards import get_saved_movies_keyboard, get_back_keyboard
from services import TMDBService
from utils.helpers import format_movie_card

router = Router()

tmdb_service = TMDBService()


async def show_saved_movies(callback: CallbackQuery, db: Database, page: int = 0):
    """Display user's saved movies."""
    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uk"

    movies = await db.get_saved_movies(callback.from_user.id)

    if not movies:
        await callback.message.edit_text(
            get_text("no_saved_movies", lang),
            reply_markup=get_back_keyboard(lang)
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        get_text("saved_movies_title", lang),
        reply_markup=get_saved_movies_keyboard(movies, lang, page)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("saved:page:"))
async def paginate_saved(callback: CallbackQuery, db: Database):
    """Handle pagination of saved movies."""
    page = int(callback.data.split(":")[2])
    await show_saved_movies(callback, db, page)


@router.callback_query(F.data.startswith("saved:view:"))
async def view_saved_movie(callback: CallbackQuery, db: Database):
    """View details of a saved movie."""
    tmdb_id = int(callback.data.split(":")[2])

    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uk"
    tmdb_language = "uk-UA" if lang == "uk" else "en-US"

    # Get movie details from TMDB
    movie_data = await tmdb_service.get_movie_details(tmdb_id, tmdb_language)

    if movie_data:
        card_text = format_movie_card(movie_data, lang=lang)

        # Get trailer
        trailer_url = await tmdb_service.get_movie_trailer(tmdb_id, tmdb_language)

        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        from aiogram.utils.keyboard import InlineKeyboardBuilder

        builder = InlineKeyboardBuilder()

        if trailer_url:
            builder.row(
                InlineKeyboardButton(
                    text=get_text("btn_trailer", lang),
                    url=trailer_url
                )
            )

        builder.row(
            InlineKeyboardButton(
                text=get_text("btn_delete", lang),
                callback_data=f"saved:delete:{tmdb_id}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=get_text("btn_back", lang),
                callback_data="menu:saved"
            )
        )

        if movie_data.get("poster_url"):
            try:
                await callback.message.delete()
                await callback.message.answer_photo(
                    photo=movie_data["poster_url"],
                    caption=card_text,
                    reply_markup=builder.as_markup(),
                    parse_mode="Markdown"
                )
            except Exception:
                await callback.message.edit_text(
                    card_text,
                    reply_markup=builder.as_markup(),
                    parse_mode="Markdown"
                )
        else:
            await callback.message.edit_text(
                card_text,
                reply_markup=builder.as_markup(),
                parse_mode="Markdown"
            )
    else:
        await callback.answer(get_text("error_occurred", lang))

    await callback.answer()


@router.callback_query(F.data.startswith("saved:delete:"))
async def delete_saved_movie(callback: CallbackQuery, db: Database):
    """Delete a movie from saved list."""
    tmdb_id = int(callback.data.split(":")[2])

    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uk"

    await db.delete_saved_movie(callback.from_user.id, tmdb_id)
    await callback.answer(get_text("movie_deleted", lang))

    # Return to saved list
    await show_saved_movies(callback, db)
