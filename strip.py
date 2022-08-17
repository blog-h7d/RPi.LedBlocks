import asyncio

try:
    import neopixel
except ModuleNotFoundError:
    from rpi_mock import neopixel

try:
    # noinspection UnusedImports
    import board  # pylint: disable=unused-import
    import digitalio  # pylint: disable=unused-import
except ModuleNotFoundError:
    from rpi_mock import board
    from rpi_mock import digitalio

import pydantic


class Strip(pydantic.BaseModel):  # pylint: disable=no-member
    identifier: str = 'default'
    count: int = 100
    gpio: str = "board.D13"
    brightness: float = 1.0
    bytes_per_pixel: int = 3
    type: str = "neopixel.GRB"
    power_gpio: str = "board.D18"

    _strip: neopixel.NeoPixel
    _gpio: digitalio.DigitalInOut
    _power_gpio: digitalio.DigitalInOut

    def __init__(self, **data):
        super().__init__(**data)

        self._gpio = eval(self.gpio)

        power_pin = eval(self.power_gpio)
        self._power_gpio = digitalio.DigitalInOut(power_pin)
        self._power_gpio.switch_to_output()

        self._strip = neopixel.NeoPixel(
            pin=self._gpio,
            n=self.count,
            bpp=self.bytes_per_pixel,
            brightness=self.brightness,
            pixel_order=eval(self.type),
            auto_write=False
        )

    @property
    def strip(self) -> neopixel.NeoPixel:
        return self._strip

    async def run_tests(self):
        print(f'Starting tests for strip {self.identifier}.')
        await self.switch_on()

        print(f'Coloring reds for {self.identifier}.')
        for index in range(self.count):
            self._strip[index] = (255, 0, 0)
            self._strip.show()

        await asyncio.sleep(1)

        print(f'Coloring greens for {self.identifier}.')
        for index in range(self.count):
            self._strip[index] = (0, 255, 0)
            self._strip.show()

        await asyncio.sleep(1)

        await self.switch_off()
        print(f'Finished tests for strip {self.identifier}.')

    def set_colors(self, color: tuple[int, int, int], start_index: int, length: int = 1):
        if self._strip:
            self._strip[start_index: start_index + length] = [color] * length

    def update_strip(self):
        self._strip.show()

    async def switch_on(self):
        self._power_gpio.value = True
        await asyncio.sleep(1)

    async def switch_off(self):
        for index in range(self.count):
            self._strip[index] = tuple([0] * self.bytes_per_pixel)
        self._strip.show()

        await asyncio.sleep(1)
        self._power_gpio.value = False

    class Config:
        underscore_attrs_are_private = True
