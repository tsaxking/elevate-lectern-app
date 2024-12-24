from motor import Motor, MotorConfig
from system import System, SystemConfig
from time import sleep
import sys
import atexit
import signal

TICK_SPEED = 15

def main():
    motor = Motor(MotorConfig(
        pin=18,
        max=2000,
        min=1000,
        zero=1500,
        invert=False,
        tick_speed=TICK_SPEED,
        acceleration=0.02
    ))
    system = System(motor, SystemConfig(
        position_pin=0,
        tick_speed=TICK_SPEED,
        max_limit_pin=26,
        min_limit_pin=26,
        power_pin=3,
        main_up_pin=5,
        main_down_pin=6,
        log_state=False,
        secondary_up_pin=6,
        secondary_down_pin=7,
        main_speed_channel=0,
        secondary_speed_channel=1,
        status_led_pin=16,
        osc_led_pin=12,
        trigger_pin=20,
        echo_pin=21
    ))
    system.stop()
    sleep(1)
    system.event_loop()

    def on_exit():
        motor.disable()
        system.cleanup()
        print('Exiting')


    def handle_signal(num: int, frame):
        print(f"Signal {num} received")
        sys.exit(0)

    atexit.register(on_exit)
    signal.signal(signal.SIGINT, handle_signal)

if __name__ == '__main__':
    main()