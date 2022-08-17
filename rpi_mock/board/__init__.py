class _Pin:
    HIGH: int = 1
    IN: int = 0
    LOW: int = 0
    OUT: int = 1

    def __init__(self, identifier):
        self._id = identifier

    @property
    def id(self) -> int:
        return self._id

    def value(self) -> int:
        return 1


D1: _Pin = _Pin(1)
D2: _Pin = _Pin(2)
D3: _Pin = _Pin(3)
D4: _Pin = _Pin(4)
D5: _Pin = _Pin(5)
D6: _Pin = _Pin(6)
D7: _Pin = _Pin(7)
D8: _Pin = _Pin(8)
D9: _Pin = _Pin(9)
D10: _Pin = _Pin(10)
D11: _Pin = _Pin(11)
D12: _Pin = _Pin(12)
D13: _Pin = _Pin(13)
D14: _Pin = _Pin(14)
D15: _Pin = _Pin(15)
D16: _Pin = _Pin(16)
D17: _Pin = _Pin(17)
D18: _Pin = _Pin(18)
D19: _Pin = _Pin(19)
