from typing import NoReturn, Any

from HABApp.openhab.errors import MapTransformationError


class MapTransformation(dict):
    def __init__(self, *args, name: str) -> None:
        super().__init__(*args)
        self._name = name

    def __repr__(self, additional: str = '') -> str:
        return f'<{self.__class__.__name__} name={self._name} items={super().__repr__()}{additional:s}>'


class MapTransformationWithDefault(MapTransformation):
    def __init__(self, *args, default: Any, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._default = default

    def __missing__(self, key: str) -> Any:
        return self._default

    def __repr__(self, additional: str = '') -> str:
        return super().__repr__(f', default={self._default}{additional}')

    def get(self, key: str, default: Any | None = None) -> NoReturn:
        raise MapTransformationError(f'Mapping is already defined with a default: "{self._default}"')
