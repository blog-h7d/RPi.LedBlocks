# pylint disable=invalid-name,unused-argument,two-few-public-methods

class NeoPixel:
    def __init__(self, *args, **kwargs):
        self._leds = [(0,0,0)] * 1000
        pass

    def begin(self):
        pass

    def setPixelColor(self, *args, **kwargs):
        pass

    def show(self):
        pass

    def __setitem__(self, index, val):
        self._leds[index] = val

    def __getitem__(self, index):
        return self._leds[index]


GRB: str = 'GRB'
