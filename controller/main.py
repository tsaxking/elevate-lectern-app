# This is the main file for the motor controller
# This will create a server to recieve commands from external sources and control the motor

from RPi import GPIO
import globals
import atexit
import asyncio

async def main():

    await globals.SYSTEM.startup()
    atexit.register(globals.SYSTEM.shutdown)
    asyncio.create_task(globals.SYSTEM.main_loop())

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally: # Clean up GPIO
        GPIO.cleanup()
