from __future__ import annotations

from typing import TYPE_CHECKING

import typing_extensions
from typing_extensions import override

from HABApp.core.asyncio import create_task
from HABApp.core.internals.wrapped_function.base import P, R, WrappedFunctionBase


if TYPE_CHECKING:
    import logging
    from collections.abc import Callable

    from HABApp.core.internals import Context


class WrappedSyncFunction(WrappedFunctionBase[P, R]):
    def __init__(
        self,
        func: Callable,
        warn_too_long: bool=True,
        name: str | None = None,
        logger: logging.Logger | None = None,
        context: Context | None = None,
    ) -> None:
        super().__init__(name=name, func=func, logger=logger, context=context)
        if not callable(func):
            msg = f'{func} is not callable'
            raise TypeError(msg)

        self.func = func
        self.warn_too_long: bool = warn_too_long

    @override
    def run(self, *args: P.args, **kwargs: P.kwargs) -> None:
        create_task(self.async_run(*args, **kwargs), name=self.name)

    @override
    async def async_run(self, *args: P.args, **kwargs: P.kwargs) -> R | None:
        try:
            return self.func(*args, **kwargs)
        except Exception as e:
            self.process_exception(e, *args, **kwargs)
            return None
