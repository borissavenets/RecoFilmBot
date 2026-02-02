from .uk import TEXTS as UK_TEXTS
from .en import TEXTS as EN_TEXTS

LOCALES = {
    "uk": UK_TEXTS,
    "en": EN_TEXTS
}


def get_text(key: str, lang: str = "uk") -> str:
    texts = LOCALES.get(lang, UK_TEXTS)
    return texts.get(key, UK_TEXTS.get(key, key))


__all__ = ["get_text", "LOCALES"]
