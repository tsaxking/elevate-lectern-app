from motor import Motor
import RPi.GPIO as GPIO
import asyncio
from control import trapezoidal_velocity_control, pid_control, PID, TrapezoidalProfile, loop_until, async_loop_until
from typing import TypedDict, Any
import json
from potentiometer import Potentiometer
from enum import Enum, auto
import time

class SYSTEM_STATE(Enum):
    STAND_BY = auto()
    MOVING = auto()
    CALIBRATING = auto()
    SHUTDOWN = auto()
    STARTUP = auto()
    LOCK = auto()

class Command(TypedDict):
    command: str
    args: Any

COMMANDS = {
    'go_to': float,
    'move': float,
    'end': None,
    'stop': None,
    'calibrate': None,
    'home': None,
    'shutdown': None
}

TARGET_RANGE = 0.05 # The range of the target position that is considered "reached"

class SystemConfig(TypedDict):
    position_pin: int
    tick_speed: int
    max_limit_pin: int
    min_limit_pin: int
    power_pin: int
    main_up_pin: int
    main_down_pin: int
    log_state: bool
    secondary_up_pin: int
    secondary_down_pin: int


class SensorState(TypedDict):
    position: float = 0
    velocity: float = 0
    min_limit: bool = False
    max_limit: bool = False
    power: bool = False
    main_up: float = 0
    main_down: float = 0
    secondary_up: float = 0
    secondary_down: float = 0

