from motor import Motor
import RPi.GPIO as GPIO
import asyncio
from control import trapezoidal_velocity_control, pid_control, PID, TrapezoidalProfile
from typing import TypedDict, Any
import json
from potentiometer import Potentiometer

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
    motor: Motor
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

class System:
    def __init__(self, motor: Motor, config: SystemConfig):
        """
        Initializes the system object.
        
        :param motor: Motor object.
        """
        self.motor = motor
        self.position_pin = config['position_pin']
        self.tick_speed = config['tick_speed']
        self.max_limit_pin = config['max_limit_pin']
        self.min_limit_pin = config['min_limit_pin']
        self.power_pin = config['power_pin']
        self.main_up_pin = Potentiometer(config['up_pin'])
        self.main_down_pin = Potentiometer(config['down_pin'])
        self.secondary_up_pin = Potentiometer(config['secondary_up_pin'])
        self.secondary_down_pin = Potentiometer(config['secondary_down_pin'])
        # self.up_pin = config['up_pin']
        # self.down_pin = config['down_pin']
        self.log_state = config['log_state']

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.position_pin, GPIO.IN)
        GPIO.setup(self.max_limit_pin, GPIO.IN)
        GPIO.setup(self.min_limit_pin, GPIO.IN)
        GPIO.setup(self.power_pin, GPIO.IN)
        GPIO.setup(self.main_up_pin, GPIO.IN)

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
        """Returns the normalized current position of the system."""
        
        min = self.get_min()
        pos = GPIO.input(self.position_pin) - min
        max = self.get_max() - min

        return pos / max
    
    async def _set_sensing_loop(self):
        """Periodically calculates the velocity of the system."""
        # async code to calculate velocity
        gpio_moving = False
        while True:
            start_pos = self.get_position()
            await asyncio.sleep(self.tick_speed / 1000)
            end_pos = self.get_position()
            self.velocity = (end_pos - start_pos) / (self.tick_speed / 1000)

            if self.log_state:
                print(chr(27) + "[2J") # Clear the terminal
                print(f"Position: {end_pos}")
                print(f"Velocity: {self.velocity}")
                print(f"Min:      {self.min_on()}")
                print(f"Max:      {self.max_on()}")
                print(f"Power:    {GPIO.input(self.power_pin)}")
                print(f"Up:       {GPIO.input(self.main_up_pin)}")
                print(f"Down:     {GPIO.input(self.main_down_pin)}")

            if GPIO.input(self.power_pin):
                self.shutdown()

            # If recieving two conflicting signals, stop
            if self.main_up_pin.read() or self.main_down_pin.read():
                if self.main_up_pin.read() and self.main_down_pin.read():
                    self.stop()
                else:
                    if self.main_up_pin.read():
                        self.force_stop = True
                        gpio_moving = True
                        self.move(10 * self.main_up_pin.read())

                    if self.main_down_pin.read():
                        self.force_stop = True
                        gpio_moving = True
                        self.move(-10 * self.main_down_pin.read())
            elif self.secondary_up_pin.read() or self.secondary_down_pin.read():
                if self.secondary_up_pin.read() and self.secondary_down_pin.read():
                    self.stop()
                else:
                    if self.secondary_up_pin.read():
                        self.force_stop = True
                        gpio_moving = True
                        self.move(10 * self.secondary_up_pin.read())

                    if self.secondary_down_pin.read():
                        self.force_stop = True
                        gpio_moving = True
                        self.move(-10 * self.secondary_down_pin.read())

            if gpio_moving and not GPIO.input(self.main_up_pin) and not GPIO.input(self.main_down_pin):
                gpio_moving = False
                self.stop()

    def min_on(self):
        return GPIO.input(self.min_limit_pin)
    
    def max_on(self):
        return GPIO.input(self.max_limit_pin)
    
    def go_to(self, desired_position: int):
        """Moves the system to the specified position."""
        self.force_stop = False

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

        profile: TrapezoidalProfile = {
            'MAX_VELOCITY': 100,
            'ACCELERATION': 10,
            'DECELERATION': 10,
            'tick_speed': self.tick_speed
        }

        while abs(desired_position - self.get_position()) > TARGET_RANGE:
            if self.force_stop:
                self.force_stop = False
                break


            # If it surpasses the target position, stop
            if current < desired_position and self.get_position() > desired_position:
                break

            if current > desired_position and self.get_position() < desired_position:
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

    # inverts the min and max values if the sensor outputs the signal in reverse
    def get_max(self):
        return self.max if self.max > self.min else self.min
    
    def get_min(self):
        return self.min if self.max > self.min else self.max

    async def _command_loop(self):
        """Command loop for the system."""
        # async code to handle commands
        while True:
            command: Command = await self.command_queue.get()
            allowed_commands = COMMANDS.keys()

            if command['command'] not in allowed_commands:
                continue

            if command['command'] == 'end':
                self.stop()
                self.motor.cleanup()
                break
            elif command['command'] == 'go_to':
                self.go_to(command['args'])
            elif command['command'] == 'move':
                self.move(command['args'])
            elif command['command'] == 'stop':
                self.stop()
            elif command['command'] == 'home':
                await self.go_to(0)
            elif command['command'] == 'calibrate':
                await self.calibrate()
            elif command['command'] == 'shutdown':
                await self.shutdown()

    async def send_command(self, command: Command):
        """Sends a command to the system."""
        await self.command_queue.put(command)

    async def calibrate(self):
        await self.to_max()
        await self.to_min()

    async def startup(self):
        """Starts the system."""
        await self.calibrate()
        self.load_state()

    async def shutdown(self):
        """Shuts down the system."""
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