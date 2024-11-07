from asyncrfx import AsyncSerialTransport, RFXContextManager, ConnectionDone
import RFXtrx
import logging
import asyncio

logger = logging.getLogger(__name__)

async def test():
    transport = AsyncSerialTransport(port='/dev/ttyUSB0', baudrate=38400)

    core = RFXContextManager(transport, modes=["ac", "arc", "fineoffset"])

    async with core:
        async for pkt in core.packets():
            if isinstance(pkt, ConnectionDone):
                logger.info("Connected")
                
                # Test
                pkt = RFXtrx.lowlevel.Lighting2()
                pkt.parse_id(0x00, "0102034:1")
                dev = RFXtrx.LightingDevice(pkt)
                dev.send_off(core.transport)
                await asyncio.sleep(5)
                dev.send_on(core.transport)
            elif isinstance(pkt, RFXtrx.lowlevel.TempHumid):
                logger.info(f"Temp: {pkt.temp} Humidity: {pkt.humidity}")

            elif isinstance(pkt, RFXtrx.SensorEvent):
                logger.info(f"Sensor: {pkt}")
            else:
                logger.debug(pkt)


logging.basicConfig(level=logging.DEBUG)

loop = asyncio.get_event_loop()
# loop.run_until_complete(core.connect(port='/dev/ttyUSB0', baudrate=38400))

asyncio.ensure_future(test())
loop.run_forever()