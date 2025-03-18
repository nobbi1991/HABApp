import asyncio
import logging
import sys

import HABApp
from HABApp.__check_dependency_packages__ import check_dependency_packages, setup_uvloop_if_available
from HABApp.__cmd_args__ import find_config_folder, parse_args
from HABApp.__debug_info__ import print_debug_info
from HABApp.__splash_screen__ import show_start_screen


def init_stuff_temp() -> None:



    # 4. Core features
    import HABApp.core

    # This holds only textual references to other objects so we can import this before everything else
    import HABApp.rule_ctx


    # Import the rest
    import HABApp.mqtt
    import HABApp.openhab
    import HABApp.rule
    import HABApp.runtime


    import HABApp.util
    from HABApp.rule import Rule
    from HABApp.parameters import Parameter, DictParameter



def main() -> int | str:

    setup_uvloop_if_available()

    # We do this here, so we can print a nice error message. Otherwise the corresponding
    # module import will fail somewhere in the middle of the startup process
    check_dependency_packages()

    show_start_screen()


    init_stuff_temp()

    # This has to be done before we create HABApp because of the possible sleep time
    args = parse_args()

    if HABApp.__cmd_args__.DO_DEBUG:
        print_debug_info()
        sys.exit(0)

    log = logging.getLogger('HABApp')

    try:
        cfg_folder = find_config_folder(args.config)

        # see if we have user code (e.g. for additional logging configuration or additional setup)
        try:
            import HABAppUser  # noqa: F401
        except ModuleNotFoundError:
            pass

        # Shutdown handler for graceful shutdown
        HABApp.core.shutdown.register_signal_handler()

        app = HABApp.runtime.Runtime()
        HABApp.core.const.loop.create_task(app.start(cfg_folder))
        HABApp.core.const.loop.run_forever()
    except Exception as e:
        for line in HABApp.core.lib.exceptions.format_exception(e):
            log.error(line)
            print(e)
        return str(e)
    finally:
        # Sleep to allow underlying connections of aiohttp to close
        # https://aiohttp.readthedocs.io/en/stable/client_advanced.html#graceful-shutdown
        HABApp.core.const.loop.run_until_complete(asyncio.sleep(1))

        asyncio.set_event_loop(None)
        HABApp.core.const.loop.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
