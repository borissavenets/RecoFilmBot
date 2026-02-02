from aiogram import Router

from .start import router as start_router
from .base_survey import router as base_survey_router
from .dynamic_survey import router as dynamic_survey_router
from .recommendation import router as recommendation_router
from .menu import router as menu_router
from .profile import router as profile_router
from .saved import router as saved_router


def setup_routers() -> Router:
    """Setup all routers and return the main router."""
    main_router = Router()

    main_router.include_router(start_router)
    main_router.include_router(base_survey_router)
    main_router.include_router(dynamic_survey_router)
    main_router.include_router(recommendation_router)
    main_router.include_router(menu_router)
    main_router.include_router(profile_router)
    main_router.include_router(saved_router)

    return main_router


__all__ = ["setup_routers"]
