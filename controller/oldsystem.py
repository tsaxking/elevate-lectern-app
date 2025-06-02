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
from sensors import Switch, Potentiometer, Ultrasonic, UltrasonicConfig, TOF
from time import sleep
from enum import Enum, auto
from Q import Queue, Command
from osc import OSC_Server, OSC_Config, AsyncOSCServer
import threading
import socket
import json
from led import LED, Brightness, FlashingSpeed
from preset import Preset, Show
import select
from utils import round
import math
# import keyboard
import time
import subprocess
import asyncio

def clear():
    print(chr(27) + "[2J")

TICK_SPEED = 15
MAX_SPEED = .5
ACCEL_RATE = 0.08 # Acceleration rate
SPEED_TOLERANCE = 0.05
POS_TOLERANCE = .5
SLOW_DOWN_DISTANCE = 2
LIMIT_SLOW_DOWN_DISTANCE = 3
LIMIT_SLOW_DOWN_SPEED = 0.35
LOWER_POSITION_OFFSET = 0
UPPER_POSITION_OFFSET = 27 # in
FAIL_STATE_TOLERANCE = 3 # in/s
FIXED_SPEED = 0.5

UDP_TICK_SPEED = TICK_SPEED * 10
UDP_PORT = 41234
E_STOP_PORT = 11111
OSC_PORT = 12321
SIG_FIGS = 2


class SystemConfig(TypedDict):
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
    start_pos: float
    gpio_moving: bool
    gpio_target_motor_speed: float
    motor_state: MotorState
    proximity_up: float
    proximity_down: float

class DualPos:
    def __init__(self, config: SystemConfig):
        self.down = Ultrasonic(UltrasonicConfig(
            echo=config['down_echo_pin'],
            trig=config['down_trigger_pin'],
            threading=True,
            tick_speed=100,
            offset=0
        ))
        self.up = Ultrasonic(
            UltrasonicConfig(
                echo=config['up_echo_pin'],
                trig=config['up_trigger_pin'],
                threading=True,
                tick_speed=TICK_SPEED,
                offset=0
            )
        )

    def read():
        up = self.up.read()
        down = self.down.read()
        if up < down:
            return up + UPPER_POSITION_OFFSET
        else:
            return down + LOWER_POSITION_OFFSET

class Sensors:
    def __init__(self, config: SystemConfig):
        GPIO.setmode(GPIO.BCM)
        self.position = TOF()
        # self.position = DualPos(config)
        # self.position = Ultrasonic(UltrasonicConfig(
        #     echo=config['echo_pin'],
        #     trig=config['trigger_pin'],
        #     threading=True,
        #     tick_speed=100,
        #     offset=LOWER_POSITION_OFFSET
        # ))
        # self.up_position = Ultrasonic(
        #     UltrasonicConfig(
        #         echo=config['up_echo_pin'],
        #         trig=config['up_trigger_pin'],
        #         threading=True,
        #         tick_speed=TICK_SPEED,
        #         offset=UPPER_
        #     )
        # )
        self.max_limit = Switch(config['max_limit_pin'], True)
        self.min_limit = Switch(config['min_limit_pin'], True)
        self.power = Switch(config['power_pin'], False)
        self.main_up = Switch(config['main_up_pin'], False)
        self.main_down = Switch(config['main_down_pin'], False)
        self.secondary_up = Switch(config['secondary_up_pin'], False)
        self.secondary_down = Switch(config['secondary_down_pin'], False)
        # self.main_speed = Potentiometer(config['main_speed_channel'])
        # self.secondary_speed = Potentiometer(config['secondary_speed_channel'])


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
            # main_speed=round(self.main_speed.read(), SIG_FIGS),
            # secondary_speed=round(self.secondary_speed.read(), SIG_FIGS)
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

    def print(self):
        state = self.read()
        clear() # Clear screen
        # print(f'Position: -------- {state["position"]}')
        # print(f'Velocity: -------- {state["velocity"]}')
        # print(f'Min Limit: ------- {state["min_limit"]}')
        print(f'Max Limit: ------- {state["max_limit"]}')
        print(f'Power: ----------- {state["power"]}')
        print(f'Main Up: --------- {state["main_up"]}')
        print(f'Main Down: ------- {state["main_down"]}')
        # print(f'Secondary Up: ---- {state["secondary_up"]}')
        # print(f'Secondary Down: -- {state["secondary_down"]}')
        print(f'Main Speed: ------ {state["main_speed"]}')
        # print(f'Secondary Speed: - {state["secondary_speed"]}')





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
        self.velocity = 0
        self.average_velocity = 0



