from __future__ import annotations

import typing
from typing import NoReturn

from HABApp.core.internals import EventFilterBase

if typing.TYPE_CHECKING:
    from HABApp.core.events import (
        ValueUpdateEvent,
        ValueChangeEvent,
        ValueCommandEvent,
        ItemNoChangeEvent,
        ItemNoUpdateEvent,
    )


class EventFilterBaseGroup(EventFilterBase):
    def __init__(self, *args: EventFilterBase) -> None:
        self.filters: tuple[EventFilterBase, ...] = args

    def trigger(
        self, event: ValueUpdateEvent | ValueChangeEvent | ValueCommandEvent | ItemNoChangeEvent | ItemNoUpdateEvent
    ) -> bool:
        raise NotImplementedError()

    def describe(self) -> str:
        raise NotImplementedError()


class OrFilterGroup(EventFilterBaseGroup):
    """Only one child filter has to match"""

    def trigger(
        self, event: ValueUpdateEvent | ValueChangeEvent | ValueCommandEvent | ItemNoChangeEvent | ItemNoUpdateEvent
    ) -> bool:
        return any(f.trigger(event) for f in self.filters)

    def describe(self) -> str:
        objs = [f.describe() for f in self.filters]
        return f'({" or ".join(objs)})'


class AndFilterGroup(EventFilterBaseGroup):
    """All child filters have to match"""

    def trigger(
        self, event: ValueUpdateEvent | ValueChangeEvent | ValueCommandEvent | ItemNoChangeEvent | ItemNoUpdateEvent
    ) -> bool:
        return all(f.trigger(event) for f in self.filters)

    def describe(self) -> str:
        objs = [f.describe() for f in self.filters]
        return f'({" and ".join(objs)})'
