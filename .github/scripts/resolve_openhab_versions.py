"""Resolve the newest patch version of the given openHAB minor versions from Docker Hub.

openHAB does not publish floating tags like ``5.2``, only ``latest`` and the exact versions.
So for every given minor version (e.g. ``5.2``) the highest release tag (``5.2.5``) is looked up.

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
    url: str | None = URL.format(name=f'{minor}.')
    tags: set[str] = set()
    while url:
        with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310
            data = json.load(response)
        tags.update(entry['name'] for entry in data['results'])
        url = data.get('next')
    return tags


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

    matrix = json.dumps({'openhab': [newest_patch(minor) for minor in minors]})
    print(matrix)

    if output := os.environ.get('GITHUB_OUTPUT'):
        with open(output, 'a', encoding='utf-8') as f:
            f.write(f'matrix={matrix}\n')


if __name__ == '__main__':
    main(sys.argv[1:])
