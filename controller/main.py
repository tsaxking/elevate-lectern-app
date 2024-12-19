# This is the main file for the motor controller
# This will create a server to recieve commands from external sources and control the motor


import time
from RPi import GPIO
from motor import Motor
from system import System
import atexit
import osc

async def main():
    motor = Motor(pwm_pin=18, frequency=1000)
    system = System(
        motor=motor,
        config={
            "log_state": True,
            "position_pin": 0,
            "main_down_pin": 17,
            "main_up_pin": 27,
            "max_limit_pin": 22,
            "min_limit_pin": 23,
            "power_pin": 24,
            "secondary_down_pin": 25,
            "secondary_up_pin": 5,
            "tick_speed": 20,
        }
    )
    osc_controller = osc.OscController(system, "127.0.0.1", 2222)

    await system.startup()
    atexit.register(system.shutdown)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally: # Clean up GPIO
        GPIO.cleanup()
