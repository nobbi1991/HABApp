import logging
import time
from time import monotonic

from HABAppTests import ItemWaiter, OpenhabTmpItem, TestBaseRule, get_random_name

from HABApp.core.internals import ItemRegistry
from HABApp.core.provider import HABAPP_PROVIDER
from HABApp.openhab.items import OpenhabItem
from HABApp.util.multimode import MultiModeItem, SwitchItemValueMode
from HABApp.util.rate_limiter import RateLimiter


log = logging.getLogger('HABApp.Tests.MultiMode')


def wait_for_enabled(mode: SwitchItemValueMode, enabled: bool, timeout: float = 1) -> None:
    # The mode is enabled/disabled by an event listener which runs in a worker thread.
    # It is executed after the item state has changed, so it has to be waited for separately.
    end = monotonic() + timeout
    while mode.enabled is not enabled and monotonic() < end:
        time.sleep(0.01)
    assert mode.enabled is enabled, mode.enabled


class TestSwitchMode(TestBaseRule):
    """This rule is testing the Parameter implementation"""

    def __init__(self) -> None:
        super().__init__()

        self.add_test('SwitchItemValueMode', self.test_sw_mode)
        self.add_test('SwitchItemValueMode inverted', self.test_sw_mode_inverted)

    def test_sw_mode(self) -> None:
        mm = MultiModeItem.get_create_item(get_random_name('HABApp'))

        with OpenhabTmpItem('Switch') as switch, ItemWaiter(OpenhabItem.get_item(switch.name)) as waiter:
            switch.on()
            waiter.wait_for_state('ON')

            mode = SwitchItemValueMode('test', switch)
            mm.add_mode(0, mode)

            assert mode.enabled is True, mode.enabled

            switch.off()
            waiter.wait_for_state('OFF')
            assert switch.is_off()
            wait_for_enabled(mode, False)

            mode.set_value('asdf')
            assert mode.enabled is False, mode.enabled

            mode.set_value(0)
            assert mode.enabled is False, mode.enabled

        HABAPP_PROVIDER.get_existing(ItemRegistry).pop_item(mm.name)

    def test_sw_mode_inverted(self) -> None:
        mm = MultiModeItem.get_create_item(get_random_name('HABApp'))

        with OpenhabTmpItem('Switch') as switch, ItemWaiter(OpenhabItem.get_item(switch.name)) as waiter:
            switch.on()
            waiter.wait_for_state('ON')

            mode = SwitchItemValueMode('test', switch, invert_switch=True, logger=log)
            mm.add_mode(0, mode)
            assert mode.enabled is False, mode.enabled

            mode.set_value('asdf')
            assert mode.enabled is False, mode.enabled

            mode.set_value(0)
            assert mode.enabled is False, mode.enabled

            switch.off()
            waiter.wait_for_state('OFF')
            wait_for_enabled(mode, True)

        HABAPP_PROVIDER.get_existing(ItemRegistry).pop_item(mm.name)


TestSwitchMode()


class TestRateLimiter(TestBaseRule):
    def __init__(self) -> None:
        super().__init__()

        self.add_test('TestRateLimiter', self.test_rate_limiter)

    def test_rate_limiter(self) -> None:
        r = RateLimiter('test_limiter')
        r.parse_limits('5 in 60s')
        assert r.test_allow()
        assert r.allow()


TestRateLimiter()
