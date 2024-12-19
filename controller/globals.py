from system import System
from motor import Motor
from osc import OscController

MOTOR = Motor(pwm_pin=18, frequency=1000)
SYSTEM = System(
    motor=MOTOR,
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
OSC = OscController(SYSTEM, "127.0.0.1", 2222)