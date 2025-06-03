'''
fileoverview: This file contains the main system loop for the lectern. It is responsible for reading sensor data,
handling incoming OSC commands, and controlling the motor. The system is designed to be controlled remotely via OSC.

In addition to OSC, there is a UDP server that sends the current state of the system to a client. This is used to
display the current state of the system on the web interface located in /app.

Because OSC commands are blocking, the system uses a queue to handle incoming commands. This allows the system to
continue running while waiting for a command.

In addition, OSC commands must be handled synchronously, so the system uses a separate thread to handle incoming
messages. However, a single TCP connection is used to handle emergency stop commands, which will do its best to stop
the current operation, delete all commands in the queue, and stop the motor.
'''

from motor import Motor, MotorState
from typing import TypedDict
from RPi import GPIO
from sensors import Switch, TOF
from enum import Enum, auto
from led import Brightness, FlashingSpeed, AsyncLED
from utils import round, clamp
import math
import time
import asyncio
from PID import PID

def clear():
    print(chr(27) + "[2J")

MAX_SPEED = .5
ACCEL_RATE = 0.08 # Acceleration rate
SPEED_TOLERANCE = 0.05
POS_TOLERANCE = .25
SLOW_DOWN_DISTANCE = 2
LIMIT_SLOW_DOWN_DISTANCE = 3
LIMIT_SLOW_DOWN_SPEED = 0.1
LOWER_POSITION_OFFSET = 0
UPPER_POSITION_OFFSET = 27 # in
FAIL_STATE_TOLERANCE = 3 # in/s

CALIBRATION_SPEED = 0.3 # 30% of MAX_SPEED

UDP_PORT = 41234
E_STOP_PORT = 11111
OSC_PORT = 12321
SIG_FIGS = 2


class LecternConfig(TypedDict):
    position_pin: int
    tick_speed: int
    max_limit_pin: int
    min_limit_pin: int
    power_pin: int
    main_up_pin: int
    main_down_pin: int
    main_speed_chanel: int
    log_state: bool
    secondary_up_pin: int
    secondary_down_pin: int
    secondary_speed_channel: int
    status_led_pin: int
    osc_led_pin: int
    down_trigger_pin: int
    down_echo_pin: int
    up_trigger_pin: int
    up_echo_pin: int

class SensorState(TypedDict):
    position: float = 0
    min_limit: bool = False
    max_limit: bool = False
    power: bool = False
    main_up: float = 0
    main_down: float = 0
    secondary_up: float = 0
    secondary_down: float = 0
    main_speed: float = 0
    secondary_speed: float = 0


class SYSTEM_STATE(Enum):
    STAND_BY = auto()
    MOVING = auto()
    ACCELERATING = auto()
    CALIBRATING = auto()
    LOCK = auto()

    def to_dict(self):
        return self.name
    
class GlobalState(Enum):
    SHUTDOWN = auto()
    STARTUP = auto()
    RUNNING = auto()
    CALIBRATING = auto()

    def to_dict(self):
        return self.name

class UDPSystemState(TypedDict):
    sensors: SensorState
    motor_speed: float
    state: SYSTEM_STATE
    command_ready: bool
    target_speed: float
    target_pos: float
    gpio_moving: bool
    gpio_target_motor_speed: float
    motor_state: MotorState
    proximity_up: float
    proximity_down: float

class Sensors:
    def __init__(self, config: LecternConfig):
        GPIO.setmode(GPIO.BCM)
        self.position = TOF()
        self.max_limit = Switch(config['max_limit_pin'], True) # Inverted because we want it NC for safety
        self.min_limit = Switch(config['min_limit_pin'], True) # Inverted because we want it NC for safety
        self.power = Switch(config['power_pin'], False)
        self.main_up = Switch(config['main_up_pin'], False)
        self.main_down = Switch(config['main_down_pin'], False)
        self.secondary_up = Switch(config['secondary_up_pin'], False)
        self.secondary_down = Switch(config['secondary_down_pin'], False)


    def read(self):
        return SensorState(
            position=round(self.position.read(), SIG_FIGS),
            min_limit=self.min_limit.read(),
            max_limit=self.max_limit.read(),
            power=self.power.read(),
            main_up=self.main_up.read(),
            main_down=self.main_down.read(),
            secondary_up=self.secondary_up.read(),
            secondary_down=self.secondary_down.read(),
        )

    def cleanup(self):
        self.position.cleanup()
        self.max_limit.cleanup()
        self.min_limit.cleanup()
        self.power.cleanup()
        self.main_up.cleanup()
        self.main_down.cleanup()
        self.secondary_up.cleanup()
        self.secondary_down.cleanup()


