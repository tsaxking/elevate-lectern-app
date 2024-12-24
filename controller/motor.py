# from RPi import GPIO
from time import sleep
from sensors import Switch, Potentiometer
from enum import Enum, auto
import sys
# from pwm import PWM
import pigpio
from typing import TypedDict

# FREQ = 100

# MAX = 20
# ZERO = 14.3
# MIN = 8

# TICK_SPEED = 10

# ACCELERATION = .02

# MAX_SPEED = 2000
# MIN_SPEED = 1000
# NEUTRAL = 1500



# def make_duty_cycle(motor_speed: float):
#     # 0 is 14.3
#     # 1 is 20
#     # -1 is 10

#     if motor_speed > 1:
#         motor_speed = 1
#     if motor_speed < -1:
#         motor_speed = -1

#     if motor_speed == 0:
#         return ZERO
    
#     if motor_speed > 0:
#         return ZERO + (MAX - ZERO) * motor_speed
#     else:
#         return ZERO + (ZERO - MIN) * motor_speed
    

class MotorState(Enum):
    STAND_BY = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()
    CALIBRATING = auto()
    TESTING = auto()

    def to_dict(self):
        return self.name


# class CalibrateState(Enum):
#     TO_MAX = auto()
#     MAX = auto()
#     TO_MIN = auto()
#     MIN = auto
#     TO_ZERO = auto()
#     ZERO = auto()
#     DONE = auto()

class MotorConfig(TypedDict):
    pin: int
    max: float
    min: float
    zero: float
    invert: bool
    tick_speed: float
    acceleration: float

def make_pulse_width(speed: float, config: MotorConfig):
    neutral = config['zero']
    max_speed = config['max']
    min_speed = config['min']

    if config['invert']:
        speed = -speed
    if speed > 1:
        speed = 1
    if speed < -1:
        speed = -1

    if speed == 0:
        return neutral
    
    if speed > 0:
        return neutral + (max_speed - neutral) * speed
    else:
        return neutral + (neutral - min_speed) * speed

class Motor:
    def __init__(self, config: MotorConfig):
        # if not GPIO.getmode():
        #     GPIO.setmode(GPIO.BCM)
        self.config = config
        self.pin = config["pin"]
        self.max = config["max"]
        self.min = config["min"]
        self.zero = config["zero"]
        self.invert = config["invert"]
        self.tick_speed = config["tick_speed"]
        self.state = MotorState.STOPPED
        self.speed = 0.0
        # GPIO.setup(self.pin, GPIO.OUT)
        # self.pwm = GPIO.PWM(self.pin, FREQ)
        # self.pwm = PWM(self.pin, FREQ)
        # self.pwm.start(0)
        self.pi = pigpio.pi()
        self.pi.set_mode(self.pin, pigpio.OUTPUT)
        self.set_speed(0)
        # self.pi.set_servo_pulsewidth()
        # self.servo = self.pi.gpioServo()

    def set_speed(self, speed: float):
        # if not self.pin:
        #     raise Exception('Motor not started')
        # print(f'Speed: {speed}')
        # Duty cycle is 0-255
        # normalized = (speed + 1) / 2
        # duty_cycle = normalized * 255
        # self.pwm.ChangeDutyCycle(make_duty_cycle(speed))
        self.pi.set_servo_pulsewidth(self.pin, make_pulse_width(speed, self.config))
        # self.pwm.ChangeDutyCycle(duty_cycle)
        self.speed = speed
        if speed == 0.0:
            self.state = MotorState.STAND_BY
        else:
            self.state = MotorState.RUNNING


    def cleanup(self):
        self.pi.set_servo_pulsewidth(self.pin, 0)

    def accelerate_to(self, target: float, time: float):
        if self.speed == target:
            return
        # print(f'Accelerating to {target}')
        
        start = self.speed
        ticks = time / (self.tick_speed / 1000)
        acceleration = (target - start) / ticks
        # print(f'Acceleration: {acceleration}')
        # print(f'Ticks: {ticks}')

        while True:
            if target < start and self.speed <= target:
                break
            if target > start and self.speed >= target:
                break
            if target < start:
                # print(f'Decelerating to {self.speed + acceleration}')
                self.set_speed(self.speed + acceleration)
            else:
                # print(f'Accelerating to {self.speed + acceleration}')
                self.set_speed(self.speed + acceleration)
            sleep(self.tick_speed / 1000)

    def calibrate(self, time: float = 10):
        self.state = MotorState.CALIBRATING
        self.accelerate_to(1, 2)
        sleep(time)
        self.accelerate_to(-1, 2)
        sleep(time)
        self.accelerate_to(0, 2)
        sleep(time)
        self.state = MotorState.STAND_BY

    def test(self, time: float = 10):
        self.state = MotorState.TESTING
        self.accelerate_to(1, 2)
        sleep(time)
        self.accelerate_to(-1, 2)
        sleep(time)
        self.accelerate_to(0, 2)
        sleep(time)

    def enable(self):
        self.state = MotorState.STAND_BY
        self.set_speed(0)

    def disable(self):
        self.state = MotorState.STOPPING
        # self.pwm.ChangeDutyCycle(0)
        self.pi.set_servo_pulsewidth(self.pin, 0)
        # self.set_speed(0)
        self.state = MotorState.STOPPED


# def start_potentiometer_loop(potentiometer: Potentiometer, motor: Motor):
#     while True:
#         speed = potentiometer.read()
#         speed = (speed - 0.5) * 2
#         motor.set_speed(speed)
#         sleep(TICK_SPEED / 1000)

# # if args include test, run test

# if __name__ == "__main__":
#     # Test args
#     if len(sys.argv) > 1 and sys.argv[1] == 'test':
#         pin = sys.argv[2] if len(sys.argv) > 2 else 18
#         # GPIO.setmode(GPIO.BCM)
#         motor = Motor(pin)
#         motor.test(2)
#         motor.cleanup()
#         exit()