from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database
from locales import get_text
from keyboards import (
    get_multi_select_keyboard,
    get_single_select_keyboard,
    get_main_menu_keyboard,
    get_skip_keyboard
)

router = Router()


class BaseSurveyStates(StatesGroup):
    emotions_like = State()
    emotions_dislike = State()
    complexity = State()
    favorite_movies = State()
    genres_like = State()
    visual_style = State()
    characters_like = State()
    taboo = State()
    afterfeel = State()


EMOTION_OPTIONS = [
    ("joy", "emo_joy"),
    ("excitement", "emo_excitement"),
    ("tension", "emo_tension"),
    ("fear", "emo_fear"),
    ("sadness", "emo_sadness"),
    ("inspiration", "emo_inspiration"),
    ("romance", "emo_romance"),
    ("nostalgia", "emo_nostalgia"),
    ("curiosity", "emo_curiosity"),
    ("relaxation", "emo_relaxation"),
]

COMPLEXITY_OPTIONS = [
    ("simple", "complexity_simple"),
    ("medium", "complexity_medium"),
    ("complex", "complexity_complex"),
    ("any", "complexity_any"),
]

GENRE_OPTIONS = [
    ("action", "genre_action"),
    ("comedy", "genre_comedy"),
    ("drama", "genre_drama"),
    ("horror", "genre_horror"),
    ("scifi", "genre_scifi"),
    ("fantasy", "genre_fantasy"),
    ("thriller", "genre_thriller"),
    ("romance", "genre_romance"),
    ("animation", "genre_animation"),
    ("documentary", "genre_documentary"),
    ("crime", "genre_crime"),
    ("mystery", "genre_mystery"),
    ("adventure", "genre_adventure"),
    ("family", "genre_family"),
    ("war", "genre_war"),
    ("history", "genre_history"),
]

VISUAL_OPTIONS = [
    ("realistic", "visual_realistic"),
    ("stylized", "visual_stylized"),
    ("dark", "visual_dark"),
    ("bright", "visual_bright"),
    ("minimalist", "visual_minimalist"),
    ("any", "visual_any"),
]

CHARACTER_OPTIONS = [
    ("hero", "char_hero"),
    ("antihero", "char_antihero"),
    ("villain", "char_villain"),
    ("ordinary", "char_ordinary"),
    ("genius", "char_genius"),
    ("rebel", "char_rebel"),
    ("romantic", "char_romantic"),
    ("comic", "char_comic"),
]

AFTERFEEL_OPTIONS = [
    ("motivated", "after_motivated"),
    ("think", "after_think"),
    ("calm", "after_calm"),
    ("discuss", "after_discuss"),
    ("rewatch", "after_rewatch"),
    ("nothing", "after_nothing"),
]


async def send_emotions_like_question(message: Message, lang: str):
    """Send the first question about liked emotions."""
    await message.answer(
        f"{get_text('base_q1_emotions_like', lang)}\n\n{get_text('select_multiple', lang)}",
        reply_markup=get_multi_select_keyboard(EMOTION_OPTIONS, set(), lang, "base_emo_like")
    )


# Step 1: Emotions Like
@router.callback_query(BaseSurveyStates.emotions_like, F.data.startswith("base_emo_like:"))
async def process_emotions_like(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "uk")
    selected = set(data.get("selected", []))

    if action == "done":
        if not selected:
            await callback.answer(get_text("min_one_option", lang))
            return

        await state.update_data(emotions_like=list(selected), selected=[])
        await state.set_state(BaseSurveyStates.emotions_dislike)

        await callback.message.edit_text(
            f"{get_text('base_q2_emotions_dislike', lang)}\n\n{get_text('select_multiple', lang)}",
            reply_markup=get_multi_select_keyboard(EMOTION_OPTIONS, set(), lang, "base_emo_dislike")
        )
    else:
        if action in selected:
            selected.remove(action)
        else:
            selected.add(action)

        await state.update_data(selected=list(selected))
        await callback.message.edit_reply_markup(
            reply_markup=get_multi_select_keyboard(EMOTION_OPTIONS, selected, lang, "base_emo_like")
        )

    await callback.answer()


