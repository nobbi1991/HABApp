import logging
from typing import Generic, TypeVar

from whenever import Instant

from HABApp.core.asyncio import run_func_from_async
from HABApp.core.items.base_item_watch import BaseWatch, ItemNoChangeWatch, ItemNoUpdateWatch

log = logging.getLogger('HABApp')

_WATCH_OBJ = TypeVar('_WATCH_OBJ', bound=BaseWatch)


class ItemTimes(Generic[_WATCH_OBJ]):
    WATCH: type[_WATCH_OBJ]

    def __init__(self, name: str, instant: Instant, watch_cls: type[_WATCH_OBJ]) -> None:
        self.name: str = name
        self.instant: Instant = instant
        self.tasks: list[_WATCH_OBJ] = []
        self.WATCH = watch_cls

    def set(self, instant: Instant, events: bool = True) -> None:
        self.instant = instant
        if not self.tasks:
            return

        if events:
            run_func_from_async(self.__async_schedule_events)
        return None

    def add_watch(self, secs: int | float) -> _WATCH_OBJ:
        # don't add the watch two times
        for t in self.tasks:
            if not t.fut.is_canceled and t.fut.secs == secs:
                log.warning(f'Watcher {self.WATCH.__name__} ({t.fut.secs}s) for {self.name} has already been created')
                return t

        w = self.WATCH(self.name, secs)
        self.tasks.append(w)
        log.debug(f'Added {self.WATCH.__name__} ({w.fut.secs}s) for {self.name}')
        return w

    def __async_schedule_events(self) -> None:
        canceled = []
        for t in self.tasks:
            if t.fut.is_canceled:
                canceled.append(t)
            else:
                t.fut.reset()

        # remove canceled tasks
        if canceled:
            for c in canceled:
                self.tasks.remove(c)
                log.debug(f'Removed {self.WATCH.__name__} ({c.fut.secs}s) for {self.name}')
        return None


class UpdatedTime(ItemTimes[ItemNoUpdateWatch]):
    def __init__(self, name: str, instant: Instant) -> None:
        super().__init__(name, instant, ItemNoUpdateWatch)


class ChangedTime(ItemTimes[ItemNoChangeWatch]):
    def __init__(self, name: str, instant: Instant) -> None:
        super().__init__(name, instant, ItemNoChangeWatch)  # ✅ Pass the correct watch class
