from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from locales import get_text


def get_language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Українська", callback_data="lang:uk"),
        InlineKeyboardButton(text="English", callback_data="lang:en")
    )
    return builder.as_markup()


def get_main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text("btn_find_movie", lang),
            callback_data="menu:find_movie"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text("btn_my_profile", lang),
            callback_data="menu:profile"
        ),
        InlineKeyboardButton(
            text=get_text("btn_saved", lang),
            callback_data="menu:saved"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text("btn_update_profile", lang),
            callback_data="menu:update_profile"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text("btn_change_language", lang),
            callback_data="menu:change_language"
        )
    )
    return builder.as_markup()


def get_multi_select_keyboard(
    options: list[tuple[str, str]],
    selected: set[str],
    lang: str,
    callback_prefix: str,
    show_done: bool = True
) -> InlineKeyboardMarkup:
    """
    Create a multi-select keyboard with checkboxes.
    options: list of (option_id, text_key) tuples
    selected: set of selected option_ids
    """
    builder = InlineKeyboardBuilder()

    for option_id, text_key in options:
        check = "✅ " if option_id in selected else ""
        text = get_text(text_key, lang)
        builder.row(
            InlineKeyboardButton(
                text=f"{check}{text}",
                callback_data=f"{callback_prefix}:{option_id}"
            )
        )

    if show_done:
        builder.row(
            InlineKeyboardButton(
                text=get_text("btn_done", lang),
                callback_data=f"{callback_prefix}:done"
            )
        )

    return builder.as_markup()


def get_single_select_keyboard(
    options: list[tuple[str, str]],
    lang: str,
    callback_prefix: str
) -> InlineKeyboardMarkup:
    """
    Create a single-select keyboard.
    options: list of (option_id, text_key) tuples
    """
    builder = InlineKeyboardBuilder()

    for option_id, text_key in options:
        text = get_text(text_key, lang)
        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=f"{callback_prefix}:{option_id}"
            )
        )

    return builder.as_markup()


def get_recommendation_keyboard(
    lang: str,
    tmdb_id: int,
    session_id: int,
    is_saved: bool = False,
    trailer_url: str | None = None
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # First row: Trailer (if available) and Save
    row1 = []
    if trailer_url:
        row1.append(
            InlineKeyboardButton(
                text=get_text("btn_trailer", lang),
                url=trailer_url
            )
        )

    save_text = get_text("btn_saved_mark" if is_saved else "btn_save", lang)
    row1.append(
        InlineKeyboardButton(
            text=save_text,
            callback_data=f"rec:save:{tmdb_id}:{session_id}"
        )
    )
    builder.row(*row1)

    # Second row: Next and New request
    builder.row(
        InlineKeyboardButton(
            text=get_text("btn_next", lang),
            callback_data=f"rec:next:{session_id}"
        ),
        InlineKeyboardButton(
            text=get_text("btn_new_request", lang),
            callback_data="rec:new_request"
        )
    )

    return builder.as_markup()


def get_saved_movies_keyboard(
    movies: list[dict],
    lang: str,
    page: int = 0,
    per_page: int = 5
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_movies = movies[start_idx:end_idx]

    for movie in page_movies:
        builder.row(
            InlineKeyboardButton(
                text=movie["title"],
                callback_data=f"saved:view:{movie['tmdb_id']}"
            ),
            InlineKeyboardButton(
                text=get_text("btn_delete", lang),
                callback_data=f"saved:delete:{movie['tmdb_id']}"
            )
        )

    # Pagination
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="◀️", callback_data=f"saved:page:{page - 1}")
        )
    if end_idx < len(movies):
        nav_buttons.append(
            InlineKeyboardButton(text="▶️", callback_data=f"saved:page:{page + 1}")
        )
    if nav_buttons:
        builder.row(*nav_buttons)

    # Back button
    builder.row(
        InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data="menu:back"
        )
    )

    return builder.as_markup()


def get_back_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data="menu:back"
        )
    )
    return builder.as_markup()


def get_skip_keyboard(lang: str, callback_prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text("btn_skip", lang),
            callback_data=f"{callback_prefix}:skip"
        )
    )
    return builder.as_markup()


def get_done_keyboard(lang: str, callback_prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text("btn_done", lang),
            callback_data=f"{callback_prefix}:done"
        )
    )
    return builder.as_markup()
