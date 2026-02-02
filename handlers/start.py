from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import Database
from locales import get_text
from keyboards import get_language_keyboard, get_main_menu_keyboard
from .base_survey import BaseSurveyStates

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database, state: FSMContext):
    """Handle /start command."""
    await state.clear()

    user = await db.get_user(message.from_user.id)

    if user is None:
        # New user - show language selection
        await message.answer(
            get_text("choose_language", "uk"),
            reply_markup=get_language_keyboard()
        )
    else:
        # Existing user - show main menu or continue setup
        lang = user["language"]

        if not user["base_profile_completed"]:
            # Need to complete base profile
            await message.answer(get_text("base_survey_intro", lang))
            await state.set_state(BaseSurveyStates.emotions_like)
            await state.update_data(lang=lang, selected=[])

            from .base_survey import send_emotions_like_question
            await send_emotions_like_question(message, lang)
        else:
            # Show main menu
            await message.answer(
                get_text("main_menu", lang),
                reply_markup=get_main_menu_keyboard(lang)
            )


@router.callback_query(F.data.startswith("lang:"))
async def language_selected(callback: CallbackQuery, db: Database, state: FSMContext):
    """Handle language selection."""
    lang = callback.data.split(":")[1]

    # Create or update user
    user = await db.get_user(callback.from_user.id)
    if user is None:
        await db.create_user(callback.from_user.id, lang)
    else:
        await db.update_user_language(callback.from_user.id, lang)

    await callback.answer(get_text("language_set", lang))

    # Check if profile is completed
    user = await db.get_user(callback.from_user.id)

    if not user["base_profile_completed"]:
        # Start base survey
        await callback.message.edit_text(get_text("welcome", lang))
        await callback.message.answer(get_text("base_survey_intro", lang))

        await state.set_state(BaseSurveyStates.emotions_like)
        await state.update_data(lang=lang, selected=[])

        from .base_survey import send_emotions_like_question
        await send_emotions_like_question(callback.message, lang)
    else:
        # Show main menu
        await callback.message.edit_text(
            get_text("main_menu", lang),
            reply_markup=get_main_menu_keyboard(lang)
        )
