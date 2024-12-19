from motor import Motor
import RPi.GPIO as GPIO
import asyncio
from control import trapezoidal_velocity_control, pid_control, PID
from typing import TypedDict
import json

class Command(TypedDict):
    command: str
    args: dict

ALLOWED_COMMANDS = ['go_to', 'move', 'end']

TARGET_RANGE = 0.05 # The range of the target position that is considered "reached"

class System:
    def __init__(self, motor: Motor, position_pin: int, tick_speed: int, max_limit_pin: int, min_limit_pin: int):
        """
        Initializes the system object.
        
        :param motor: Motor object.
        """
        self.motor = motor
        self.position_pin = position_pin
        self.tick_speed = tick_speed
        self.max_limit_pin = max_limit_pin
        self.min_limit_pin = min_limit_pin

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.position_pin, GPIO.IN)
        GPIO.setup(self.max_limit_pin, GPIO.IN)
        GPIO.setup(self.min_limit_pin, GPIO.IN)

        self.velocity = 0
        self.min = 0
        self.max = 100 # Will be changed after calibration
        self.force_stop = False

        # Start velocity calculation loop in the background
        asyncio.create_task(self._set_sensing_loop())
        # Command queue for asynchronous command handling
        self.command_queue: asyncio.Queue = asyncio.Queue()
        asyncio.create_task(self._command_loop())

    def get_position(self) -> float:
        """Returns the current position of the system."""
        
        min = self.min
        pos = GPIO.input(self.position_pin) - min
        max = self.max - min

        return pos / max
    
    async def _set_sensing_loop(self):
        """Periodically calculates the velocity of the system."""
        # async code to calculate velocity
        while True:
            start_pos = self.get_position()
            await asyncio.sleep(self.tick_speed / 1000)
            end_pos = self.get_position()
            self.velocity = (end_pos - start_pos) / (self.tick_speed / 1000)

    def min_on(self):
        return GPIO.input(self.min_limit_pin)
    
    def max_on(self):
        return GPIO.input(self.max_limit_pin)
    
    def go_to(self, desired_position: int):
        """Moves the system to the specified position."""

        if desired_position < 0 or desired_position > 1:
            return

        # If it's at its limit and wants to go further, do nothing
        # This is to prevent the motor from trying to move past its limits
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

        while abs(desired_position - self.get_position()) > TARGET_RANGE:
            if self.force_stop:
                self.force_stop = False
                break

            desired_velocity = trapezoidal_velocity_control(
                current_pos=self.get_position(),
                target_pos=desired_position,
                current_vel=self.velocity,
                profile={
                    'MAX_VELOCITY': 100,
                    'ACCELERATION': 10,
                    'DECELERATION': 10,
                    'tick_speed': self.tick_speed
                }
            )

            pwm_output = pid_control(
                setpoint=desired_velocity,
                measured=self.velocity,
                pid=pid
            )

            # If it's in motion and hits a limit, stop
            if pwm_output < 0 and self.min_on():
                self.stop()
                break
            if pwm_output > 0 and self.max_on():
                self.stop()
                break

            self.motor.set_speed(pwm_output)

    def move(self, speed: float):
        """Moves the system at the specified speed."""
        self.motor.set_speed(speed)

    def stop(self):
        """Stops the system."""
        self.motor.stop()
        self.force_stop = True

    async def to_min(self):
        """Moves the system to the home position."""
        # Implement this function
        # Ignore self.force_stop value
        # I don't know if this will block the thread

        while not self.min_on():
            self.move(-10)
            await asyncio.sleep(self.tick_speed / 1000)

        self.move(5)
        await asyncio.sleep(0.1)

        # Slower speed
        while not self.min_on():
            self.move(-1)
            await asyncio.sleep(self.tick_speed / 100)

        self.stop()
        self.min = GPIO.input(self.position_pin)

    async def to_max(self):
        """Moves the system to the max position."""
        # Implement this function
        # Ignore self.force_stop value
        # I don't know if this will block the thread

        while not self.max_on():
            self.move(10)
            await asyncio.sleep(self.tick_speed / 1000)

        self.move(-5)
        await asyncio.sleep(0.1)

        # Slower speed
        while not self.max_on():
            self.move(1)
            await asyncio.sleep(self.tick_speed / 100)

        self.stop()
        self.max = GPIO.input(self.position_pin)

    async def _command_loop(self):
        """Command loop for the system."""
        # async code to handle commands
        while True:
            command: Command = await self.command_queue.get()
            if command['command'] not in ALLOWED_COMMANDS:
                continue

            if command['command'] == 'end':
                self.stop()
                self.motor.cleanup()
                break
            elif command['command'] == 'go_to':
                self.go_to(command['args']['position'])
            elif command['command'] == 'move':
                self.move(command['args']['speed'])
            elif command['command'] == 'stop':
                self.stop()
            elif command['command'] == 'home':
                await self.to_min()

    async def send_command(self, command: Command):
        """Sends a command to the system."""
        await self.command_queue.put(command)

    async def startup(self):
        """Starts the system."""
        await self.to_min()
        self.load_state()

    def save_state(self):
        # JSON dump the current state of the system
        str = json.dump({
            'position': self.get_position(),
            'min': self.min,
            'max': self.max
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