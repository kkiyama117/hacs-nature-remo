from typing import Any, Iterable, TypeVar

T = TypeVar('T')


def find_by(items: Iterable[T], attr: str, value: Any = None) -> T:
    for x in items:
        if hasattr(x, attr) and getattr(x, attr) == value:
            return x
    else:
        x = None
