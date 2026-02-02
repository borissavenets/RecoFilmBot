from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from database import Database
from locales import get_text
from keyboards import get_main_menu_keyboard, get_language_keyboard
from .dynamic_survey import start_dynamic_survey
from .base_survey import BaseSurveyStates, send_emotions_like_question

router = Router()


@router.callback_query(F.data == "menu:find_movie")
async def find_movie(callback: CallbackQuery, state: FSMContext, db: Database):
    """Start finding a movie - begin dynamic survey."""
    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uk"

    await start_dynamic_survey(callback, state, lang)


@router.callback_query(F.data == "menu:profile")
async def show_profile(callback: CallbackQuery, db: Database):
    """Show user profile."""
    from .profile import show_user_profile
    await show_user_profile(callback, db)


@router.callback_query(F.data == "menu:saved")
async def show_saved(callback: CallbackQuery, db: Database):
    """Show saved movies."""
    from .saved import show_saved_movies
    await show_saved_movies(callback, db)


@router.callback_query(F.data == "menu:update_profile")
async def update_profile(callback: CallbackQuery, state: FSMContext, db: Database):
    """Start profile update - re-run base survey."""
    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uk"

    await state.set_state(BaseSurveyStates.emotions_like)
    await state.update_data(lang=lang, selected=[])

    await callback.message.edit_text(get_text("base_survey_intro", lang))
    await send_emotions_like_question(callback.message, lang)
    await callback.answer()


@router.callback_query(F.data == "menu:change_language")
async def change_language(callback: CallbackQuery):
    """Show language selection."""
    await callback.message.edit_text(
        get_text("choose_language", "uk"),
        reply_markup=get_language_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "menu:back")
async def back_to_menu(callback: CallbackQuery, db: Database):
    """Return to main menu."""
    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uk"

    await callback.message.edit_text(
        get_text("main_menu", lang),
        reply_markup=get_main_menu_keyboard(lang)
    )
    await callback.answer()
