from __future__ import annotations

import collections
import logging
import runpy
from typing import TYPE_CHECKING

import HABApp
from HABApp.core.internals import get_current_context, wrap_func
from HABApp.rule.rule_hook import HABAppRuleHook


if TYPE_CHECKING:
    from pathlib import Path

    from HABApp import Rule
    from HABApp.rule_manager import RuleManager


log = logging.getLogger('HABApp.Rules')


class RuleFile:
    def __init__(self, rule_manager: RuleManager, name: str, path: Path) -> None:
        self.rule_manager = rule_manager

        self.name: str = name
        self.path: Path = path

        self.rules: dict[str, Rule] = {}
        self.class_ctr: dict[str, int] = collections.defaultdict(lambda: 1)

    def suggest_rule_name(self, obj: Rule) -> str:

        # if there is already a name set we make no suggestion
        if getattr(obj, 'rule_name', '') != '':
            return obj.rule_name.replace('ü', 'ue').replace('ö', 'oe').replace('ä', 'ae')

        name = obj.__class__.__name__
        found = self.class_ctr[name]
        self.class_ctr[name] += 1

        return f'{name:s}.{found:d}' if found > 1 else f'{name:s}'

    async def check_all_rules(self) -> None:
        for rule in self.rules.values():
            await get_current_context(rule).check_rule()

    async def unload(self) -> None:

        # If we don't have any rules we can not unload
        if not self.rules:
            return None

        # unload all registered callbacks
        for rule in self.rules.values():
            await get_current_context(rule).unload_rule()

        log.debug(f'File {self.name} successfully unloaded!')
        return None

    def __process_tc(self, tb: list[str]) -> list[str]:
        tb.insert(0, f'Could not load {self.path}!')
        return [line.replace('<module>', self.path.name) for line in tb]

    def create_rules(self, created_rules: list) -> None:

        rule_hook = HABAppRuleHook(created_rules.append, self.suggest_rule_name, self.rule_manager.runtime, self)

        # It seems like python 3.8 doesn't allow path like objects anymore:
        # https://github.com/spacemanspiff2007/HABApp/issues/111
        with rule_hook:
            runpy.run_path(str(self.path), run_name=str(self.path), init_globals=rule_hook.in_dict())

    async def load(self) -> bool:

        created_rules: list[Rule] = []

        ign = HABApp.core.wrapper.ExceptionToHABApp(logger=log)
        ign.proc_tb = self.__process_tc

        with ign:
            await wrap_func(self.create_rules).async_run(created_rules)

        if ign.raised_exception:
            # unload all rule instances which might have already been created otherwise they might
            # still listen to events and do stuff
            for rule in created_rules:
                with ign:
                    await get_current_context(rule).unload_rule()
            return False

        if not created_rules:
            log.warning(f'Found no instances of HABApp.Rule in {self.path!s}')
            return True

        with ign:
            for rule in created_rules:
                # ensure that we have a rule name
                rule.rule_name = self.suggest_rule_name(rule)

                # rule name must be unique for every file
                if rule.rule_name in self.rules:
                    msg = f'Rule name must be unique!\n"{rule.rule_name}" is already used!'
                    raise ValueError(msg)

                self.rules[rule.rule_name] = rule
                log.info(f'Added rule "{rule.rule_name}" from {self.name}')

        if ign.raised_exception:
            # unload all rule instances which might have already been created otherwise they might
            # still listen to events and do stuff
            for rule in created_rules:
                with ign:
                    await get_current_context(rule).unload_rule()
            return False

        return True
