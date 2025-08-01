import sys
from enum import Enum
from typing import Final, Literal, TypeAlias

from whenever import Instant


class _MissingType(Enum):
    _MISSING = object()

    def __repr__(self) -> str:
        return '<Missing>'


MISSING: Final = _MissingType._MISSING
MISSING_TYPE: TypeAlias = Literal[_MissingType._MISSING]

STARTUP_INSTANT: Final = Instant.now()

# Python Versions for feature control
PYTHON_311: Final = sys.version_info >= (3, 11)
PYTHON_312: Final = sys.version_info >= (3, 12)
PYTHON_313: Final = sys.version_info >= (3, 13)
PYTHON_314: Final = sys.version_info >= (3, 14)


# In python 3.11 there were changes to MyEnum(str, Enum), so we have to use the StrEnum
# https://docs.python.org/3/library/enum.html#enum.StrEnum
if PYTHON_311:
    # noinspection PyUnresolvedReferences
    from enum import StrEnum
else:
    class StrEnum(str, Enum):
        pass
