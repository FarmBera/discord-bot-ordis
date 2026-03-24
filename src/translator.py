import yaml
import discord

from config.config import Lang, language
from src.constants.color import C


class Translator:
    EN: str = Lang.EN
    KO: str = Lang.KO

    def __init__(self, lang=EN):
        self.lang = lang
        self.translations = {}
        try:
            with open(f"locale/{self.lang}.yml", "r", encoding="utf-8") as f:
                self.translations = yaml.safe_load(f)
        except FileNotFoundError:
            msg = f"{C.yellow}[warn]: Translation file for '{self.lang}' not found.{C.default}"
            print(msg)
            try:  # retry with default language: English
                with open(f"locale/{self.EN}.yml", "r", encoding="utf-8") as f:
                    self.translations = yaml.safe_load(f)
            except FileNotFoundError:
                msg = f"{C.red}[warn]: Default translation file 'en.yml' also not found.{C.default}"
                print(msg)

    def get(self, key, **kwargs) -> str:
        """
        receive keys and return translated text (ex: 'main_screen.title')
        """
        keys = key.split(".")
        value = self.translations
        try:
            for k in keys:
                value = value[k]
            return value.format(**kwargs) if kwargs else value
        except (KeyError, TypeError):
            return key

    def trs(self, key) -> str:
        """
        receive SPECIAL keys (not officialy translated text in API) and return translated text (ex: 'ts.trs(SEARCH_QUERY)')
        """
        if self.lang == self.EN:
            return key

        trs_dict = self.translations.get("trs")
        if not trs_dict:
            return key

        lower_key = key.lower()
        for k, v in trs_dict.items():
            if k.lower() == lower_key:
                return v
        return key


# initialize language
if language not in [Lang.EN, Lang.KO]:  # input check
    print(
        f"{C.red}Unknown string: {C.yellow}'{language}'. {C.white}will setup default lang: {C.cyan}{Lang.EN}{C.default}"
    )
    language = Lang.EN

_translators: dict[str, Translator] = {
    Lang.KO: Translator(lang=Lang.KO),
    Lang.EN: Translator(lang=Lang.EN),
}
ts = _translators.get(language, _translators[Lang.EN])

_LOCALE_TO_LANG: dict[discord.Locale, str] = {
    discord.Locale.korean: Lang.KO,
    discord.Locale.american_english: Lang.EN,
}


def locale_to_lang(locale: discord.Locale) -> str:
    return _LOCALE_TO_LANG.get(locale, Lang.EN)


def get_ts_by_lang(lang_code: str) -> Translator:
    """Get Translator instance by language code string (e.g. 'ko', 'en')."""
    return _translators.get(lang_code, _translators[Lang.EN])


def get_ts(locale: discord.Locale) -> Translator:
    """Get Translator instance by discord.Locale."""
    return get_ts_by_lang(locale_to_lang(locale))