# Step 2: Emotions Dislike
@router.callback_query(BaseSurveyStates.emotions_dislike, F.data.startswith("base_emo_dislike:"))
async def process_emotions_dislike(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "uk")
    selected = set(data.get("selected", []))

    if action == "done":
        await state.update_data(emotions_dislike=list(selected), selected=[])
        await state.set_state(BaseSurveyStates.complexity)

        await callback.message.edit_text(
            get_text("base_q3_complexity", lang),
            reply_markup=get_single_select_keyboard(COMPLEXITY_OPTIONS, lang, "base_complexity")
        )
    else:
        if action in selected:
            selected.remove(action)
        else:
            selected.add(action)

        await state.update_data(selected=list(selected))
        await callback.message.edit_reply_markup(
            reply_markup=get_multi_select_keyboard(EMOTION_OPTIONS, selected, lang, "base_emo_dislike")
        )

    await callback.answer()


# Step 3: Complexity
@router.callback_query(BaseSurveyStates.complexity, F.data.startswith("base_complexity:"))
async def process_complexity(callback: CallbackQuery, state: FSMContext):
    complexity = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "uk")

    await state.update_data(complexity=complexity)
    await state.set_state(BaseSurveyStates.favorite_movies)

    await callback.message.edit_text(
        get_text("base_q4_favorite_movies", lang),
        reply_markup=get_skip_keyboard(lang, "base_favorite")
    )
    await callback.answer()


