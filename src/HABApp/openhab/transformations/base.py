import logging
from typing import Any, Final, Generic, TypeVar, NoReturn


T = TypeVar('T')

log = logging.getLogger('HABApp.openhab.transform')


class TransformationFactoryBase(Generic[T]):
    def __init__(self, registry: 'TransformationRegistryBase') -> None:
        self._registry: Final = registry

    def __repr__(self) -> str:
        return f'<{self._registry.name.title()}{self.__class__.__name__}>'

    def __getitem__(self, key: str) -> T:
        return self._registry.get(key)


def sort_order(uid: str) -> tuple[int, str, str]:
    if '.' in uid:
        # created through file
        name, ext = uid.rsplit('.', 1)
        return 0, ext, name
    else:
        # UI created
        name, ext = uid.rsplit(':', 1)
        return 1, name, ext


class TransformationRegistryBase:
    objs: dict[str, Any]

    def __init__(self, name: str) -> None:
        self.name: Final = name

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} {" ".join(self.available())}'

    def available(self) -> tuple[str, ...]:
        return tuple(sorted(self.objs.keys(), key=sort_order))

    def get(self, name: str) -> NoReturn:
        raise NotImplementedError()

    def set(self, name: str, configuration: dict) -> NoReturn:
        raise NotImplementedError()

    def clear(self) -> None:
        self.objs.clear()
