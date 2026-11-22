"""Summarize the JUnit test reports of all openHAB versions as markdown.

Usage: summarize_test_reports.py <folder with the downloaded artifacts> <openHAB version> [<openHAB version> ...]

For every version the report ``<folder>/logs-openhab-<version>-attempt-<n>/HABApp/test_report.xml`` is read.
If a job was re-run there is one folder per attempt: the report of the latest attempt is used.
The markdown is printed and appended to ``$GITHUB_STEP_SUMMARY`` if it is set.
"""
import os
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


OK, WARNING, FAILED, ERROR, SKIPPED = 'ok', 'warning', 'failed', 'error', 'skipped'
SYMBOLS = {OK: '✅', WARNING: '⚠️', FAILED: '❌', ERROR: '❌', SKIPPED: '⏭️', None: '➖'}


def find_report(folder: Path, version: str) -> Path | None:
    pattern = re.compile(rf'logs-openhab-{re.escape(version)}-attempt-(\d+)')

    attempts: dict[int, Path] = {}
    for artifact in folder.iterdir():
        if artifact.is_dir() and (m := pattern.fullmatch(artifact.name)):
            attempts[int(m.group(1))] = artifact

    # The latest attempt is the result of the job, even if it has no report (e.g. openHAB did not start)
    if not attempts:
        return None
    file = attempts[max(attempts)] / 'HABApp' / 'test_report.xml'
    return file if file.is_file() else None


def read_report(folder: Path, version: str) -> dict[str, str] | None:
    if (file := find_report(folder, version)) is None:
        return None

    results: dict[str, str] = {}
    for case in ET.parse(file).getroot().iter('testcase'):
        name = f'{case.get("classname")}.{case.get("name")}'
        if case.find('failure') is not None:
            results[name] = FAILED
        elif case.find('error') is not None:
            results[name] = ERROR
        elif case.find('skipped') is not None:
            results[name] = SKIPPED
        elif case.find('system-out') is not None:  # the report writes warnings as system-out
            results[name] = WARNING
        else:
            results[name] = OK
    return results


def build_markdown(reports: dict[str, dict[str, str] | None]) -> str:
    lines = ['# Summary of all openHAB versions', '']

    lines += ['| openHAB | Executed | Passed | Skipped | Warnings | Failed | Errors |', '|---|---:|---:|---:|---:|---:|---:|']
    for version, report in reports.items():
        if report is None:
            lines.append(f'| {version} | no report (job failed, cancelled or timed out) | | | | | |')
            continue
        values = list(report.values())
        lines.append(
            f'| {version} | {len(values)} | {values.count(OK)} | {values.count(SKIPPED)} | {values.count(WARNING)} '
            f'| {values.count(FAILED)} | {values.count(ERROR)} |'
        )
    lines.append('')

    # tests which fail in at least one version
    names: list[str] = []
    for report in reports.values():
        for name, state in (report or {}).items():
            if state in (FAILED, ERROR) and name not in names:
                names.append(name)

    if not names:
        lines.append('No failed tests.' if all(reports.values()) else 'No failed tests in the available reports.')
        return '\n'.join(lines) + '\n'

    lines += ['## Failed tests', '', f'| Test | {" | ".join(reports)} |', '|---|' + '---|' * len(reports)]
    for name in names:
        cells = [SYMBOLS[None if report is None else report.get(name)] for report in reports.values()]
        lines.append(f'| `{name}` | {" | ".join(cells)} |')
    lines += ['', f'{SYMBOLS[OK]} passed, {SYMBOLS[WARNING]} warning, {SYMBOLS[FAILED]} failed or error, {SYMBOLS[SKIPPED]} skipped, '
                  f'{SYMBOLS[None]} not available (no report or test not part of the run)']
    return '\n'.join(lines) + '\n'


def main(folder: str, versions: list[str]) -> None:
    reports = {version: read_report(Path(folder), version) for version in versions}
    markdown = build_markdown(reports)
    print(markdown)

    if output := os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(output, 'a', encoding='utf-8') as f:
            f.write(markdown)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2:])
