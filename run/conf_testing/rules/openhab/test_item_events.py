import time
from time import monotonic
from typing import Final

from HABAppTests import (
    EventWaiter,
    ItemWaiter,
    OpenhabTmpItem,
    TestBaseRule,
    get_openhab_item_names,
    get_openhab_test_commands,
    get_openhab_test_states,
)

from HABApp.core.events import ValueUpdateEventFilter
from HABApp.openhab.events import (
    ItemCommandEvent,
    ItemCommandEventFilter,
    ItemStateChangedEvent,
    ItemStateUpdatedEvent,
)
from HABApp.openhab.items import NumberItem


class TestOpenhabEventTypes(TestBaseRule):
    """This rule is testing the OpenHAB data types by posting values and checking the events"""

    def __init__(self) -> None:
        super().__init__()

        for oh_type in get_openhab_item_names():
            self.add_test(
                f'{oh_type} updates', self.test_item, oh_type,
                get_openhab_test_states(oh_type), get_openhab_test_commands(oh_type)
            )

        dimensions = {
            'Length': 'm', 'Temperature': '°C', 'Pressure': 'hPa', 'Speed': 'km/h', 'Intensity': 'W/m²', 'Angle': '°',
            'Dimensionless': '',
        }
        for name, unit in dimensions.items():
            self.add_test(f'Quantity {name} events', self.test_quantity_type_events, name, unit)

        # Before openHAB 5.1 the REST API ignores the source parameter and the ItemStateChangedEvent
        # does not contain the source of the update which caused the change.
        self.add_test('EventSourceCommandHttp', self.test_event_source_command, 'http', min_openhab_version=(5, 1))
        self.add_test('EventSourceCommandWs', self.test_event_source_command, 'websocket')
        self.add_test('EventSourceUpdateHttp', self.test_event_source_update, 'http', min_openhab_version=(5, 1))
        self.add_test('EventSourceUpdateWs', self.test_event_source_update, 'websocket', min_openhab_version=(5, 1))

    def test_item(self, item_type: str, test_states: tuple, test_commands: tuple) -> None:
        item_name = f'{item_type}_value_test'

        with (OpenhabTmpItem(item_type, item_name) as item,
              EventWaiter(item_name, ValueUpdateEventFilter()) as state_waiter,
              EventWaiter(item_name, ItemCommandEventFilter()) as command_waiter):

            # check that the event is properly received
            for post_value, receive_value in test_states:
                item.oh_post_update(post_value)
                state_waiter.wait_for_event(value=receive_value)

            # use oh_send_command to send commands
            for send_command, receive_value in test_commands:
                item.oh_send_command(send_command)
                command_waiter.wait_for_event(value=receive_value)

            # use command_value to send commands
            for send_command, receive_value in test_commands:
                item.command_value(send_command)
                command_waiter.wait_for_event(value=receive_value)

    def test_quantity_type_events(self, dimension, unit) -> None:
        item_name = f'{dimension}_event_test'
        with OpenhabTmpItem(f'Number:{dimension}', item_name) as item, \
                EventWaiter(item_name, ValueUpdateEventFilter()) as event_waiter, \
                ItemWaiter(item) as item_waiter:

            for post_func in (item.oh_post_update, lambda x: self.openhab.post_update(item_name, x)):

                for post_value, receive_value in get_openhab_test_states('Number'):
                    if unit and post_value is not None:
                        post_value = f'{post_value} {unit}'  # noqa: PLW2901

                    post_func(post_value)
                    event_waiter.wait_for_event(value=receive_value)
                    item_waiter.wait_for_state(receive_value)

    def test_event_source_command(self, transport: str) -> None:
        source_suffix: Final = '' if transport == 'websocket' else '=>org.openhab.core.io.rest$asdf'

        with OpenhabTmpItem('Number') as item, EventWaiter(item.name, ItemCommandEventFilter()) as event_waiter:
            # test manual source
            self.oh.send_command(item.name, 5, source='TestSource', transport=transport)
            event: ItemCommandEvent = event_waiter.wait_for_event()
            assert event.source == 'HABApp.TestSource' + source_suffix

            # automatic source
            self.oh.send_command(item.name, 6, transport=transport)
            event: ItemCommandEvent = event_waiter.wait_for_event()
            assert event.source == 'HABApp.TestOpenhabEventTypes' + source_suffix

    def test_event_source_update(self, transport: str) -> None:
        source_suffix: Final = '' if transport == 'websocket' else '=>org.openhab.core.io.rest$asdf'

        events: list[ItemStateUpdatedEvent | ItemStateChangedEvent] = []

        def _on_event(event: ItemStateUpdatedEvent | ItemStateChangedEvent) -> None:
            assert isinstance(event, (ItemStateUpdatedEvent, ItemStateChangedEvent))
            events.append(event)

        with OpenhabTmpItem('Number') as item:

            NumberItem.get_item(item.name).listen_event(_on_event)

            # test manual source
            value_1: Final = 5
            self.oh.post_update(item.name, value_1, source='TestSource_1', transport=transport)
            self.oh.post_update(item.name, value_1, source='TestSource_2', transport=transport)

            # automatic source
            value_2: Final = 6
            self.oh.post_update(item.name, value_2, transport=transport)
            self.oh.post_update(item.name, value_2, transport=transport)

            # The callbacks run in worker threads, so the order in which they append to the list is not
            # guaranteed to be the order in which the events were received -> wait for all of them
            end = monotonic() + 2
            while len(events) < 6 and monotonic() < end:  # noqa: PLR2004
                time.sleep(0.01)
            time.sleep(0.1)  # make sure no additional events arrive

        assert len(events) == 6, events  # noqa: PLR2004

        updated = [e for e in events if isinstance(e, ItemStateUpdatedEvent)]
        changed = [e for e in events if isinstance(e, ItemStateChangedEvent)]

        # updated events have no source
        assert len(updated) == 4, updated  # noqa: PLR2004
        assert sorted(e.value for e in updated) == [value_1, value_1, value_2, value_2]
        for e in updated:
            assert e.source is None

        assert len(changed) == 2, changed  # noqa: PLR2004
        c1, c2 = sorted(changed, key=lambda x: x.value)

        assert c1.source == 'HABApp.TestSource_1' + source_suffix
        assert c1.source.origin == ('HABApp', 'TestSource_1')
        assert str(c1.source.origin) == 'HABApp.TestSource_1'
        assert c1.value == value_1

        assert c2.source == 'HABApp.TestOpenhabEventTypes' + source_suffix
        assert c2.value == value_2

TestOpenhabEventTypes()
