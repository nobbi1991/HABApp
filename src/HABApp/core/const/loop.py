import asyncio
import os
import sys
import threading


# we can have subprocesses (https://docs.python.org/3/library/asyncio-platforms.html#subprocess-support-on-windows)
# or mqtt support (https://github.com/sbtinstruments/aiomqtt#note-for-windows-users)
# but not both. For testing, it makes sense to use mqtt support as a default
if (sys.platform.lower() == 'win32' or os.name.lower() == 'nt') and os.environ.get('HABAPP_NO_MQTT') is None:
    from asyncio import WindowsSelectorEventLoopPolicy, set_event_loop_policy
    set_event_loop_policy(WindowsSelectorEventLoopPolicy())

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

loop.set_debug(True)
loop.slow_callback_duration = 0.02

LOOP_THREAD_ID = None

async def get_loop_thread_id():
    global LOOP_THREAD_ID
    LOOP_THREAD_ID =  threading.get_ident()

asyncio.run(get_loop_thread_id())