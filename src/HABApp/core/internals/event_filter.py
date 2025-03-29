from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from HABApp.core.events import (
        ValueUpdateEvent,
        ValueChangeEvent,
        ValueCommandEvent,
        ItemNoChangeEvent,
        ItemNoUpdateEvent,
    )


class EventFilterBase:
    def trigger(
        self, event: ValueUpdateEvent | ValueChangeEvent | ValueCommandEvent | ItemNoChangeEvent | ItemNoUpdateEvent
    ) -> bool:
        raise NotImplementedError()

    def describe(self) -> str:
        raise NotImplementedError()

    def __repr__(self) -> str:
        return f'<{self.describe()} at 0x{id(self):X}>'
