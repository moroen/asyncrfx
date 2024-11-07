from time import sleep
import asyncio

import logging
import RFXtrx

from typing import AsyncGenerator, List

from .transports import AsyncTransport

logger = logging.getLogger(__name__)

cmd_reset = b'\x0D\x00\x00\x00\x00\x00\x00' b'\x00\x00\x00\x00\x00\x00\x00'
cmd_getStatus = b'\x0D\x00\x00\x01\x02\x00\x00' b'\x00\x00\x00\x00\x00\x00\x00'
cmd_start = b'\x0D\x00\x00\x03\x07\x00\x00' b'\x00\x00\x00\x00\x00\x00\x00'


class ConnectionDone():
    pass

class RFXContextManager():
    transport: AsyncTransport = None

    queue: asyncio.Queue
    loop = None

    status: RFXtrx.lowlevel.Status

    modes: List[str]

    def __init__(self, transport, modes: List[str]|None =None):
        self.transport = transport
        self.modes = modes
        self.loop = asyncio.get_event_loop()
        self.queue = asyncio.Queue()


    async def packets(self) -> AsyncGenerator[None, None]:
        while True:
            task = self.loop.create_task(self.queue.get())
            try:
                done, _ = await asyncio.wait((task, asyncio.Future()), return_when=asyncio.FIRST_COMPLETED)
            except asyncio.CancelledError:
                task.cancel()
                raise
            if task in done:
                yield task.result()
            else:
                task.cancel()

    async def __aenter__(self):

        # Init
        await self.transport.write_async(cmd_reset)
        await asyncio.sleep(0.5)

        await self.transport.write_async(cmd_getStatus)
        self.status = await self.readPacket()
        
        if self.modes is not None:
            await self.set_recmodes(self.modes)
            await self.transport.write_async(cmd_getStatus)
            self.status = await self.readPacket()
        
        logger.debug(self.status)
        await self.transport.write_async(cmd_start)

        asyncio.ensure_future(self.monitor())

        self.queue.put_nowait(ConnectionDone())



    async def __aexit__(self, exc_type, exc, tb):
        print("exit")

    async def monitor(self):
        logger.debug("monitor waiting for packet")
        pkt = await self.readPacket()
        # print(pkt)
        self.queue.put_nowait(pkt)
        asyncio.ensure_future(self.monitor())

    async def set_recmodes(self, modenames):
        logging.debug(f"Setting modes to {modenames}")
        data = bytearray([0x0D, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

        # Keep the values read during init.
        data[5] = self.status.tranceiver_type
        data[6] = self.status.output_power

        # Build the mode data bytes from the mode names
        for mode in modenames:
            byteno, bitno = RFXtrx.lowlevel.get_recmode_tuple(mode)
            if byteno is None:
                raise ValueError('Unknown mode name '+mode)

            data[7 + byteno] |= 1 << bitno

        await self.transport.write_async(data)

    async def readPacket(self):
        
        data = await self.transport.read_async(1)
        pkt = bytearray(data)    
        data = await self.transport.read_async(pkt[0]+1 - len(pkt))
        pkt.extend(bytearray(data))

        logger.debug("Recv: %s", " ".join("0x{0:02x}".format(x) for x in pkt))

        pkt = RFXtrx.lowlevel.parse(pkt)

        return pkt

