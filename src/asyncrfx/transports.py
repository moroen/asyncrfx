import aioserial
import asyncio
import logging

logger = logging.getLogger(__name__)

class AsyncTransport():
    def __init__(self):
        pass

    def send(self, pkt):
        loop = asyncio.get_event_loop()
        loop.create_task(self.write_async(pkt))
        
    async def write_async(self, pkt):
        logger.debug("Send: %s", " ".join("0x{0:02x}".format(x) for x in pkt))

    async def read_async(self, size: int):
        pass
        

class AsyncSerialTransport(AsyncTransport):
    port: str
    baudrate: int
    transport: aioserial.AioSerial = None

    loop = None

    def __init__(self, port, baudrate):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.loop = asyncio.get_event_loop()
        self.transport = aioserial.AioSerial(port=self.port, baudrate=self.baudrate)

    async def write_async(self, pkt):
        await super().write_async(pkt)
        await self.transport.write_async(pkt)


    async def read_async(self, size: int):
        await super().read_async(size)
        return await self.transport.read_async(size)
