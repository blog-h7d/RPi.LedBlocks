import enum
import rpi_mock.board


class Direction(enum.Enum):
    OUTPUT = 'output'
    INPUT = 'input'


class DigitalInOut:
    _direction: Direction = Direction.INPUT
    value: bool = False

    def __init__(self, pin: rpi_mock.board._Pin):
        self._pin = pin

    @property
    def direction(self):
        return self._direction

    def switch_to_output(self):
        self._direction = Direction.OUTPUT

    def switch_to_input(self):
        self._direction = Direction.INPUT