from typing import TypedDict
import lectern
import asyncio
import osc
import Q
import subprocess
import tcp
import socket
import json
# import queue

class SystemConfig(TypedDict):
    lectern=lectern.Lectern
    ip=str
    osc_port=int
    udp_port=int
    tcp_port=int
    emit_tick_speed=int

class System:
    def __init__(self, config: SystemConfig):
        self.osc_queue = Q.SystemQueue()
        self.tcp_queue = Q.SystemQueue()
        self.lectern: lectern.Lectern = config['lectern']
        self.tasks: list[asyncio.Task] = []
        self.emit_tick_speed = config['emit_tick_speed']
        self.udp_port = config['udp_port']
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.osc = osc.OSC_Server(
            osc.OSC_Config(
                ip=config['ip'],
                port=config['osc_port'],
                queue=self.osc_queue,
                threading=True
            )
        )
        self.tcp = tcp.TCPServer(
            host=config['ip'],
            port=config['tcp_port'],
            queue=self.tcp_queue
        )

    async def handle_lectern_osc_command(self, command: Q.System_Command):
        print(f"Running lectern command: {command.args}")
        # wait for lectern to be ready
        while not self.lectern.command_ready:
            await asyncio.sleep(self.lectern.tick_speed / 1000)
        if command.args[0] == "move":
            speed = float(command.args[1])
            if speed != speed:
                print("Speed is NaN, ignoring command")
                return
            print(f"Moving lectern at speed: {speed}")
            self.lectern.set_speed(speed)
            return
        if command.args[0] == "stop":
            self.lectern.stop()
            return
        if command.args[0] == "calibrate":
            self.lectern.run_calibration()
            return
        if command.args[0] == "go_to":
            position = float(command.args[1])
            if position != position:
                print("Position is NaN, ignoring command")
                return
            if len(command.args) < 3:
                self.lectern.go_to(position)
                return
            if command.args[2] == "in":
                time = float(command.args[3])
                if time != time:
                    print("Time is NaN, ignoring command")
                    return
                self.lectern.go_to_in(position, time)
            else:
                self.lectern.go_to(position)
            return
        if command.args[0] == "bump":
            distance = float(command.args[1])
            if distance != distance:
                print("Distance is NaN, ignoring command")
                return
            self.lectern.bump(distance)

    def handle_teleprompter_osc_command(self, command: Q.System_Command):
        print(f"Running teleprompter command: {command.args}")
    
    async def handle_osc_command(self, command: Q.System_Command):
        print(f"Running OSC command: {command.args} for {command.who}")
        if command.who == "lectern":
            await self.handle_lectern_osc_command(command)
        elif command.who == "teleprompter":
            await self.handle_teleprompter_osc_command(command)
        else:
           asyncio.create_task(self.handle_teleprompter_osc_command(command))
           asyncio.create_task(self.handle_lectern_tcp_command(command))

    async def handle_lectern_tcp_command(self, command: Q.System_Command):
        self.lectern.stop()
        self.osc_queue.clear_lectern()
        await asyncio.sleep(0.5) # wait for the motor to stop
        if command.args[0] == "stop":
            # No action needed, already stopped
            return
        if command.args[0] == "reboot":
            asyncio.create_task(self.lectern.reboot())
            return
        if command.args[0] == "home":
            self.lectern.home()
            return

    async def handle_teleprompter_tcp_command(self, command: Q.System_Command):
        print(f"Running teleprompter TCP command: {command.args} for {command.who}")

    async def handle_tcp_command(self, command: Q.System_Command):
        print(f"Running TCP command: {command.args} for {command.who}")
        if command.args[0] == "system_reboot":
            print("Rebooting system...")
            self.reboot()
        elif command.args[0] == "system_shutdown":
            print("Shutting down system...")
            self.shutdown()
        elif command.args[0] == "reboot_tcp":
            print("Rebooting Lectern TCP...")
        elif command.args[0] == "reboot_osc":
            print("Rebooting OSC...")
            self.osc.restart()

    def kill_processes(self):
        self.lectern.shutdown()
        self.osc.stop()

    def reboot(self):
        self.kill_processes()
        self.run_bash_command("sudo reboot 0")

    def shutdown(self):
        self.kill_processes()
        self.run_bash_command("sudo shutdown 0")
                              
    def run_bash_command(self, command: str):
        print(f"Running bash command: {command}")
        subprocess.run(command.split(' '))
        
    async def start(self):
        self.tasks.append(asyncio.create_task(self.lectern.start()))
        self.osc.start()
        self.tasks.append(asyncio.create_task(self.tcp.start()))
        self.tasks.append(asyncio.create_task(self.start_emitter()))
        self.tasks.append(asyncio.create_task(self.handle_osc_queue()))
        self.tasks.append(asyncio.create_task(self.handle_tcp_queue()))

    async def handle_osc_queue(self):
        print("Starting OSC queue handler")
        while True:
            command = self.osc_queue.get(
            )
            if command is None:
                await asyncio.sleep(0.1)
                continue
            try:
                await self.handle_osc_command(command)
            except Exception as e:
                print(f"Error handling OSC command: {e}")
            await asyncio.sleep(0.1)  # Prevent busy-waiting

    async def handle_tcp_queue(self):
        print("Starting TCP queue handler")
        while True:
            command = self.tcp_queue.get(
            )
            if command is None:
                await asyncio.sleep(0.1)
                continue
            try:
                await self.handle_tcp_command(command)
            except Exception as e:
                print(f"Error handling TCP command: {e}")
            await asyncio.sleep(0.1)

    async def start_emitter(self):
        print(f"Starting UDP emitter on port {self.udp_port}")
        while True:
            S = self.lectern.sensors.read()
            try:
                state = lectern.UDPSystemState(
                    sensors=S,
                    motor_speed=round(self.lectern.motor.speed / lectern.MAX_SPEED, lectern.SIG_FIGS),
                    state=self.lectern.state.to_dict(),
                    command_ready=self.lectern.command_ready,
                    gpio_moving=self.lectern.gpio_moving,
                    target_speed=round(self.lectern.target_motor_speed, lectern.SIG_FIGS),
                    gpio_target_motor_speed=round(self.lectern.gpio_target_motor_speed, lectern.SIG_FIGS),
                    # backlog = self.osc_queue.queue,
                    backlog = [],
                    current_command = None,
                    target_pos=round(self.lectern.target_pos, lectern.SIG_FIGS),
                    start_pos=round(self.lectern.start_pos, lectern.SIG_FIGS),
                    velocity=round(self.lectern.velocity, lectern.SIG_FIGS),
                    motor_state=self.lectern.motor.state.to_dict(),
                    global_state=self.lectern.global_state.to_dict(),
                    proximity_up=round(self.lectern.calibration.top - S['position'], lectern.SIG_FIGS), #if self.calibration_state == CalibrationState.DONE and abs(self.calibration.top - S['position']) <= LIMIT_SLOW_DOWN_DISTANCE else 9999,
                    proximity_down=round(S['position'] - self.lectern.calibration.bottom, lectern.SIG_FIGS), #if self.calibration_state == CalibrationState.DONE and abs(S['position'] - self.calibration.bottom) <= LIMIT_SLOW_DOWN_DISTANCE else -9999,
                    calibration=self.lectern.calibration.__dict__,
                    speed_multiplier=round(self.lectern.speed_multiplier, lectern.SIG_FIGS)
                )
            except Exception as e:
                print(f"Error creating UDP state: {e}")

            payload = json.dumps(state).encode('utf-8')

            self.socket.sendto(
                payload,
                ('localhost', self.udp_port)
            )
            for client in self.tcp.clients:
                self.socket.sendto(
                    payload,
                    client.address
                )
            await asyncio.sleep(self.emit_tick_speed / 1000)

    async def stop(self):
        # clear queues
        self.osc_queue.clear()
        self.tcp_queue.clear()
        await self.lectern.e_stop()
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        await self.lectern.cleanup()
        self.tasks.clear()
        self.osc.stop()