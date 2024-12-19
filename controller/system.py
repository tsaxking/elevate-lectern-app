from motor import Motor
import RPi.GPIO as GPIO
import asyncio
from control import trapezoidal_velocity_control, pid_control, PID
from typing import TypedDict

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
        self.offset = 0
        self.force_stop = False
        # Limit switch state
        self.max_on = False
        self.min_on = False

        # Start velocity calculation loop in the background
        asyncio.create_task(self._set_sensing_loop())
        # Command queue for asynchronous command handling
        self.command_queue: asyncio.Queue = asyncio.Queue()
        asyncio.create_task(self._command_loop())

    def get_position(self, offset = True) -> int:
        """Returns the current position of the system."""
        return GPIO.input(self.position_pin) + self.offset if offset else GPIO.input(self.position_pin)
    
    async def _set_sensing_loop(self):
        """Periodically calculates the velocity of the system."""
        # async code to calculate velocity
        while True:
            current_pos = self.get_position()
            await asyncio.sleep(self.tick_speed / 1000)
            new_pos = self.get_position()
            self.velocity = (new_pos - current_pos) / (self.tick_speed / 1000)

            self.max_on = GPIO.input(self.max_limit_pin)
            self.min_on = GPIO.input(self.min_limit_pin)
    
    def go_to(self, position: int):
        """Moves the system to the specified position."""

        pid: PID = {
            'Kp': 1.0,
            'Ki': 0.1,
            'Kd': 0.001,
            'integral': 0,
            'previous_error': 0,
            'tick_speed': self.tick_speed
        }

        while abs(position - self.get_position()) > TARGET_RANGE:
            if self.force_stop:
                self.force_stop = False
                break

            desired_velocity = trapezoidal_velocity_control(
                current_pos=self.get_position(),
                target_pos=position,
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

            self.motor.set_speed(pwm_output)

    def move(self, speed: float):
        """Moves the system at the specified speed."""
        self.motor.set_speed(speed)

    def stop(self):
        """Stops the system."""
        self.motor.stop()
        self.force_stop = True

    def home(self):
        """Moves the system to the home position."""
        # Implement this function
        # Ignore self.force_stop value
        # I don't know if this will block the thread

        while not self.min_on:
            self.move(-100)
        self.stop()
        self.offset = self.get_position(False)

    async def _command_loop(self):
        """Command loop for the system."""
        # async code to handle commands
        while True:
            command: Command = await self.command_queue.get()
            if command['command'] not in ALLOWED_COMMANDS:
                continue

            if command['command'] == 'end':
                self.motor.stop()
                self.motor.cleanup()
                break
            elif command['command'] == 'go_to':
                self.go_to(command['args']['position'])

    async def send_command(self, command: Command):
        """Sends a command to the system."""
        await self.command_queue.put(command)