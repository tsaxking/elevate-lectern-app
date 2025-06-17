from RPi import GPIO
from gpiozero import MCP3008
from typing import TypedDict
import threading
import time
import utils
import numpy as np
import busio
import adafruit_vl53l0x
import board

class TOF:
    def __init__(self):
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = adafruit_vl53l0x.VL53L0X(self.i2c)
        self.points = []
        time.sleep(0.2)

    def read(self):
        value = self.sensor.range #* 15.5 / 27
        self.points.append(value)
        if len(self.points) > 5:
            self.points.pop(0)
        if len(self.points) < 3:
            return utils.cm_to_in(value / 10)
        data = utils.remove_outliers_zscore(self.points, 3)
        avg = np.average(data)
        # return round(utils.cm_to_in(avg / 10) / 0.25) * 0.25 if not np.isnan(avg) else 0
        return utils.cm_to_in(avg / 10) if not np.isnan(avg) else 0

    def cleanup(self):
        print('Cleaning up TOF')


class Switch:
    def __init__(self, pin: int, flip: bool):
        if not GPIO.getmode():
            GPIO.setmode(GPIO.BCM)
        self.pin = pin
        self.flip = flip
        GPIO.setup(pin, GPIO.IN)

    def read(self):
        input = GPIO.input(self.pin)
        if self.flip:
            if input == 0:
                return True
            else:
                return False
        else:
            if input == 1:
                return True
            else:
                return False

    def cleanup(self):
        pass

    def stop(self):
        pass

class Potentiometer:
    def __init__(self, channel: int):
        self.channel = channel
        self.potentiometer = MCP3008(channel=channel)
        
    def read(self) -> float:
        return self.potentiometer.value


class UltrasonicConfig(TypedDict):
    trig: int
    echo: int
    threading: bool
    tick_speed: float
    offset: float

class Ultrasonic:
    def __init__(self, config: UltrasonicConfig):
        self.trig = config["trig"]
        self.echo = config["echo"]
        self.tick_speed = config["tick_speed"]
        self.running = True
        self.offset = config['offset']
        self.points = [] # limit the number of points to 5, and use moving average
        if not GPIO.getmode():
            GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.trig, GPIO.OUT)
        GPIO.setup(self.echo, GPIO.IN)

        if config['threading']:
            self.thread = threading.Thread(target=self.event_loop)
            self.thread.daemon = True
            self.thread.start()

    def event_loop(self):
        timeout = 1
        # seconds_per_level = 10
        # ticks_per_seconds = 1000 / self.tick_speed
        # ticks_per_level = seconds_per_level * ticks_per_seconds
        # tick = 0
        length = 12
        while self.running:
            GPIO.output(self.trig, True)
            time.sleep(0.00001)
            GPIO.output(self.trig, False)
            start_time = 0
            end_time = 0

            stop = False

            start = time.time()
            while GPIO.input(self.echo) == 0:
                start_time = time.time()
                if (start_time - start) > timeout:
                    stop = True
                    break

            end = time.time()
            while GPIO.input(self.echo) == 1:
                end_time = time.time()
                if (end_time - end) > timeout:
                    stop = True
                    break

            # tick += 1
            # if tick > ticks_per_level:
            #     tick = 0
            #     length += 1
            #     print(f'Next level: {length}')


            if not stop:
                duration = end_time - start_time
                distance = (duration * 34300) / 2
                self.points.append(utils.cm_to_in(distance))
                if len(self.points) > length:
                    self.points.pop(0)
            time.sleep(self.tick_speed / 1000)

    def read(self):
        data = utils.remove_outliers_zscore(self.points, 3)
        # data = utils.remove_outliers_iqr(self.points)
        # data = utils.remove_outliers_trim(self.points, 10)
        avg = np.average(data)
        return avg if not np.isnan(avg) else 0 + self.offset
        # threshold = 20 # percent
        # data = np.array(self.points)
        # data_min = np.min(data)
        # data_max = np.max(data)
        # data_range = (threshold / 100) * (data_max - data_min)
        # filtered_data = data[(data >= data_min + data_range) & (data <= data_max - data_range)]
        # return np.average(self.points)
    
    def cleanup(self):
        self.running = False
        GPIO.cleanup([self.trig, self.echo])