class CalibrationState(Enum):
    NOT_CALIBRATED = auto()
    MAX_FAST = auto()
    MAX_SLOW = auto()
    MIN_FAST = auto()
    MIN_SLOW = auto()
    DONE = auto()

class Calibration:
    def __init__(self):
        self.top = 20
        self.bottom = 6
        self.velocity = 5.354 * MAX_SPEED # in/s at 100% velocity

class Lectern:
    def __init__(self, motor: Motor, config: LecternConfig):
        self.motor = motor
        self.config = config
        self.sensors = Sensors(config)
        self.calibration = Calibration()
        self.calibration_state = CalibrationState.DONE
        self.state = SYSTEM_STATE.STAND_BY
        self.tick_speed = config['tick_speed']
        self.pid = PID(kp=0.7, ki=0.01, kd=0.2)

        self.global_state = GlobalState.STARTUP
        self.leds = {
            'status': AsyncLED(config['status_led_pin'], self.tick_speed),
            'osc': AsyncLED(config['osc_led_pin'], self.tick_speed)
        }

        self.on = True
        self.stop_timer = 0
        self.locked = False

        self.connections = []

        self.prev_speed = 0
        self.target_motor_speed = 0
        self.speed_multiplier = 1.0  # Used to adjust speed based on position or other factors
        
        self.velocity = 0
        self.velocity_points = []

        self.gpio_target_motor_speed = 0
        self.gpio_moving = False
        self.gpio_fixed_speed = 0.3

        self.start_pos = -1  # Used for position tracking when moving to a target position
        self.target_pos = -1
        self.target_pos_with_time = -1
        self.target_time = 0
        self.target_time_start = 0
        self.esitmated_speed = 0

        self.command_ready = True
        self.fail_state = False

        self.tasks = []
        self.calibration_task: asyncio.Task = None

    def set_speed(self, speed: float):
        self.prev_speed = self.motor.speed
        self.target_motor_speed = speed

    def stop(self):
        self.target_motor_speed = 0
        self.gpio_target_motor_speed = 0
        self.target_pos = -1
        self.target_pos_with_time = -1
        self.target_time = 0
        self.target_time_start = 0
        self.esitmated_speed = 0
        if self.calibration_task:
            self.calibration_task.cancel()
            self.calibration_task = None

    def bump(self, distance: float):
        print(f"Bumping {distance} inches")
        self.go_to(self.sensors.position.read() + distance)

    async def cleanup(self):
        print("Cleaning up system...")
        self.on = False
        self.motor.cleanup()
        self.sensors.cleanup()
        GPIO.cleanup()
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)

    
    def go_to(self, pos: float):
        if self.calibration_state != CalibrationState.DONE:
            print("Cannot go to position, system is not calibrated")
            return
        self.target_pos = pos
        self.pid.reset()

    def go_to_in(self, pos: float, time: float):
        if self.calibration_state != CalibrationState.DONE:
            print("Cannot go to position, system is not calibrated")
            return
        distance = pos - self.sensors.position.read()
        velocity = distance / time
        velocity = clamp(velocity, -1, 1)
        self.target_time = time
        self.target_time_start = time.time()
        self.target_pos_with_time = pos
        self.estimated_speed = velocity

    def home(self):
        self.go_to(self.calibration.bottom + LOWER_POSITION_OFFSET)

    def print_state(self):
        clear()
        sensors = self.sensors.read()
        print(f'State: {self.state}')
        print(f'Target Speed: {self.target_motor_speed}')
        print(f'Previous Speed: {self.prev_speed}')
        print(f'Current Speed: {self.motor.speed}')
        print(f'Main Up: {sensors["main_up"]}')
        print(f'Main Down: {sensors["main_down"]}')
        print(f'Max Limit: {sensors["max_limit"]}')
        print(f'Ready: {self.command_ready}')

    async def e_stop(self):
        print("Emergency stop triggered")
        self.stop()
        self.command_ready = False
        await asyncio.sleep(2)  # Give some time for the motor to stop
        self.command_ready = True

    async def run_calibration(self):
        self.global_state = GlobalState.CALIBRATING
        print('Starting calibration...')
        self.calibration_state = CalibrationState.MAX_FAST
        self.set_speed(CALIBRATION_SPEED)
        self.command_ready = False
        # Wait for max limit to be hit

        while not self.sensors.max_limit.read():
            await asyncio.sleep(self.tick_speed / 1000)
        self.set_speed(0) # Not neccessary, but good practice
        print('Max limit hit, slowly calibrating max position...')
        await asyncio.sleep(0.5) # Wait for the motor to stop
        self.calibration_state = CalibrationState.MAX_SLOW
        self.set_speed(-CALIBRATION_SPEED)
        await asyncio.sleep(0.5) 
        self.set_speed(0)
        await asyncio.sleep(0.5) # Wait for the motor to stop
        self.set_speed(CALIBRATION_SPEED / 2)
        while not self.sensors.max_limit.read():
            await asyncio.sleep(self.tick_speed / 1000)
        self.set_speed(0) # Not neccessary, but good practice
        print('Max position calibrated')
        self.calibration.top = self.sensors.position.read()
        await asyncio.sleep(0.5)
    
        # Now calibrate the min position
        print('Calibrating min position...')
        self.calibration_state = CalibrationState.MIN_FAST
        self.set_speed(-CALIBRATION_SPEED)
        start = time.time()
        while not self.sensors.min_limit.read():
            await asyncio.sleep(self.tick_speed / 1000)
        self.set_speed(0)
        await asyncio.sleep(0.5) # Wait for the motor to stop
        self.set_speed(CALIBRATION_SPEED)
        await asyncio.sleep(0.5) # Wait for the motor to start moving
        self.set_speed(0)
        await asyncio.sleep(0.5) # Wait for the motor to stop
        self.set_speed(-CALIBRATION_SPEED / 2)
        self.calibration_state = CalibrationState.MIN_SLOW


        while not self.sensors.min_limit.read():
            await asyncio.sleep(self.tick_speed / 1000)
        end = time.time()
        self.set_speed(0)
        print('Min position calibrated')
        self.calibration.bottom = self.sensors.position.read()
        await asyncio.sleep(0.5)
        self.calibration_state = CalibrationState.DONE
        print(f'Calibration done: Top={self.calibration.top}, Bottom={self.calibration.bottom}')
        self.set_speed(0)
        self.target_pos = -1
        self.target_pos_with_time = -1
        self.start_pos = -1
        self.command_ready = True
        self.global_state = GlobalState.RUNNING
        self.set_led_state()

        # Estimated velocity at 100% speed
        self.calibration.velocity = ((self.calibration.top - self.calibration.bottom) / (end - start)) / CALIBRATION_SPEED
        print(f'Calibration velocity: {self.calibration.velocity} in/s')


    def calibrate(self):
        self.calibration_task = asyncio.create_task(self.run_calibration())
        self.tasks.append(self.calibration_task)

    def shutdown(self):
        print("Shutting down lectern...")
        self.cleanup()
        self.target_motor_speed = 0
        self.gpio_target_motor_speed = 0
        self.target_pos = -1
        self.target_pos_with_time = -1
        self.stop_timer = 0
        self.state = SYSTEM_STATE.STAND_BY
        self.global_state = GlobalState.SHUTDOWN
        self.command_ready = False
        self.motor.disable()
        self.sensors.cleanup()
        self.on = False

    async def fail_state_cb(self):
        print("Is fail state")

    def set_led_state(self):
        self.leds['status'].brightness = Brightness.HIGH
        self.leds['status'].flashing_speed = FlashingSpeed.MEDIUM

    async def reboot(self):
        print("Rebooting system...")
        self.cleanup()
        self.global_state = GlobalState.STARTUP
        self.on = False
        self.motor.disable()
        self.sensors.cleanup()
        await self.start()

    def gpio_move(self, up: bool):
        print(f"GPIO Move: {'Up' if up else 'Down'}")
        if up:
            self.set_speed(self.gpio_fixed_speed)
        else:
            self.set_speed(-self.gpio_fixed_speed)
        self.gpio_moving = True
        self.command_ready = False
        self.target_pos = -1
        self.target_pos_with_time = -1
        self.target_time = 0
        self.target_time_start = 0
        self.esitmated_speed = 0

    def gpio_stop(self):
        print("GPIO Stop")
        self.gpio_moving = False
        self.command_ready = True
        self.stop()

    def gpio_lock(self):
        print("GPIO Lock")
        self.stop()
        self.gpio_moving = False
        self.command_ready = False
        self.locked = True

    def gpio_unlock(self):
        print("GPIO Unlock")
        self.command_ready = True
        self.locked = False

    async def start_up(self):
        self.set_speed(0.3)
        await asyncio.sleep(1)
        self.set_speed(0)
        await asyncio.sleep(0.5)
        self.set_speed(-0.3)
        await asyncio.sleep(1)
        self.set_speed(0)

    async def event_loop(self):
        start_power = None
        prev_pos = None
        try:
            while self.on:
                sensors = self.sensors.read()

                if sensors['power']:
                    if start_power is None:
                        start_power = time.time()
                    else:
                        if time.time - start_power > 5:
                            self.shutdown()
                else:
                    start_power = None
                
                # if self.is_fail_state() and self.global_state != GlobalState.CALIBRATING:
                #     self.fail_state_cb()

                # Count how many movement buttons are pressed
                movement_keys = ['main_up', 'main_down', 'secondary_up', 'secondary_down']
                pressed = [sensors[k] for k in movement_keys]
                active_count = sum(1 for p in pressed if p)

                # Lock if more than one movement input is active
                if active_count > 1:
                    self.gpio_lock()

                # Handle movement (only one input is active here)
                if not self.gpio_moving and not self.locked and active_count == 1:
                    if sensors['main_up'] or sensors['secondary_up']:
                        self.gpio_move(True)
                    elif sensors['main_down'] or sensors['secondary_down']:
                        self.gpio_move(False)
                    else:
                        self.gpio_stop()

                if not any(pressed):
                    if self.locked:
                        self.gpio_unlock()
                    if self.gpio_moving:
                        self.gpio_stop()

                # if not within tolerance, accelerate
                if self.target_motor_speed * self.speed_multiplier > self.motor.speed + SPEED_TOLERANCE:
                    self.motor.set_speed(self.motor.speed + ACCEL_RATE)
                    self.state = SYSTEM_STATE.ACCELERATING
                    self.command_ready = False
                elif self.target_motor_speed * self.speed_multiplier < self.motor.speed - SPEED_TOLERANCE:
                    self.motor.set_speed(self.motor.speed - ACCEL_RATE)
                    self.state = SYSTEM_STATE.ACCELERATING
                    self.command_ready = False

                # if within tolerance, set speed
                if abs(self.target_motor_speed * self.speed_multiplier - self.motor.speed) < SPEED_TOLERANCE:
                    self.motor.set_speed(self.target_motor_speed * self.speed_multiplier)
                    self.state = SYSTEM_STATE.MOVING
                    self.command_ready = True

                # if moving in the positive direction and the max limit is hit, stop
                if self.motor.speed > 0 and sensors['max_limit']:
                    self.motor.set_speed(0)
                    self.state = SYSTEM_STATE.STAND_BY
                    self.command_ready = True
                if self.motor.speed < 0 and sensors['min_limit']:
                    self.motor.set_speed(0)
                    self.state = SYSTEM_STATE.STAND_BY
                    self.command_ready = True

                if self.target_pos_with_time != -1:
                    current_pos = sensors['position']
                    if self.start_pos == -1:
                        self.start_pos = current_pos

                    distance_to_target = self.target_pos_with_time - current_pos
                    reached = abs(distance_to_target) <= POS_TOLERANCE

                    if not reached:
                        speed = self.pid.compute(self.target_pos, current_pos)
                        speed = clamp(speed, -1.0, 1.0)  # prevent overspeeding
                        self.set_speed(speed)
                    else:
                        self.stop()
                        self.target_pos_with_time = -1
                        self.start_pos = -1
                        distance_to_target = 0
                        self.command_ready = True

                if self.target_pos != -1:
                    current_pos = sensors['position']
                    if self.start_pos == -1:
                        self.start_pos = current_pos
                    
                    distance_to_target = self.target_pos - current_pos
                    reached = abs(distance_to_target) < POS_TOLERANCE

                    # slow_down = abs(distance_to_target) - SLOW_DOWN_DISTANCE if abs(distance_to_target) < SLOW_DOWN_DISTANCE else 0
                    # if distance_to_target > 0 and not reached:
                    #     self.set_speed(1 + slow_down / 50)
                    # elif distance_to_target < 0 and not reached:
                    #     self.set_speed(-1 - slow_down / 50)

                    if not reached:
                        speed = self.pid.compute(self.target_pos, current_pos)
                        speed = clamp(speed, -1.0, 1.0)  # prevent overspeeding
                        self.set_speed(speed)
                    else:
                        self.stop()
                        self.target_pos = -1
                        self.start_pos = -1
                        distance_to_target = 0
                        self.command_ready = True

                stop = False

                if self.calibration_state == CalibrationState.DONE:
                    position = sensors['position']
                    if self.motor.speed > 0:  # Moving up
                        distance_to_top = self.calibration.top - position
                        if distance_to_top <= 0:
                            stop = True
                        elif distance_to_top < LIMIT_SLOW_DOWN_DISTANCE:
                            # Inverse logarithmic slowdown: drastically reduce speed as approaching the limit
                            self.speed_multiplier = 1 - math.log1p((LIMIT_SLOW_DOWN_DISTANCE - distance_to_top) / LIMIT_SLOW_DOWN_DISTANCE)
                        else:
                            self.speed_multiplier = 1  # No slowdown if far away
                    elif self.motor.speed < 0:  # Moving down
                        distance_to_bottom = position - self.calibration.bottom
                        if distance_to_bottom <= 0:
                            stop = True
                        elif distance_to_bottom < LIMIT_SLOW_DOWN_DISTANCE:
                            # Inverse logarithmic slowdown: drastically reduce speed as approaching the limit
                            self.speed_multiplier = 1 - math.log1p((LIMIT_SLOW_DOWN_DISTANCE - distance_to_bottom) / LIMIT_SLOW_DOWN_DISTANCE)
                        else:
                            self.speed_multiplier = 1  # No slowdown if far away
                    else:
                        self.speed_multiplier = 1  # No movement, no speed change

                if self.target_motor_speed == 0 and abs(self.motor.speed) < SPEED_TOLERANCE or stop:
                    self.prev_speed = 0
                    self.motor.disable()
                    self.state = SYSTEM_STATE.STAND_BY
                    self.command_ready = True
                
                # if self.locked:
                #     self.state = SYSTEM_STATE.LOCK
                #     self.command_ready = False

                # if self.state == SYSTEM_STATE.LOCK:
                #     self.stop()

                    
                if self.global_state == SYSTEM_STATE.CALIBRATING:
                    self.command_ready = False

                    
                if self.stop_timer > 0:
                    self.stop_timer = self.stop_timer - 1

                if prev_pos is not None:
                    distance = prev_pos - sensors['position']
                    velocity = distance / (self.tick_speed / 1000)
                    self.velocity_points.append(velocity)
                    if len(self.velocity_points) > 5:
                        self.velocity_points.pop(0)
                    self.velocity = sum(self.velocity_points) / len(self.velocity_points)

                prev_pos = sensors['position']

                await asyncio.sleep(self.tick_speed / 1000)
        except Exception as e:
            print(f"Error in event loop: {e}")
            exit()

    async def start(self):
        print("Starting lectern...")
        self.on = True
        
        for led in self.leds.values():
            self.tasks.append(asyncio.create_task(led.start()))

        self.tasks.append(asyncio.create_task(self.event_loop()))
        self.tasks.append(asyncio.create_task(self.start_up()))