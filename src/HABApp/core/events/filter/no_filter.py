from __future__ import annotations

import typing

from HABApp.core.internals import EventFilterBase

if typing.TYPE_CHECKING:
    from HABApp.core.events import (
        ValueUpdateEvent,
        ValueChangeEvent,
        ValueCommandEvent,
        ItemNoChangeEvent,
        ItemNoUpdateEvent,
    )


class NoEventFilter(EventFilterBase):
    """Triggers on all events"""

    def trigger(
        self, event: ValueUpdateEvent | ValueChangeEvent | ValueCommandEvent | ItemNoChangeEvent | ItemNoUpdateEvent
    ) -> bool:
        return True

    def describe(self) -> str:
        return f'{self.__class__.__name__}()'
