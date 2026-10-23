"""Винятки пакета."""


# Базовий клас для всіх помилок пакета. Сам нічого не додає: його сенс у тому,
# що except ReporterError ловить і його, і всіх нащадків — як instanceof у JS
# перевіряє весь ланцюжок прототипів. Так "наші" помилки відрізняються від
# чужих багів (KeyError, TypeError), які ловити не можна.
class ReporterError(Exception):
    pass


class ValidationError(ReporterError):
    def __init__(self, rule: str, field: str, detail: str) -> None:
        # Текст помилки потрапляє в e.args, і його показує repr(e):
        # ValidationError('expected int, got str ...').
        super().__init__(detail)
        self.rule = rule
        self.field = field
        self.detail = detail

    # __str__ — те, що повертають str(e), f"{e}" і print(e); аналог toString()
    # у JS. Формат рядка живе тут, а не там, де помилку друкують, тому __main__
    # ловить базовий ReporterError і друкує просто {e}, не знаючи про rule і field.
    def __str__(self) -> str:
        return f"rule={self.rule} field={self.field}: {self.detail}"
