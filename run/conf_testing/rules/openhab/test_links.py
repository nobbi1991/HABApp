from HABAppTests import TestBaseRule
from HABAppTests.utils import find_astro_sun_thing, run_coro

from HABApp.openhab.connection.handler.func_async import async_get_link, async_get_links


class OpenhabLinkApi(TestBaseRule):

    def __init__(self) -> None:
        super().__init__()
        self.add_test('AllLinks', self.wrap_async, self.api_get_links)

    def wrap_async(self, coro, *args, **kwargs) -> None:
        # create valid data
        run_coro(coro(*args, **kwargs))

    def set_up(self) -> None:
        self.thing = self.openhab.get_thing(find_astro_sun_thing())

    async def api_get_links(self) -> None:
        objs = await async_get_links()
        assert objs

        obj = objs[0]

        single = await async_get_link(obj.item, obj.channel)
        assert single == obj


OpenhabLinkApi()
