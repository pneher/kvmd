import asyncio
import functools
from re import A

from typing import Callable
from typing import Any


from ...logging import get_logger

from ... import aiotools

from ...yamlconf import Option

from ...validators.basic import valid_number, valid_stripped_string
from ...validators.basic import valid_float_f0
from ...validators.basic import valid_float_f01
from ...validators.net import valid_ip_or_host

from . import BaseUserGpioDriver
from . import GpioDriverOfflineError

from ...plugins.ugpio.intellinet_163682.intellinet_163682 import IPU


# =====
class Plugin(BaseUserGpioDriver):  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        instance_name: str,
        notifier: aiotools.AioNotifier,

        host: str,

        username: str,
        password: str,

        state_poll: float,
    ) -> None:

        super().__init__(instance_name, notifier)

        self.__host = host
        
        self.__username = username
        self.__password = password
          
        self.__initials: dict[int, (bool | None)] = {}
        self.__outlet_states: dict[int, (bool | None)] = {}
        self.__ipu_temp = None
        self.__ipu_current = None
        self.__ipc_humidity = None
        self.__update_notifier = aiotools.AioNotifier()

    @classmethod
    def get_plugin_options(cls) -> dict:
        return {
            "host":         Option("",   type=valid_ip_or_host, if_empty=""),
            
            "username":     Option("admin",   type=valid_stripped_string),
            "password":     Option("admin",   type=valid_stripped_string),

            "state_poll":   Option(10.0, type=valid_float_f01),
        }

    @classmethod
    def get_pin_validator(cls) -> Callable[[Any], Any]:
        return functools.partial(valid_number, min=0, max=7, name="IPU outlet")

    def register_output(self, pin: str, initial: (bool | None)) -> None:
        self.__initials[int(pin)] = initial
        self.__outlet_states[int(pin)] = False

    def prepare(self) -> None:
        self.__pdu = IPU(self.__host, (self.__username, self.__password))
        assert self.__pdu
        for (pin, state) in self.__initials.items():
            if state is not None:
                self.write(pin, state)
        # to get outlet states
        self.run()

    async def run(self) -> None:
        assert self.__pdu
        stats = self.__pdu.status()
        self.__ipu_temp = stats["degree_celcius"]
        self.__ipu_humidity = stats["humidity_percent"]
        self.__ipu_current = stats["current_amperes"]
        for i in range(0,8):
            status = str(stats["outlet_states"][i])
            if status == 'On':
                state = True
            if status == 'Off':
                state = False

            self.__outlet_states[int(i)] = state
        await self.__update_notifier.notify()
                

    async def cleanup(self) -> None:
        await self.__close_device()

    async def read(self, pin: str) -> bool:
        return self.__outlet_states[int(pin)]

    async def write(self, pin: str, state: bool) -> None:
        assert self.__pdu
        # Switch input source command uses 1-based numbering (0x01->PC1...0x10->PC16)
        channel = int(pin) + 1
        assert 1 <= channel <= 8
        if state == True:
            await self.__pdu.enable_outlets(channel)
            await self.__update_notifier.notify()

        if state == False:
            await self.__pdu.disable_outlets(channel)
            await self.__update_notifier.notify()


    # =====

    async def __close_device(self) -> None:
        self.__pdu = None

    # =====

    def __str__(self) -> str:
        return f"IPU_163682({self._instance_name})"

    __repr__ = __str__
