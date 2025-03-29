from __future__ import annotations

import typing

from .base_event import OpenhabEvent

if typing.TYPE_CHECKING:
    from typing_extensions import Self


class ChannelTriggeredEvent(OpenhabEvent):
    """
    :ivar str name:
    :ivar str event:
    :ivar str channel:
    """

    name: str
    event: str
    channel: str

    def __init__(self, name: str = '', event: str = '', channel: str = '') -> None:
        super().__init__()

        self.name: str = name
        self.event: str = event
        self.channel: str = channel

    @classmethod
    def from_dict(cls, topic: str, payload: dict) -> Self:
        return cls(topic[17:-10], payload['event'], payload['channel'])

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} name: {self.name}, event: {self.event}>'


class ChannelDescriptionChangedEvent(OpenhabEvent):
    """
    :ivar str name:
    :ivar str field:
    :ivar str value:
    """

    name: str
    field: str
    value: str

    def __init__(self, name: str = '', field: str = '', value: str = '') -> None:
        super().__init__()

        self.name: str = name
        self.field: str = field
        self.value: str = value

    @classmethod
    def from_dict(cls, topic: str, payload: dict) -> Self:
        return cls(topic[17:-19], payload['field'], payload['value'])

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} name: {self.name}, field: {self.field}>'
