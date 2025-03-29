from typing import Any, Final


class ValueUpdateEvent:
    """
    :ivar str name:
    :ivar Any value:
    """

    name: Final[str]
    value: Final[Any]

    def __init__(self, name: str, value: Any) -> None:
        self.name = name
        self.value = value

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} name: {self.name:s}, value: {self.value}>'


class ValueChangeEvent:
    """
    :ivar str name:
    :ivar Any value:
    :ivar Any old_value:
    """

    name: Final[str]
    value: Final[Any]
    old_value: Final[Any]

    def __init__(self, name: str, value: Any, old_value: Any) -> None:
        self.name = name
        self.value = value
        self.old_value = old_value

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} name: {self.name:s}, value: {self.value}, old_value: {self.old_value}>'


class ValueCommandEvent:
    """
    :ivar str name:
    :ivar Any value:
    """

    name: Final[str]
    value: Final[Any]

    def __init__(self, name: str, value: Any) -> None:
        self.name = name
        self.value = value

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} name: {self.name:s}, value: {self.value}>'


class ItemNoChangeEvent:
    """
    :ivar str name:
    :ivar int | float seconds:
    """

    name: Final[str]
    seconds: Final[int | float]

    def __init__(self, name: str, seconds: int | float) -> None:
        self.name = name
        self.seconds = seconds

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} name: {self.name:s}, seconds: {self.seconds}>'


class ItemNoUpdateEvent:
    """
    :ivar str               name:
    :ivar int | float seconds:
    """
    name: Final[str]
    seconds: Final[int | float]

    def __init__(self, name: str, seconds: int | float) -> None:
        self.name = name
        self.seconds = seconds

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} name: {self.name:s}, seconds: {self.seconds}>'
