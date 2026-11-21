"""Resolve the openHAB versions for the build matrix from Docker Hub.

openHAB does not publish floating tags like ``5.2``, only ``latest`` and the exact versions.
So for every given minor version (e.g. ``5.2``) the highest release tag (``5.2.5``) is looked up.

Additionally the newest milestone / release candidate (e.g. ``5.3.0.M5``) is added if there is one.
It is only used as long as there is no final release (``5.3.0``) for it. Snapshots are not used.

Usage: resolve_openhab_versions.py 4.3 5.0 5.1 5.2
Prints a json object that can be used as a build matrix, e.g. ``{"openhab": ["4.3.11", "5.0.3"]}``.
Writes ``matrix=<json>`` to ``$GITHUB_OUTPUT`` if it is set.
"""
import json
import os
import re
import sys
import urllib.request


URL = 'https://hub.docker.com/v2/repositories/openhab/openhab/tags?page_size=100&name={name}'


def get_tags(minor: str) -> set[str]:
    url: str | None = URL.format(name=minor if minor.startswith('.') or minor.count('.') > 1 else f'{minor}.')
    tags: set[str] = set()
    while url:
        with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310
            data = json.load(response)
        tags.update(entry['name'] for entry in data['results'])
        url = data.get('next')
    return tags


def newest_prerelease() -> str | None:
    """Newest milestone or release candidate (``5.3.0.M5``, ``5.2.0.RC2``) of a version which is not released yet"""
    pattern = re.compile(r'(\d+)\.(\d+)\.(\d+)\.(M|RC)(\d+)')  # no variants (-alpine, ...) and no snapshots

    versions: dict[tuple[int, int, int], list[tuple[int, int, str]]] = {}
    for name in ('.M', '.RC'):
        for tag in get_tags(name):
            if m := pattern.fullmatch(tag):
                major, minor, patch, kind, number = m.groups()
                # M1 < M2 < ... < RC1 < RC2
                versions.setdefault((int(major), int(minor), int(patch)), []).append(
                    (0 if kind == 'M' else 1, int(number), tag)
                )

    if not versions:
        return None

    # Only the newest version is relevant: if it has a final release, all older ones are released, too.
    newest = max(versions)
    name = '.'.join(map(str, newest))
    if name in get_tags(name):
        return None
    return max(versions[newest])[2]


def newest_patch(minor: str) -> str:
    pattern = re.compile(rf'{re.escape(minor)}\.(\d+)')  # only releases, no milestones, RCs or variants (-alpine, ...)
    patches = [int(m.group(1)) for tag in get_tags(minor) if (m := pattern.fullmatch(tag))]
    if not patches:
        msg = f'No release found for openHAB {minor}'
        raise ValueError(msg)
    return f'{minor}.{max(patches)}'


def main(minors: list[str]) -> None:
    if not minors:
        msg = 'Pass at least one minor version, e.g. 5.2'
        raise SystemExit(msg)

    versions = [newest_patch(minor) for minor in minors]
    if prerelease := newest_prerelease():
        versions.append(prerelease)

    matrix = json.dumps({'openhab': versions})
    print(matrix)

    if output := os.environ.get('GITHUB_OUTPUT'):
        with open(output, 'a', encoding='utf-8') as f:
            f.write(f'matrix={matrix}\n')


if __name__ == '__main__':
    main(sys.argv[1:])
