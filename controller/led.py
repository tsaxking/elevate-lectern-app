from RPi import GPIO
from time import sleep
import threading
from enum import Enum
import asyncio


class FlashingSpeed(Enum):
    NONE = 0 # Ticks
    SLOW = 10 # Ticks
    MEDIUM = 5 # Ticks
    FAST = 2 # Ticks

class Brightness(Enum):
    OFF = 0 # Duty Cycle
    LOW = .33 # Duty Cycle
    MEDIUM = .66 # Duty Cycle
    HIGH = 1 # Duty Cycle



class LED:
    def __init__(self, pin: int, tick_speed, threaded: bool):
        self.pin = pin
        self.tick_speed = tick_speed
        # print(tick_speed)
        GPIO.setup(pin, GPIO.OUT)
        self.pwm = GPIO.PWM(pin, 1000)
        self.pwm.start(0)
        self.flashing_speed = FlashingSpeed.NONE
        self.brightness = Brightness.OFF
        self.running = True

        if threaded:
            thread = threading.Thread(target=self.event_loop)
            thread.daemon = True
            thread.start()

    def event_loop(self):
        tick = 0
        # self.pwm.ChangeDutyCycle(100)
        on = True
        while self.running:
            if self.flashing_speed is not FlashingSpeed.NONE:
                if tick - self.flashing_speed.value == 0:
                    on = not on
            else:
                on = True
            # print(on, tick, self.brightness.value)
            if on:
                self.pwm.ChangeDutyCycle(self.brightness.value * 100)
            else:
                self.pwm.ChangeDutyCycle(0)

            tick += 1
            if tick > self.flashing_speed.value:
                tick = 0
            sleep(self.tick_speed / 1000)
    
    def cleanup(self):
        self.running = False
        self.pwm.stop()
        GPIO.cleanup(self.pin)

class AsyncLED:
    def __init__(self, pin: int, tick_speed: int):
        self.pin = pin
        self.tick_speed = tick_speed
        GPIO.setup(pin, GPIO.OUT)
        self.pwm = GPIO.PWM(pin, 1000)
        self.pwm.start(0)
        self.flashing_speed = FlashingSpeed.NONE
        self.brightness = Brightness.OFF
        self.running = False

    def set_flashing_speed(self, speed: FlashingSpeed):
        self.flashing_speed = speed
        if speed is FlashingSpeed.NONE:
            self.pwm.ChangeDutyCycle(0)
        else:
            self.pwm.ChangeDutyCycle(self.brightness.value * 100)

    async def start(self):
        self.running = True
        tick = 0
        on = True
        while self.running:
            if self.flashing_speed is not FlashingSpeed.NONE:
                if tick - self.flashing_speed.value == 0:
                    on = not on
            else:
                on = True

            if on:
                self.pwm.ChangeDutyCycle(self.brightness.value * 100)
            else:
                self.pwm.ChangeDutyCycle(0)

            tick += 1
            if tick > self.flashing_speed.value:
                tick = 0
            await asyncio.sleep(self.tick_speed / 1000)

    def stop(self):
        self.running = False
        self.pwm.stop()

    def cleanup(self):
        self.stop()
        GPIO.cleanup(self.pin)