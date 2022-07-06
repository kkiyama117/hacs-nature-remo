from typing import Any, Iterable


def find_by(items: Iterable[Any], attr: str, value: Any = None):
    for x in items:
        if hasattr(x, attr) and getattr(x, attr) == value:
            return x
    else:
        x = None
