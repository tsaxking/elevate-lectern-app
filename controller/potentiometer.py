from gpiozero import MCP3008

class Potentiometer:
    def __init__(self, pin):
        self.pin = pin
        self.adc = MCP3008(channel=pin)

    def read(self):
        return float(self.adc.value)