# Step 4: Favorite Movies (text input or skip)
@router.callback_query(BaseSurveyStates.favorite_movies, F.data == "base_favorite:skip")
async def skip_favorite_movies(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uk")

    await state.update_data(favorite_movies="", selected=[])
    await state.set_state(BaseSurveyStates.genres_like)

    await callback.message.edit_text(
        f"{get_text('base_q6_genres', lang)}\n\n{get_text('select_multiple', lang)}",
        reply_markup=get_multi_select_keyboard(GENRE_OPTIONS, set(), lang, "base_genre_like")
    )
    await callback.answer()


@router.message(BaseSurveyStates.favorite_movies)
async def process_favorite_movies(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uk")

    await state.update_data(favorite_movies=message.text, selected=[])
    await state.set_state(BaseSurveyStates.genres_like)

    await message.answer(
        f"{get_text('base_q6_genres', lang)}\n\n{get_text('select_multiple', lang)}",
        reply_markup=get_multi_select_keyboard(GENRE_OPTIONS, set(), lang, "base_genre_like")
    )


# Step 5: Genres Like
@router.callback_query(BaseSurveyStates.genres_like, F.data.startswith("base_genre_like:"))
async def process_genres_like(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "uk")
    selected = set(data.get("selected", []))

    if action == "done":
        if not selected:
            await callback.answer(get_text("min_one_option", lang))
            return

        await state.update_data(genres_like=list(selected), selected=[])
        await state.set_state(BaseSurveyStates.visual_style)

        await callback.message.edit_text(
            f"{get_text('base_q8_visual', lang)}\n\n{get_text('select_multiple', lang)}",
            reply_markup=get_multi_select_keyboard(VISUAL_OPTIONS, set(), lang, "base_visual")
        )
    else:
        if action in selected:
            selected.remove(action)
        else:
            selected.add(action)

        await state.update_data(selected=list(selected))
        await callback.message.edit_reply_markup(
            reply_markup=get_multi_select_keyboard(GENRE_OPTIONS, selected, lang, "base_genre_like")
        )

    await callback.answer()


# Step 6: Visual Style (multi-select)
@router.callback_query(BaseSurveyStates.visual_style, F.data.startswith("base_visual:"))
async def process_visual_style(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "uk")
    selected = set(data.get("selected", []))

    if action == "done":
        if not selected:
            await callback.answer(get_text("min_one_option", lang))
            return

        await state.update_data(visual_style=list(selected), selected=[])
        await state.set_state(BaseSurveyStates.characters_like)

        await callback.message.edit_text(
            f"{get_text('base_q9_characters_like', lang)}\n\n{get_text('select_multiple', lang)}",
            reply_markup=get_multi_select_keyboard(CHARACTER_OPTIONS, set(), lang, "base_char_like")
        )
    else:
        if action in selected:
            selected.remove(action)
        else:
            selected.add(action)

        await state.update_data(selected=list(selected))
        await callback.message.edit_reply_markup(
            reply_markup=get_multi_select_keyboard(VISUAL_OPTIONS, selected, lang, "base_visual")
        )

    await callback.answer()


# Step 7: Characters Like
@router.callback_query(BaseSurveyStates.characters_like, F.data.startswith("base_char_like:"))
async def process_characters_like(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "uk")
    selected = set(data.get("selected", []))

    if action == "done":
        if not selected:
            await callback.answer(get_text("min_one_option", lang))
            return

        await state.update_data(characters_like=list(selected), selected=[])
        await state.set_state(BaseSurveyStates.taboo)

        await callback.message.edit_text(
            get_text("base_q11_taboo", lang),
            reply_markup=get_skip_keyboard(lang, "base_taboo")
        )
    else:
        if action in selected:
            selected.remove(action)
        else:
            selected.add(action)

        await state.update_data(selected=list(selected))
        await callback.message.edit_reply_markup(
            reply_markup=get_multi_select_keyboard(CHARACTER_OPTIONS, selected, lang, "base_char_like")
        )

    await callback.answer()


# Step 9: Taboo (text input or skip)
@router.callback_query(BaseSurveyStates.taboo, F.data == "base_taboo:skip")
async def skip_taboo(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uk")

    await state.update_data(taboo="", selected=[])
    await state.set_state(BaseSurveyStates.afterfeel)

    await callback.message.edit_text(
        f"{get_text('base_q12_afterfeel', lang)}\n\n{get_text('select_multiple', lang)}",
        reply_markup=get_multi_select_keyboard(AFTERFEEL_OPTIONS, set(), lang, "base_afterfeel")
    )
    await callback.answer()


@router.message(BaseSurveyStates.taboo)
async def process_taboo(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uk")

    text = message.text.lower()
    if text in ["нічого", "nothing", "ні", "no", "пропустити", "skip"]:
        await state.update_data(taboo="")
    else:
        await state.update_data(taboo=message.text)

    await state.update_data(selected=[])
    await state.set_state(BaseSurveyStates.afterfeel)

    await message.answer(
        f"{get_text('base_q12_afterfeel', lang)}\n\n{get_text('select_multiple', lang)}",
        reply_markup=get_multi_select_keyboard(AFTERFEEL_OPTIONS, set(), lang, "base_afterfeel")
    )


# Step 10: Afterfeel (final step)
@router.callback_query(BaseSurveyStates.afterfeel, F.data.startswith("base_afterfeel:"))
async def process_afterfeel(callback: CallbackQuery, state: FSMContext, db: Database):
    action = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "uk")
    selected = set(data.get("selected", []))

    if action == "done":
        if not selected:
            await callback.answer(get_text("min_one_option", lang))
            return

        # Save profile
        profile_data = {
            "emotions_like": data.get("emotions_like", []),
            "emotions_dislike": data.get("emotions_dislike", []),
            "complexity": data.get("complexity", "any"),
            "favorite_movies": data.get("favorite_movies", ""),
            "disliked_movies": "",
            "genres_like": data.get("genres_like", []),
            "genres_dislike": [],
            "visual_style": data.get("visual_style", []),
            "characters_like": data.get("characters_like", []),
            "characters_dislike": [],
            "taboo": data.get("taboo", ""),
            "afterfeel": list(selected),
        }

        await db.save_base_profile(callback.from_user.id, profile_data)
        await db.set_base_profile_completed(callback.from_user.id, True)

        await state.clear()

        await callback.message.edit_text(
            f"{get_text('base_survey_complete', lang)}\n\n{get_text('try_find_movie', lang)}"
        )
        await callback.message.answer(
            get_text("main_menu", lang),
            reply_markup=get_main_menu_keyboard(lang)
        )
    else:
        if action in selected:
            selected.remove(action)
        else:
            selected.add(action)

        await state.update_data(selected=list(selected))
        await callback.message.edit_reply_markup(
            reply_markup=get_multi_select_keyboard(AFTERFEEL_OPTIONS, selected, lang, "base_afterfeel")
        )

    await callback.answer()
