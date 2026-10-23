"""Читання вхідного файлу."""

import json
import logging

logger = logging.getLogger(__name__)


# Читання окремо від політики: функція лише відкриває й парсить файл, а що
# робити з помилкою (який текст, який exit code) вирішує __main__.
# with закриває файл навіть при винятку, як try/finally.
def load_courses(path: str) -> list:
    logger.debug("reading %s", path)
    with open(path, encoding="utf-8") as f:
        return json.load(f)
