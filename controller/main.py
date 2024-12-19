# This is the main file for the motor controller
# This will create a server to recieve commands from external sources and control the motor


import time
from RPi import GPIO
from motor import Motor
from system import System

def main():
    motor = Motor(pwm_pin=18, frequency=1000)
    system = System(motor, position_pin=17, tick_speed=20)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally: # Clean up GPIO
        GPIO.cleanup()
