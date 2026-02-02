from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database
from locales import get_text
from keyboards import get_single_select_keyboard, get_skip_keyboard

router = Router()


class DynamicSurveyStates(StatesGroup):
    mood = State()
    energy = State()
    company = State()
    time = State()
    seen_preference = State()
    specific_request = State()


MOOD_OPTIONS = [
    ("happy", "mood_happy"),
    ("sad", "mood_sad"),
    ("stressed", "mood_stressed"),
    ("bored", "mood_bored"),
    ("romantic", "mood_romantic"),
    ("adventurous", "mood_adventurous"),
    ("thoughtful", "mood_thoughtful"),
    ("tired", "mood_tired"),
]

ENERGY_OPTIONS = [
    ("high", "energy_high"),
    ("medium", "energy_medium"),
    ("low", "energy_low"),
]

COMPANY_OPTIONS = [
    ("alone", "company_alone"),
    ("partner", "company_partner"),
    ("friends", "company_friends"),
    ("family", "company_family"),
    ("kids", "company_kids"),
]

TIME_OPTIONS = [
    ("short", "time_short"),
    ("medium", "time_medium"),
    ("long", "time_long"),
    ("series", "time_series"),
]

SEEN_OPTIONS = [
    ("new", "seen_new"),
    ("classic", "seen_classic"),
    ("any", "seen_any"),
]


async def start_dynamic_survey(message_or_callback, state: FSMContext, lang: str):
    """Start the dynamic survey flow."""
    await state.set_state(DynamicSurveyStates.mood)
    await state.update_data(lang=lang)

    text = f"{get_text('dynamic_intro', lang)}\n\n{get_text('dynamic_q1_mood', lang)}"
    keyboard = get_single_select_keyboard(MOOD_OPTIONS, lang, "dyn_mood")

    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.edit_text(text, reply_markup=keyboard)
    else:
        await message_or_callback.answer(text, reply_markup=keyboard)


# Step 1: Mood
@router.callback_query(DynamicSurveyStates.mood, F.data.startswith("dyn_mood:"))
async def process_mood(callback: CallbackQuery, state: FSMContext):
    mood = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "uk")

    await state.update_data(mood=mood)
    await state.set_state(DynamicSurveyStates.energy)

    await callback.message.edit_text(
        get_text("dynamic_q2_energy", lang),
        reply_markup=get_single_select_keyboard(ENERGY_OPTIONS, lang, "dyn_energy")
    )
    await callback.answer()


# Step 2: Energy
@router.callback_query(DynamicSurveyStates.energy, F.data.startswith("dyn_energy:"))
async def process_energy(callback: CallbackQuery, state: FSMContext):
    energy = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "uk")

    await state.update_data(energy=energy)
    await state.set_state(DynamicSurveyStates.company)

    await callback.message.edit_text(
        get_text("dynamic_q3_company", lang),
        reply_markup=get_single_select_keyboard(COMPANY_OPTIONS, lang, "dyn_company")
    )
    await callback.answer()


# Step 3: Company
@router.callback_query(DynamicSurveyStates.company, F.data.startswith("dyn_company:"))
async def process_company(callback: CallbackQuery, state: FSMContext):
    company = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "uk")

    await state.update_data(company=company)
    await state.set_state(DynamicSurveyStates.time)

    await callback.message.edit_text(
        get_text("dynamic_q4_time", lang),
        reply_markup=get_single_select_keyboard(TIME_OPTIONS, lang, "dyn_time")
    )
    await callback.answer()


# Step 4: Time
@router.callback_query(DynamicSurveyStates.time, F.data.startswith("dyn_time:"))
async def process_time(callback: CallbackQuery, state: FSMContext):
    time = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "uk")

    await state.update_data(time=time)
    await state.set_state(DynamicSurveyStates.seen_preference)

    await callback.message.edit_text(
        get_text("dynamic_q5_seen", lang),
        reply_markup=get_single_select_keyboard(SEEN_OPTIONS, lang, "dyn_seen")
    )
    await callback.answer()


# Step 5: Seen preference (new/classic)
@router.callback_query(DynamicSurveyStates.seen_preference, F.data.startswith("dyn_seen:"))
async def process_seen_preference(callback: CallbackQuery, state: FSMContext):
    seen_pref = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "uk")

    await state.update_data(seen_preference=seen_pref)
    await state.set_state(DynamicSurveyStates.specific_request)

    await callback.message.edit_text(
        get_text("dynamic_q6_specific", lang),
        reply_markup=get_skip_keyboard(lang, "dyn_specific")
    )
    await callback.answer()


# Step 6: Specific request (text or skip)
@router.callback_query(DynamicSurveyStates.specific_request, F.data == "dyn_specific:skip")
async def skip_specific_request(callback: CallbackQuery, state: FSMContext, db: Database):
    await state.update_data(specific_request="")
    await _finish_dynamic_survey(callback, state, db)


@router.message(DynamicSurveyStates.specific_request)
async def process_specific_request(message: Message, state: FSMContext, db: Database):
    text = message.text.lower()
    if text in ["ні", "no", "немає", "none"]:
        await state.update_data(specific_request="")
    else:
        await state.update_data(specific_request=message.text)

    await _finish_dynamic_survey(message, state, db)


async def _finish_dynamic_survey(source, state: FSMContext, db: Database):
    """Finish dynamic survey and start recommendation generation."""
    data = await state.get_data()
    lang = data.get("lang", "uk")

    # Get user ID
    if isinstance(source, CallbackQuery):
        user_id = source.from_user.id
        message = source.message
    else:
        user_id = source.from_user.id
        message = source

    # Create dynamic answers dict
    dynamic_answers = {
        "mood": data.get("mood", ""),
        "energy": data.get("energy", ""),
        "company": data.get("company", ""),
        "time": data.get("time", ""),
        "seen_preference": data.get("seen_preference", ""),
        "specific_request": data.get("specific_request", ""),
    }

    # Create session in DB
    session_id = await db.create_session(user_id, dynamic_answers)

    # Save session_id to state for recommendation handler
    await state.update_data(session_id=session_id, dynamic_answers=dynamic_answers)
    await state.clear()

    # Import here to avoid circular imports
    from .recommendation import generate_and_show_recommendation

    # Show loading message
    if isinstance(source, CallbackQuery):
        await source.message.edit_text(get_text("searching_movie", lang))
        await source.answer()
    else:
        loading_msg = await source.answer(get_text("searching_movie", lang))

    # Generate recommendation
    await generate_and_show_recommendation(
        message if isinstance(source, Message) else source.message,
        db,
        user_id,
        session_id,
        dynamic_answers,
        lang
    )
