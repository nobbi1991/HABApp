from __future__ import annotations

from collections.abc import Iterator
from typing import Generic, Literal, TypeAlias, TypeVar


T = TypeVar('T')

T_PRIO: TypeAlias = Literal['first', 'last'] | int
T_ENTRY: TypeAlias = tuple[T_PRIO, T]


def _sort_func(obj: T_ENTRY) -> tuple[int, T_PRIO]:
    """Sorting function for the priority list.

    Returns a tuple of (prio, obj) where prio is an int that defines the order
    of the items in the list. The first element in the tuple is used for sorting
    and the second element is the original object.

    If the priority is not set, it is set to 1.

    :param obj: A tuple of (priority, object)
    :return: A tuple of (prio, obj)
    """
    prio = {'first': 0, 'last': 2}
    key = obj[0]
    assert isinstance(key, int) or key in prio
    return prio.get(key, 1), key


# TODO: Move this to the connection
class PriorityList(Generic[T]):
    def __init__(self) -> None:
        self._objs: list[T_ENTRY] = []

    def append(self, obj: T, priority: T_PRIO) -> None:
        for o in self._objs:
            assert o[0] != priority, priority
        self._objs.append((priority, obj))
        self._objs.sort(key=_sort_func)

    def remove(self, obj: T) -> None:
        for i, (_, existing) in self._objs:
            if existing is obj:
                self._objs.pop(i)
                return None

    def __iter__(self) -> Iterator[T]:
        for p, o in self._objs:
            yield o

    def reversed(self) -> Iterator[T]:
        for p, o in reversed(self._objs):
            yield o

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} {list(self)}>'
