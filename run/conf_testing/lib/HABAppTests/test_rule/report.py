"""Write test reports (JUnit xml and markdown summary) from the test results."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING
from xml.etree import ElementTree as ET

from HABAppTests.test_rule.test_result import TestResultStatus

if TYPE_CHECKING:
    from collections.abc import Iterable

    from HABAppTests.test_rule.test_result import TestResult


def _name(result: TestResult) -> str:
    return f'{result.group_name}.{result.test_name}'


def _first_msg(result: TestResult) -> str:
    msg = next((m for m in result.msgs if m.strip()), '')
    if msg.strip() in ('', 'Exception:'):
        # e.g. a plain assert without a message -> show the last line of the traceback instead
        msg = next((d.strip() for d in reversed(result.details) if d.strip() and set(d.strip()) != {'-'}), msg)
    return msg


def _details(result: TestResult) -> str:
    return '\n'.join([*result.msgs, *result.details]).strip()


def build_junit_xml(results: Iterable[TestResult]) -> ET.ElementTree:
    results = list(results)
    groups: dict[str, list[TestResult]] = {}
    for r in results:
        groups.setdefault(r.group_name, []).append(r)

    count = {s: sum(r.state is s for r in results) for s in TestResultStatus}
    root = ET.Element('testsuites', {
        'name': 'HABApp openHAB tests',
        'tests': str(len(results)),
        'failures': str(count[TestResultStatus.FAILED]),
        'errors': str(count[TestResultStatus.ERROR]),
        'skipped': str(count[TestResultStatus.SKIPPED]),
    })

    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    for group, group_results in groups.items():
        suite = ET.SubElement(root, 'testsuite', {
            'name': group,
            'tests': str(len(group_results)),
            'failures': str(sum(r.state is TestResultStatus.FAILED for r in group_results)),
            'errors': str(sum(r.state is TestResultStatus.ERROR for r in group_results)),
            'skipped': str(sum(r.state is TestResultStatus.SKIPPED for r in group_results)),
            'timestamp': timestamp,
        })
        for r in group_results:
            case = ET.SubElement(suite, 'testcase', {'classname': group, 'name': r.test_name})
            if r.state is TestResultStatus.SKIPPED:
                ET.SubElement(case, 'skipped')
            elif r.state in (TestResultStatus.FAILED, TestResultStatus.ERROR):
                tag = 'failure' if r.state is TestResultStatus.FAILED else 'error'
                node = ET.SubElement(case, tag, {'message': _first_msg(r)})
                node.text = _details(r)
            elif r.state is TestResultStatus.WARNING:
                ET.SubElement(case, 'system-out').text = _details(r)

    ET.indent(root)
    return ET.ElementTree(root)


def build_markdown(results: Iterable[TestResult]) -> str:
    results = list(results)
    by_state = {s: [r for r in results if r.state is s] for s in TestResultStatus}

    lines = ['# HABApp openHAB test report', '']
    lines.append('| Executed | Passed | Skipped | Warnings | Failed | Errors |')
    lines.append('|---:|---:|---:|---:|---:|---:|')
    lines.append(
        f'| {len(results)} | {len(by_state[TestResultStatus.PASSED])} | {len(by_state[TestResultStatus.SKIPPED])} '
        f'| {len(by_state[TestResultStatus.WARNING])} | {len(by_state[TestResultStatus.FAILED])} '
        f'| {len(by_state[TestResultStatus.ERROR])} |'
    )
    lines.append('')

    bad = [*by_state[TestResultStatus.FAILED], *by_state[TestResultStatus.ERROR]]
    if bad:
        lines += ['## Failed tests', '', '| Test | Status | Message |', '|---|---|---|']
        for r in bad:
            msg = _first_msg(r).replace('|', '\|')
            lines.append(f'| `{_name(r)}` | {r.state.name.lower()} | {msg} |')
        lines.append('')
        for r in bad:
            lines += [f'<details><summary><code>{_name(r)}</code> ({r.state.name.lower()})</summary>', '', '```text',
                      _details(r) or '(no details)', '```', '', '</details>', '']

    for title, state in (('Warnings', TestResultStatus.WARNING), ('Skipped tests', TestResultStatus.SKIPPED)):
        if by_state[state]:
            lines += [f'## {title}', '']
            lines += [f'- `{_name(r)}`' + (f': {_first_msg(r)}' if _first_msg(r) else '') for r in by_state[state]]
            lines.append('')

    return '\n'.join(lines).rstrip() + '\n'


def write_reports(results: Iterable[TestResult], folder: Path) -> list[Path]:
    results = list(results)
    folder.mkdir(parents=True, exist_ok=True)

    xml_file = folder / 'test_report.xml'
    build_junit_xml(results).write(xml_file, encoding='utf-8', xml_declaration=True)

    md_file = folder / 'test_report.md'
    md_file.write_text(build_markdown(results), encoding='utf-8')
    return [xml_file, md_file]