class System:
    def __init__(self, motor: Motor, config: SystemConfig):
        """
        Initializes the system object.
        
        :param motor: Motor object.
        """
        self.motor = motor
        self.position_pin = Potentiometer(config['position_pin'])
        self.tick_speed = config['tick_speed']
        self.max_limit_pin = config['max_limit_pin']
        self.min_limit_pin = config['min_limit_pin']
        self.power_pin = config['power_pin']
        self.main_up_pin = Potentiometer(config['up_pin'])
        self.main_down_pin = Potentiometer(config['down_pin'])
        self.secondary_up_pin = Potentiometer(config['secondary_up_pin'])
        self.secondary_down_pin = Potentiometer(config['secondary_down_pin'])
        self.log_state = config['log_state']
        self.state = SYSTEM_STATE.STAND_BY

        self.sensor_state = SensorState()

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.max_limit_pin, GPIO.IN)
        GPIO.setup(self.min_limit_pin, GPIO.IN)
        GPIO.setup(self.power_pin, GPIO.IN)
        GPIO.setup(self.main_up_pin, GPIO.IN)

        self.velocity = 0
        self.min = 0
        self.max = 100 # Will be changed after calibration
        self.force_stop = False

        self.command_queue: asyncio.Queue = asyncio.Queue()

    def get_position(self) -> float:
        """Returns the normalized current position of the system."""
        
        min = self.get_min()
        pos = self.position_pin.read() - min
        max = self.get_max() - min

        return pos / max
    
    async def go_to(self, desired_position: int):
        """Moves the system to the specified position."""
        self.force_stop = False

        if desired_position < 0 or desired_position > 1:
            return

        # If it's at its limit and wants to go further, do nothing
        current = self.get_position()
        if current < desired_position and self.max_on():
            return
        if current > desired_position and self.min_on():
            return

        pid: PID = {
            'Kp': 1.0,
            'Ki': 0.1,
            'Kd': 0.001,
            'integral': 0,
            'previous_error': 0,
            'tick_speed': self.tick_speed
        }

        profile: TrapezoidalProfile = {
            'MAX_VELOCITY': 100,
            'ACCELERATION': 10,
            'DECELERATION': 10,
            'tick_speed': self.tick_speed
        }

        self.state = SYSTEM_STATE.MOVING

        while True:
            if self.force_stop:
                break
            if current < desired_position and self.get_position() > desired_position:
                break
            if current > desired_position and self.get_position() < desired_position:
                break
            if abs(desired_position - self.get_position()) < TARGET_RANGE:
                break
        
            desired_velocity = trapezoidal_velocity_control(
                current_pos=self.get_position(),
                target_pos=desired_position,
                current_vel=self.velocity,
                profile=profile
            )
            # If it's at the constant velocity phase, use PID control
            # Otherwise, use the trapezoidal profile
            pwm_output = pid_control(
                setpoint=desired_velocity,
                measured=self.velocity,
                pid=pid
            ) if abs(desired_velocity) == profile['MAX_VELOCITY'] else desired_velocity

            # If it's in motion and hits the limit in that direction, stop
            if pwm_output < 0 and self.sensor_state['min_limit']:
                self.stop()
                break
            if pwm_output > 0 and self.sensor_state['max_limit']:
                self.stop()
                break

            self.move(pwm_output)
            await asyncio.sleep(self.tick_speed / 1000)

        self.state = SYSTEM_STATE.STAND_BY

    def move(self, speed: float):
        """Moves the system at the specified speed."""
        self.motor.set_speed(speed)

    def stop(self):
        """Stops the system."""
        self.motor.stop()
        self.force_stop = True

    async def to_min(self):
        """Moves the system to the home position."""

        while not self.sensor_state['min_limit']:
            if self.force_stop:
                break
            self.move(-10)
            await asyncio.sleep(self.tick_speed / 1000)
        
        self.stop()
        self.move(5)
        await asyncio.sleep(0.1)

        while not self.sensor_state['min_limit']:
            if self.force_stop:
                break
            self.move(1)
            await asyncio.sleep(self.tick_speed / 1000)

        self.stop()
        self.min = GPIO.input(self.position_pin)

    async def to_max(self):
        """Moves the system to the max position."""

        while not self.sensor_state['max_limit']:
            if self.force_stop:
                break
            self.move(10)
            await asyncio.sleep(self.tick_speed / 1000)
        
        self.stop()
        self.move(-5)
        await asyncio.sleep(0.1)

        while not self.sensor_state['max_limit']:
            if self.force_stop:
                break
            self.move(-1)
            await asyncio.sleep(self.tick_speed / 1000)

        self.stop()
        self.max = GPIO.input(self.position_pin)

    # inverts the min and max values if the sensor outputs the signal in reverse
    def get_max(self):
        return self.max if self.max > self.min else self.min
    
    def get_min(self):
        return self.min if self.max > self.min else self.max

    async def send_command(self, command: Command):
        """Sends a command to the system."""
        await self.command_queue.put(command)

    async def calibrate(self):
        self.state = SYSTEM_STATE.CALIBRATING
        await self.to_max()
        await self.to_min()
        self.state = SYSTEM_STATE.STAND_BY

    async def startup(self):
        """Starts the system."""
        self.state = SYSTEM_STATE.STARTUP
        await self.calibrate()
        self.load_state()
        self.state = SYSTEM_STATE.STAND_BY

    async def shutdown(self):
        """Shuts down the system."""
        self.state = SYSTEM_STATE.SHUTDOWN
        self.save_state()
        await self.to_min()
        self.stop()
        self.motor.cleanup()

    def save_state(self):
        # JSON dump the current state of the system
        str = json.dump({
            'position': self.get_position(),
        })

        with open('state.json', 'w') as f:
            f.write(str)

    def load_state(self):
        # Load the state from the JSON file
        try:
            with open('state.json', 'r') as f:
                data = json.load(f)
                self.go_to(data['position'])
        except:
            self.go_to(0)

    def set_sensor_state(self):
        prev_pos = self.sensor_state['position']
        current_pos = self.get_position()   
        self.sensor_state['position'] = current_pos
        self.sensor_state['velocity'] = (current_pos - prev_pos) / (self.tick_speed / 1000)
        self.sensor_state['min_limit'] = GPIO.input(self.min_limit_pin)
        self.sensor_state['max_limit'] = GPIO.input(self.max_limit_pin)
        self.sensor_state['power'] = GPIO.input(self.power_pin)
        self.sensor_state['main_up'] = self.main_up_pin.read()
        self.sensor_state['main_down'] = self.main_down_pin.read()
        self.sensor_state['secondary_up'] = self.secondary_up_pin.read()
        self.sensor_state['secondary_down'] = self.secondary_down_pin.read()

        if self.log_state:
            print(chr(27) + "[2J") # Clear the terminal
            print(f"Position: ----- {current_pos}")
            print(f"Velocity: ----- {self.sensor_state['velocity']}")
            print(f"Min: ---------- {self.sensor_state['min_limit']}")
            print(f"Max: ---------- {self.sensor_state['max_limit']}")
            print(f"Power: -------- {self.sensor_state['power']}")
            print(f"Up: ----------- {self.sensor_state['main_up']}")
            print(f"Down: --------- {self.sensor_state['main_down']}")
            print(f"Secondary Up: - {self.sensor_state['secondary_up']}")
            print(f"Secondary Down: {self.sensor_state['secondary_down']}")

    def main_loop(self):
        gpio_moving = False
        while True:
            time.sleep(self.tick_speed / 1000)
            self.set_sensor_state()
            if self.sensor_state['power']:
                self.shutdown()
                break

            # not gpio_moving isn't put into its own block because each of the if statements are mutually exclusive

            if not gpio_moving and self.sensor_state['main_up'] and self.sensor_state['main_down']:
                self.state = SYSTEM_STATE.LOCK
                self.stop()
                gpio_moving = True
            
            if not gpio_moving and self.sensor_state['main_up']:
                self.state = SYSTEM_STATE.MOVING
                self.move(10 * self.sensor_state['main_up'])
                gpio_moving = True
            
            if not gpio_moving and self.sensor_state['main_down']:
                self.state = SYSTEM_STATE.MOVING
                self.move(-10 * self.sensor_state['main_down'])
                gpio_moving = True
            
            if not gpio_moving and self.sensor_state['secondary_up'] and self.sensor_state['secondary_down']:
                self.state = SYSTEM_STATE.LOCK
                self.stop()
                gpio_moving = True
            
            if not gpio_moving and self.sensor_state['secondary_up']:
                self.state = SYSTEM_STATE.MOVING
                self.move(10 * self.sensor_state['secondary_up'])
                gpio_moving = True
            
            if not gpio_moving and self.sensor_state['secondary_down']:
                self.state = SYSTEM_STATE.MOVING
                self.move(-10 * self.sensor_state['secondary_down'])
                gpio_moving = True


            # If it was moving with the GPIO and now it's not, stop
            if gpio_moving and not self.sensor_state['main_up'] and not self.sensor_state['main_down'] and not self.sensor_state['secondary_up'] and not self.sensor_state['secondary_down']:
                self.stop()
                gpio_moving = False
                self.state = SYSTEM_STATE.STAND_BY

            command: Command = self.command_queue.get()
            allowed_commands = COMMANDS.keys()

            if command['command'] not in allowed_commands:
                continue

            if command['command'] == 'go_to' and self.state == SYSTEM_STATE.STAND_BY:
                asyncio.create_task(self.go_to(command['args']))

            if command['command'] == 'move' and self.state == SYSTEM_STATE.STAND_BY:
                self.state = SYSTEM_STATE.MOVING
                self.move(command['args'])

            if command['command'] == 'shutdown':
                self.force_stop = True
                asyncio.create_task(self.shutdown())
                break

            if command['command'] == 'calibrate' and self.state == SYSTEM_STATE.STAND_BY:
                asyncio.create_task(self.calibrate())
            
            if command['command'] == 'home' and self.state == SYSTEM_STATE.STAND_BY:
                asyncio.create_task(self.to_min())

            if command['command'] == 'stop':
                self.force_stop = True
                self.stop()
                self.state = SYSTEM_STATE.STAND_BY