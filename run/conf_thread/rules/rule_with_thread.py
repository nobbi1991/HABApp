import threading

import HABApp

class RuleWithTread(HABApp.Rule):

    def __init__(self):
        super().__init__()

        self._str_item=HABApp.openhab.items.StringItem.get_item("I00_Thread_1")

        self._timer = threading.Timer(10, self._cb_timer)
        print(msg:="Start Timer")
        self._str_item.oh_send_command(msg)

        self._timer.start()
        print(msg:="Started Timer")
        self._str_item.oh_send_command(msg)


    def _cb_timer(self):
        print(msg:="Timer End")
        self._str_item.oh_send_command(msg)


RuleWithTread()