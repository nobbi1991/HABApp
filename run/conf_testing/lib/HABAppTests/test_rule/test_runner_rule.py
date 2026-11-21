import asyncio
import logging
from time import monotonic
from typing import Final

import HABApp
from HABApp.core.const.topics import TOPIC_FILES
from HABApp.core.events import EventFilter
from HABApp.core.events.habapp_events import RequestFileLoadEvent
from HABApp.core.lib.asyncio import AsyncioProvider
from HABApp.core.provider import HABAPP_PROVIDER
from HABApp.core.shutdown import ShutdownInfo
from HABApp.core.wrapper import ignore_exception
from HABAppTests.test_rule.test_case import TestResult, TestResultStatus

from .report import write_reports
from .test_rule import TestBaseRule, TestRuleStatus
import sys

log = logging.getLogger('HABApp.Tests')


class TestRunnerRule(HABApp.Rule):
    def __init__(self) -> None:
        super().__init__()

        self.listen_event(TOPIC_FILES, self._file_event, EventFilter(event_class=RequestFileLoadEvent))
        self.countdown = self.run.countdown(3, self._files_const)
        self.countdown.reset()

        self.task: Final = HABAPP_PROVIDER.get_existing(AsyncioProvider).create_single_task(self._run_tests)

    async def _file_event(self, event) -> None:
        self.countdown.reset()

    async def _files_const(self) -> None:
        self.task.start_if_not_running()

    def _get_next_rule(self) -> TestBaseRule | None:
        all_rules = [r for r in self.get_rule(None) if isinstance(r, TestBaseRule)]
        for rule in all_rules:
            if rule._rule_status is TestRuleStatus.CREATED:
                rule._rule_status = TestRuleStatus.PENDING
            if rule._rule_status is TestRuleStatus.PENDING:
                return rule
        return None

    async def _wait_until_item_events_work(self, shutdown: ShutdownInfo, stable_for: float = 30,
                                           timeout: float = 240) -> None:
        """Wait until HABApp receives the events for items which were created in openHAB.

        Some openHAB versions (e.g. 4.3) close the websocket some seconds after the startup. HABApp needs
        around a minute to notice this and to reconnect. Items which are created in this time are not known to
        HABApp, so all tests that create items would fail.
        Because the websocket is closed after the first successful check, the check has to succeed
        for ``stable_for`` seconds without interruption.
        """
        from HABAppTests.openhab_tmp_item import AsyncOpenhabTmpItem  # noqa: PLC0415

        started = monotonic()
        ok_since: float | None = None
        while not shutdown.is_requested():
            item = AsyncOpenhabTmpItem('String')
            try:
                await item.create_item()
                ready = True
            except Exception as e:  # noqa: BLE001
                log.debug(f'Item events do not work yet: {e!r}')
                ready = False
            finally:
                try:
                    await item.remove()
                except Exception as e:  # noqa: BLE001
                    log.debug(f'Could not remove item {item.name}: {e!r}')

            now = monotonic()
            if not ready:
                ok_since = None
            elif ok_since is None:
                ok_since = now
            elif now - ok_since >= stable_for:
                log.info(f'HABApp receives item events from openHAB (waited {now - started:.0f}s)')
                return

            if now - started > timeout:
                log.warning(f'HABApp does not receive item events from openHAB after {now - started:.0f}s! '
                            f'Tests which create items will fail.')
                return

            await asyncio.sleep(2)

    @ignore_exception
    async def _run_tests(self) -> None:
        results: list[TestResult] = []

        # todo: Implement this properly
        shutdown = await HABAPP_PROVIDER.get(ShutdownInfo)

        await self._wait_until_item_events_work(shutdown)

        while (rule := self._get_next_rule()) is not None and not shutdown.is_requested():
            results.extend(await rule.run_test_cases())

        await self.tests_done(results)

        skipped = tuple(x for x in results if x.state is TestResultStatus.SKIPPED)
        passed  = tuple(x for x in results if x.state is TestResultStatus.PASSED)
        warning = tuple(x for x in results if x.state is TestResultStatus.WARNING)
        failed  = tuple(x for x in results if x.state is TestResultStatus.FAILED)
        error   = tuple(x for x in results if x.state is TestResultStatus.ERROR)

        def plog(msg: str) -> None:
            print(msg)
            log.info(msg)

        parts = [f'{len(results)} executed', f'{len(passed)} passed']
        if skipped:
            parts.append(f'{len(skipped)} skipped')
        if warning:
            parts.append(f'{len(warning)} warning{"" if len(warning) == 1 else "s"}')
        parts.append(f'{len(failed)} failed')
        if error:
            parts.append(f'{len(error)} error{"" if len(error) == 1 else "s"}')

        plog('')
        plog('-' * 120)
        plog(', '.join(parts))

        for file in write_reports(results, HABApp.CONFIG.directories.logging):
            plog(f'Report written to {file}')

        sys.exit(1 if failed or error else 0)

    async def tests_done(self, results: list[TestResult]) -> None:
        raise NotImplementedError()