class System:
    def __init__(self, motor: Motor, config: SystemConfig):
        GPIO.setmode(GPIO.BCM)
        self.motor = motor
        self.sensors = Sensors(config)
        self.target_motor_speed = 0
        self.speed_multiplier = 1
        self.gpio_target_motor_speed = 0
        self.prev_speed = 0
        self.state = SYSTEM_STATE.STAND_BY
        self.config = config
        self.command_ready = False
        self.gpio_moving = False
        self.lock_gpio = False
        self.Q = Queue()
        self.target_pos = -1
        self.start_pos = -1
        self.fail_state = False
        self.target_pos_with_time = -1
        self.velocity = 0
        self.prev_pos = -1
        self.osc = AsyncOSCServer(OSC_Config(
            ip="0.0.0.0",
            port=OSC_PORT,
            queue=self.Q,
            threading=True,
        ))

        self.global_state = GlobalState.RUNNING
        self.on = True
        self.calibration_state = CalibrationState.DONE
        self.calibration = Calibration()
        # self.prev_calibration = None # used if there is a stop command while the system is calibrating, it will go back to this calibration
        self.current_command = None
        # self.max = 1
        # self.min = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.status_led = LED(config['status_led_pin'], config['tick_speed'], True)
        self.osc_led = LED(config['osc_led_pin'], config['tick_speed'], True)
        self.stop_timer = 0
        # List of all TCP ip connections (strings)
        self.connections = []

    def set_speed(self, speed: float):
        # self.motor.set_speed(speed * MAX_SPEED)
        self.prev_speed = self.motor.speed
        self.target_motor_speed = speed * MAX_SPEED

    def stop(self):
        self.target_motor_speed = 0
        self.gpio_target_motor_speed = 0
        self.target_pos = -1
        self.start_pos = -1

    def cleanup(self):
        self.on = False
        self.osc.stop()
        self.motor.cleanup()
        self.sensors.cleanup()
        GPIO.cleanup()

    def go_to(self, pos: float):
        # If not calibrated, return
        if self.calibration_state != CalibrationState.DONE:
            return
        self.target_pos = pos

    def go_to_in(self, pos: float, time: float):
        # If not calibrated, return
        if self.calibration_state != CalibrationState.DONE:
            return
        # Estimate velocity given current position, and target position
        distance = pos - self.sensors.read()['position']
        velocity = distance / time
        # min max to -1 +1
        velocity = max(-1, min(1, velocity))
        self.target_pos_with_time = pos
        self.set_speed(velocity)
        

    def go_to_preset(self, preset: str):
        # If not calibrated, return
        if self.calibration_state != CalibrationState.DONE:
            return
        # Ensure preset looks like <number>.<number>
        p = preset.split('.')

        if len(p) != 2:
            return
        try:
            show_id = int(p[0])
            preset_id = int(p[1])
            def load_json_async():
                with open(f'/home/taylorpi/Documents/shows/show-{show_id}.json', 'r') as file:
                    data: Show = json.load(file)
                    for p in data['presets']:
                        if p['id'] == preset_id:
                            print(f'Going to preset {p["name"]}')
                            self.go_to(p['state']['height'])
                            break
                    
            thread = threading.Thread(target=load_json_async, args=())
            thread.start()
        except ValueError:
            return

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

    def command_handler(self):
        '''
        This function handles incoming commands from the OSC and TCP server. It will run the server in a separate thread, and run each command sync in that thread
        and wait for the command to finish before moving on to the next command.

        The command handler will also handle emergency stop commands from the TCP server generated by the e_stop_server() function
        '''
        def run_command(command: Command):
            '''
                Runs the command in a separate thread
            '''
            # print(f"Preparing to run command {command}")
            while self.on:
                name = command['command'].split(' ')[0].split('/')
                pos = self.sensors.position.read()
                if self.stop_timer > 0:
                    return
                if self.command_ready:
                    # print(f"running command {command}")
                    if name[1] == 'move':
                        self.set_speed(float(name[2]))
                        self.command_ready = True
                        break
                    if name[1] == 'stop':
                        self.Q.clear()
                        self.target = pos
                        self.target_motor_speed = 0
                        self.gpio_target_motor_speed = 0
                        self.stop()
                        self.command_ready = True
                        self.target_pos_with_time = pos
                        self.stop_timer = 10
                        break
                    if name[1] == 'test':
                        print('TEST SUCCESSFUL')
                        break
                    if name[1] == 'go_to':
                        if name[2] == 'in':
                            self.go_to_in(float(name[2]), float(name[3]))
                        else:
                            self.go_to(float(name[2]))
                        break
                    if name[1] == 'bump':
                        self.set_speed(float(name[2]))
                        sleep(1)
                        self.stop()
                        break
                    if name[1] == 'preset':
                        self.command_ready = False
                        self.go_to_preset(str(name[2]))
                        break
                    if name[1] == 'shutdown':
                        self.command_ready = False
                        self.shut_down()
                        break
                    if name[1] == 'calibrate':
                        self.command_ready = False
                        self.run_calibration()
                        break
                    if command[1] == 'release_fail':
                        self.fail_state = False
                        break
                sleep(TICK_SPEED / 1000)

        def start_queue_handler():
            while self.on:
                command = self.Q.get()
                if command:
                    self.current_command = command
                    try:
                        run_command(command)
                    except Exception as e:
                        print(f"Error running command {command} - {e}")
                        self.stop()
                        self.command_ready = True
                sleep(TICK_SPEED / 1000)

        def e_stop_server():
            async def handle_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
                addr = writer.get_extra_info('peername')
                print(f"Connection from {addr}")
                self.connections.append(addr[0])

                try:
                    while self.on:
                        data = await reader.read(1024)
                        message = data.decode().strip()
                        print(f"Received: {message}")
                        if message == "stop":
                            print('Stopping system')
                            self.Q.clear()
                            self.stop()
                except Exception as e:
                    print(f"Error with connection {addr}: {e}")
                    try:
                        writer.close()
                        await writer.wait_closed()
                        self.connections.remove(addr[0])
                    except Exception as e:
                        print(f"Error closing connection {addr}: {e}")
                    print(f"Connection with {addr} closed")

            async def start_handler():
                server = await asyncio.start_server(handle_connection, '0.0.0.0', E_STOP_PORT)
                print(f"Server listening on 0.0.0.0:{E_STOP_PORT}")
                async with server:
                    await server.serve_forever()

            def thread_runner():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(start_handler())

            t = threading.Thread(target=thread_runner, daemon=True)
            t.start()

        q_thread = threading.Thread(target=start_queue_handler)
        q_thread.daemon = True
        q_thread.start()
        e_stop_server()

    def emit_state(self):

        # def send_state(state: UDPSystemState):
        # # def send_state(state: str, value):
        #     for connection in self.connections:
        #         try:
        #             # print(f'Emitting to {connection} {state}')
        #             # self.socket.sendto(
        #             #     # f'CUSTOM-VARIABLE lectern_{state} SET-VALUE {value}'.encode('utf-8'),
        #             #     # f'{state} {value}'.encode('utf-8'),
        #             #     json.dumps(state).encode('utf-8'),
        #             #     (connection[0], 11111)
        #             # )
        #         except Exception as e:
        #             try:
        #                 print(f"Error sending state: {e}")
        #                 self.connections.remove(connection)
        #                 connection.close()
        #                 print("Connection closed")
        #             except Exception as e:
        #                 print(f"Error closing connection: {e}")
        #                 break
        #             break
        def run():
            # calibration_sent = False
            while self.on:
                S = self.sensors.read()
                state = UDPSystemState(
                    sensors=S,
                    motor_speed=round(self.motor.speed / MAX_SPEED, SIG_FIGS),
                    state=self.state.to_dict(),
                    command_ready=self.command_ready,
                    gpio_moving=self.gpio_moving,
                    target_speed=round(self.target_motor_speed, SIG_FIGS),
                    gpio_target_motor_speed=round(self.gpio_target_motor_speed, SIG_FIGS),
                    backlog = self.Q.to_dict()['queue'],
                    current_command = self.current_command,
                    target_pos=round(self.target_pos, SIG_FIGS),
                    start_pos=round(self.start_pos, SIG_FIGS),
                    velocity=round(self.get_velocity(), SIG_FIGS),
                    motor_state=self.motor.state.to_dict(),
                    global_state=self.global_state.to_dict(),
                    proximity_up=round(self.calibration.top - S['position'], SIG_FIGS), #if self.calibration_state == CalibrationState.DONE and abs(self.calibration.top - S['position']) <= LIMIT_SLOW_DOWN_DISTANCE else 9999,
                    proximity_down=round(S['position'] - self.calibration.bottom, SIG_FIGS), #if self.calibration_state == CalibrationState.DONE and abs(S['position'] - self.calibration.bottom) <= LIMIT_SLOW_DOWN_DISTANCE else -9999,
                    calibration=self.calibration.__dict__,
                    speed_multiplier=round(self.speed_multiplier, SIG_FIGS)
                )
                # self.udp_server.sendto(
                #     json.dumps(state).encode('utf-8'),
                #     ('0.0.0.0', UDP_PORT)
                # )
                self.socket.sendto(
                    json.dumps(state).encode('utf-8'),
                    ('localhost', UDP_PORT)
                )
                for connection in self.connections:
                    try:
                        self.socket.sendto(
                            json.dumps(state).encode('utf-8'),
                            (connection, UDP_PORT)
                        )
                        # print(f"Sent State to {connection}")
                    except Exception as e:
                        try:
                            print(f"Error sending state: {e}")
                            self.connections.remove(connection)
                            print("Connection closed")
                        except Exception as e:
                            print(f"Error closing connection: {e}")
                            break
                        break
                # send_state(state)
                # send_state('status', self.global_state.to_dict())
                # send_state('state', self.state.to_dict())
                # send_state('target', round(self.target_pos, SIG_FIGS))
                # send_state('position', round(S['position'], SIG_FIGS))
                # send_state('ready', self.command_ready)
                # send_state('calibrated', self.calibration_state == CalibrationState.DONE)
                # send_state('fail', self.is_fail_state())
                # if not calibration_sent and self.calibration_state == CalibrationState.DONE:
                #     self.socket.sendto(
                #         json.dumps(self.calibration.__dict__).encode('utf-8'),
                #         ('localhost', UDP_PORT)
                #     )
                #     calibration_sent = True
                sleep(UDP_TICK_SPEED / 1000)

        t = threading.Thread(target=run)
        t.daemon = True
        t.start()

    def set_led_state(self):
        if self.global_state == GlobalState.STARTUP or self.global_state == GlobalState.SHUTDOWN or self.calibration_state != CalibrationState.DONE:
            self.status_led.brightness = Brightness.LOW
            self.status_led.flashing_speed = FlashingSpeed.SLOW
            self.osc_led.brightness = Brightness.LOW
            self.osc_led.flashing_speed = FlashingSpeed.SLOW
            return

        if self.state == SYSTEM_STATE.MOVING:
            self.status_led.brightness = Brightness.MEDIUM
            self.status_led.flashing_speed = FlashingSpeed.SLOW

        if self.state == SYSTEM_STATE.ACCELERATING:
            self.status_led.brightness = Brightness.MEDIUM
            self.status_led.flashing_speed = FlashingSpeed.FAST

        if self.state == SYSTEM_STATE.STAND_BY:
            self.status_led.brightness = Brightness.HIGH
            self.status_led.flashing_speed = FlashingSpeed.NONE

        if self.state == SYSTEM_STATE.LOCK:
            self.status_led.brightness = Brightness.HIGH
            self.status_led.flashing_speed = FlashingSpeed.FAST

        if self.state == SYSTEM_STATE.CALIBRATING:
            self.status_led.brightness = Brightness.MEDIUM
            self.status_led.flashing_speed = FlashingSpeed.MEDIUM

        if self.Q.qsize() > 0:
            self.osc_led.brightness = Brightness.HIGH
            self.osc_led.flashing_speed = FlashingSpeed.FAST
        else:
            self.osc_led.brightness = Brightness.OFF
            self.osc_led.flashing_speed = FlashingSpeed.NONE

    def get_velocity(self): # in/s
        if self.calibration.average_velocity == 0:
            return 0
        vel = self.calibration.velocity / self.calibration.average_velocity * self.velocity
        if vel == 0:
            return 0
        return round(vel, SIG_FIGS)

    def expected_velocity(self): # in/s
        vel = self.motor.speed * self.calibration.velocity / MAX_SPEED
        if vel == 0:
            return 0.0
        return round(vel, SIG_FIGS)

    def vel_delta(self):
        # TODO: This will be used to assess a fail state
        expect = self.expected_velocity()
        if expect == 0:
            return 1
        return self.get_velocity() / expect 

    def calibrate(self):
        print('Starting calibration')
        self.global_state = GlobalState.CALIBRATING
        max_speed = .4
        min_speed = .2

        # Assume this is on a different thread
        self.calibration_state = CalibrationState.MAX_FAST
        self.set_speed(max_speed)
        max_height = 0
        print('Calibrating max height')
        while self.on and not self.sensors.max_limit.read():
            max_height = self.sensors.read()['position']
            sleep(TICK_SPEED / 1000)
        self.stop() # Probably not necessary since it hit the limit
        self.calibration_state = CalibrationState.MAX_SLOW
        self.set_speed(-max_speed)
        sleep(1)
        self.set_speed(min_speed)
        print('Calibrating max height again, but slowly...')
        while self.on and not self.sensors.max_limit.read():
            max_height = self.sensors.read()['position']
            sleep(TICK_SPEED / 1000)

        self.stop() # Again, probably not necessary
        self.calibration.top = max_height - 0.5
        sleep(1)

        # This next step takes the longest time, so calibrate velocity as well
        self.calibration_state = CalibrationState.MIN_FAST
        start_time = time.time() * 1000
        self.set_speed(-max_speed)
        min_height = 0
        points = []
        print('Calibrating min height and velocity')
        # print(self.sensors.min_limit.read())
        while self.on and not self.sensors.min_limit.read():
            min_height = self.sensors.read()['position']
            points.append(self.velocity)
            sleep(TICK_SPEED / 1000)
        num_points = len(points)

        distance = max_height - min_height
        self.calibration.velocity = round(((distance / abs(time.time() * 1000 - start_time)) / max_speed) * 1000, SIG_FIGS) # in/s
        if num_points > 0:
            self.calibration.average_velocity = -1 * round(sum(points) / len(points), SIG_FIGS) * (1 / max_speed)
        
        self.stop()
        self.calibration_state = CalibrationState.MIN_SLOW
        self.set_speed(max_speed)
        sleep(1)
        self.set_speed(-min_speed)
        print('Calibrating min height again, but slowly...')
        while self.on and not self.sensors.min_limit.read():
            min_height = self.sensors.read()['position']
            sleep(TICK_SPEED / 1000)
        self.stop()
        self.calibration.bottom = min_height + 0.5
        self.calibration_state = CalibrationState.DONE

        print('Calibration complete')
        print(f'Results: {self.calibration.__dict__}')
        self.global_state = GlobalState.RUNNING

    def run_calibration(self):
        self.global_state = GlobalState.STARTUP
        thread = threading.Thread(target=self.calibrate, args=())
        thread.daemon = True
        thread.start()

    def shut_down(self):
        def run_shutdown():
            self.set_speed(-0.5)
            while self.on and not self.sensors.min_limit.read() or self.sensors.position.read() <= self.calibration.bottom:
                sleep(TICK_SPEED / 1000)
            self.stop() # Probably isn't necessary because it should be at the limit
            self.on = False
            self.cleanup()
            subprocess.run(['sudo', 'shutdown', '0'])
            exit()

        self.global_state = GlobalState.SHUTDOWN
        thread = threading.Thread(target=run_shutdown)
        thread.daemon = True
        thread.start()

    def kill(self):
        print('Received kill signal')
        self.set_speed(0)
        self.on = False
        self.cleanup()
        exit()

    def fail_state_cb(self):
        print('FAIL STATE DETECTED')
        # self.fail_state = True
        # self.motor.disable()
        # self.set_speed(0)
        # self.target_pos = self.sensors.read()['position']
        # self.gpio_moving = False
        # self.command_ready = False

    def is_fail_state(self):
        if self.state == SYSTEM_STATE.ACCELERATING:
            return False
        return abs(self.get_velocity() - self.expected_velocity()) > FAIL_STATE_TOLERANCE

    def start_up(self):
        self.set_speed(0.3)
        sleep(0.5)
        self.set_speed(-0.3)
        sleep(0.5)
        self.set_speed(0)

    def event_loop(self):
        # self.run_calibration()
        self.gpio_moving = False
        locked = False
        # start_server(self.Q, "localhost", OSC_PORT)
        self.osc.start()
        self.emit_state()
        self.command_handler()
        prev_pos = None
        start_power = None
        while self.on:
            # print(f'Velocity delta: {self.vel_delta()}')
            # If spacebar is pressed, stop the system
            # if keyboard.is_pressed('space'):
            #     self.kill()
            #     return
            sensors = self.sensors.read()
            # print(f'GPIOMOVING: {self.gpio_moving}')
            # print(f'LOCKED: {locked}')
            # if self.config['log_state']:
            # self.print_state()

            # print(sensors)

            if sensors['power']:
                if start_power is None:
                    start_power = time.time()
                else:
                    if time.time() - start_power > 5:
                        self.shut_down()
            else:
                start_power = None

            if self.is_fail_state() and self.global_state != GlobalState.CALIBRATING:
                self.fail_state_cb()

            if self.global_state != GlobalState.CALIBRATING:
                if sensors['main_up'] and sensors['main_down']:
                    locked = True
                    self.stop()
                    self.gpio_moving = True
                    self.command_ready = False

                if not self.gpio_moving and sensors['main_up']:
                    self.gpio_target_motor_speed = 1
                    self.gpio_moving = True
                    self.command_ready = False

                if not self.gpio_moving and sensors['main_down']:
                    self.gpio_target_motor_speed = -1
                    self.gpio_moving = True
                    self.command_ready = False

                if self.gpio_moving and not sensors['main_up'] and not sensors['main_down']:
                    self.stop()
                    self.gpio_moving = False
                    locked = False
                    self.command_ready = True

                if not self.gpio_moving:
                    if sensors['secondary_up'] and sensors['secondary_down']:
                        locked = True
                        self.stop()
                        self.gpio_moving = True
                        self.command_ready = False

                    if not self.gpio_moving and sensors['secondary_up']:
                        self.gpio_target_motor_speed = 1
                        self.gpio_moving = True
                        self.command_ready = False

                    if not self.gpio_moving and sensors['secondary_down']:
                        self.gpio_target_motor_speed = -1
                        self.gpio_moving = True
                        self.command_ready = False

                    if self.gpio_moving and not sensors['secondary_up'] and not sensors['secondary_down']:
                        self.stop()
                        self.gpio_moving = False
                        locked = False
                        self.command_ready = True

                # GPIO Target Speeds
                if self.gpio_target_motor_speed and self.gpio_moving and not locked:
                    self.set_speed(self.gpio_target_motor_speed * FIXED_SPEED)
                    self.command_ready = False

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

                slow_down = abs(distance_to_target) - SLOW_DOWN_DISTANCE if abs(distance_to_target) < SLOW_DOWN_DISTANCE else 0
                if distance_to_target > 0 and not reached:
                    self.set_speed(1 + slow_down / 50)
                elif distance_to_target < 0 and not reached:
                    self.set_speed(-1 - slow_down / 50)

                if reached:
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

                slow_down = abs(distance_to_target) - SLOW_DOWN_DISTANCE if abs(distance_to_target) < SLOW_DOWN_DISTANCE else 0
                if distance_to_target > 0 and not reached:
                    self.set_speed(1 + slow_down / 50)
                elif distance_to_target < 0 and not reached:
                    self.set_speed(-1 - slow_down / 50)

                if reached:
                    self.stop()
                    self.target_pos = -1
                    self.start_pos = -1
                    distance_to_target = 0
                    self.command_ready = True

            stop = False

            # If the system is calibrated, and it is close to a limit, slow down drastically as it approaches
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

            if self.speed_multiplier < LIMIT_SLOW_DOWN_SPEED:
                self.speed_multiplier = LIMIT_SLOW_DOWN_SPEED


            if self.target_motor_speed == 0 and abs(self.motor.speed) < SPEED_TOLERANCE or stop:
                self.prev_speed = 0
                self.motor.disable()
                self.state = SYSTEM_STATE.STAND_BY
                self.command_ready = True

            if locked:
                self.state = SYSTEM_STATE.LOCK
                self.command_ready = False

            if self.state == SYSTEM_STATE.LOCK:
                self.stop()

            self.set_led_state()

            if prev_pos:
                # TODO: throw away velocity based on the calibration state and motor speed
                self.velocity = sensors['position'] - prev_pos

            prev_pos = sensors['position']

            if self.global_state == SYSTEM_STATE.CALIBRATING:
                self.command_ready = False

            if self.stop_timer > 0:
                self.stop_timer = self.stop_timer - 1

            sleep(TICK_SPEED / 1000)


    


