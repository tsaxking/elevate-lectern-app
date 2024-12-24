import pigpio

# Initialize pigpio
pi = pigpio.pi()

if not pi.connected:
    raise RuntimeError("pigpio daemon not running or connection failed!")

# Set up a GPIO pin for PWM
# PWM_PIN = 18  # Use GPIO 18 (hardware PWM-capable)
# FREQUENCY = 100  # Set PWM frequency in Hz


class PWM:
    def __init__(self, pin: int, frequency: int):
        self.pin = pin
        self.frequency = frequency
        pi.set_PWM_frequency(self.pin, self.frequency)
        pi.set_PWM_dutycycle(self.pin, 0)

    def ChangeDutyCycle(self, duty_cycle: int):
        print(f"Setting duty cycle to {duty_cycle}/255")
        pi.set_PWM_dutycycle(self.pin, duty_cycle)

    def stop(self):
        pi.set_PWM_dutycycle(self.pin, 0)

    def start(self, duty_cycle: int):
        pi.set_PWM_dutycycle(self.pin, duty_cycle)

# # Set PWM frequency
# pi.set_PWM_frequency(PWM_PIN, FREQUENCY)

# # Test various duty cycles
# try:
#     print(f"PWM Frequency: {pi.get_PWM_frequency(PWM_PIN)} Hz")

#     for duty_cycle in range(0, 256, 25):  # Duty cycle range 0-255
#         print(f"Setting duty cycle to {duty_cycle}/255")
#         pi.set_PWM_dutycycle(PWM_PIN, duty_cycle)
#         time.sleep(1)

#     # Turn off PWM
#     print("Turning off PWM")
#     pi.set_PWM_dutycycle(PWM_PIN, 0)

# finally:
#     # Cleanup
#     pi.stop()
