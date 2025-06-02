from motor import Motor, MotorConfig
# from controller.oldsystem import System, SystemConfig
from lectern import Lectern, LecternConfig
from RPi import GPIO
from time import sleep
import signal
import asyncio
import system

TICK_SPEED = 15

# def main():
#     GPIO.setmode(GPIO.BCM)
#     motor = Motor(MotorConfig(
#         pin=17,
#         max=2000,
#         min=1000,
#         zero=1500,
#         invert=False,
#         tick_speed=TICK_SPEED,
#         acceleration=0.02
#     ))
#     system = System(motor, SystemConfig(
#         position_pin=0,
#         tick_speed=TICK_SPEED,
#         max_limit_pin=26,
#         min_limit_pin=19,
#         power_pin=18,
#         main_up_pin=5,
#         main_down_pin=6,
#         log_state=False,
#         secondary_up_pin=24,
#         secondary_down_pin=23,
#         # main_speed_channel=0,
#         # secondary_speed_channel=1,
#         status_led_pin=16,
#         osc_led_pin=12,
#         # down_trigger_pin=21,
#         # down_echo_pin=20,
#         # up_trigger_pin=0,
#         # up_echo_pin=0
#     ))
#     def on_exit():
#         motor.disable()
#         system.cleanup()
#         print('Exiting')
#         exit()


#     def handle_signal(num: int, frame):
#         print(f"Signal {num} received")
#         on_exit()

#     atexit.register(on_exit)
#     signal.signal(signal.SIGINT, handle_signal)
#     signal.signal(signal.SIGTERM, handle_signal)

#     try:
#         system.stop()
#         sleep(1)
#         system.event_loop()
#     finally:
#         on_exit()

#     return system

async def async_main():
    GPIO.setmode(GPIO.BCM)
    motor = Motor(MotorConfig(
        pin=17,
        max=2000,
        min=1000,
        zero=1500,
        invert=False,
        tick_speed=TICK_SPEED,
        acceleration=0.02
    ))
    lectern = Lectern(motor, LecternConfig(
        position_pin=0,
        tick_speed=TICK_SPEED,
        max_limit_pin=26,
        min_limit_pin=19,
        power_pin=18,
        main_up_pin=5,
        main_down_pin=6,
        log_state=False,
        secondary_up_pin=24,
        secondary_down_pin=23,
        status_led_pin=16,
        osc_led_pin=12,
    ))

    shutdown_event = asyncio.Event()

    S = system.System(system.SystemConfig(
        lectern=lectern,
        ip="0.0.0.0",
        osc_port=12321,
        udp_port=41234,
        tcp_port=11111,
        emit_tick_speed=TICK_SPEED * 5, # Emit every 5 ticks (75ms)
    ))

    async def on_exit():
        print('Exiting')
        motor.disable()
        await S.stop()
        shutdown_event.set()
        await lectern.cleanup()



    def handle_signal(num: int, frame):
        print(f"Signal {num} received")
        asyncio.create_task(on_exit())

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        await S.start()
        await shutdown_event.wait()
    except Exception as e:
        print(f"An error occurred: {e}")
        await on_exit()

if __name__ == '__main__':
    # main()
    asyncio.run(async_main())