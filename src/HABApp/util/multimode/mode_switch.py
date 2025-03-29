import datetime
import logging

import HABApp

from . import ValueMode
from typing import NoReturn, Callable, Any


class SwitchItemValueMode(ValueMode):
    """SwitchItemMode, same as ValueMode but enabled/disabled of the mode is controlled by a OpenHAB
    :class:`~HABApp.openhab.items.SwitchItem`

    :ivar datetime.datetime last_update: Timestamp of the last update/enable of this value                                                                    a given timedelta on the next recalculation
    :ivar    auto_disable_func: Function which can be used to disable this mode. Any function that accepts two
                                Arguments can be used. First arg is value with lower priority,
                                second argument is own value. Return ``True`` to disable this mode.
    :ivar    calc_value_func: Function to calculate the new value (e.g. ``min`` or ``max``). Any function that accepts
                              two Arguments can be used. First arg is value with lower priority,
                              second argument is own value.
    """

    def __init__(
        self,
        name: str,
        # these are the parameters special to SwitchItemValueMode
        switch_item: 'HABApp.openhab.items.SwitchItem',
        invert_switch: bool = False,
        # default kw-args from the base class
        initial_value=None,
        logger: logging.Logger | None = None,
        auto_disable_after: datetime.timedelta | None = None,
        auto_disable_func: Callable[[Any, Any], bool] | None = None,
        calc_value_func: Callable[[Any, Any], Any] | None = None,
    ) -> None:
        """

        :param name: Name of the mode
        :param switch_item: :class:`~HABApp.openhab.items.SwitchItem` that will enable/disable the mode
        :param invert_switch: invert switch state (e.g. `OFF` -> enabled, default is ``False``)
        :param initial_value: initial value of the mode
        :param logger: logger to log events
        :param auto_disable_after: see variables
        :param auto_disable_func: see variables
        :param calc_value_func: see variables
        """

        assert invert_switch is True or invert_switch is False
        assert isinstance(switch_item, HABApp.openhab.items.SwitchItem), type(switch_item)
        self.__invert_switch: bool = invert_switch

        super().__init__(
            name=name,
            initial_value=initial_value,
            enabled=switch_item.value == ('ON' if not self.__invert_switch else 'OFF'),
            enable_on_value=False,  # enable_on_value must be pinned False
            logger=logger,
            auto_disable_after=auto_disable_after,
            auto_disable_func=auto_disable_func,
            calc_value_func=calc_value_func,
        )

        # setup listener as the last thing
        switch_item.listen_event(self.__switch_changed, HABApp.core.events.ValueChangeEventFilter())
        return

    # this is the original enabled method
    __set_enable = ValueMode.set_enabled

    # prevent direct calling
    def set_enabled(self, value: bool, only_on_change: bool = False) -> NoReturn:
        """"""  # Empty docstring so this function doesn't show up in Sphinx
        msg = 'Enabled is controlled through the switch item!'
        raise PermissionError(msg)

    def __switch_changed(self, event) -> None:
        self.__set_enable(event.value == ('ON' if not self.__invert_switch else 'OFF'))
