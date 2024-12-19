import RPi.GPIO as GPIO

class Motor:
    def __init__(self, pwm_pin: int, frequency: int = 1000):
        """
        Initializes the motor object.
        
        :param pwm_pin: GPIO pin connected to the motor's PWM input.
        :param frequency: PWM frequency in Hz.
        """
        self.pwm_pin = pwm_pin
        self.frequency = frequency
        
        # Motor state
        self.speed = 0.0  # Current speed in percentage (0-100)
        self.direction = 1  # 1 for forward, -1 for reverse
        
        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pwm_pin, GPIO.OUT)
        
        # Set up PWM
        self.pwm = GPIO.PWM(self.pwm_pin, self.frequency)
        self.pwm.start(0)  # Start PWM with 0% duty cycle
    
    def set_speed(self, speed: float):
        """
        Sets the motor speed.
        
        :param speed: Speed as a percentage (0-100). Negative values indicate reverse direction.
        """
        if speed < 0:
            self.direction = -1
            speed = -speed
        else:
            self.direction = 1
        
        # Clamp speed to 0-100
        speed = max(0, min(100, speed))
        self.speed = speed
        
        # Apply speed via PWM
        self.pwm.ChangeDutyCycle(self.speed)
    
    def stop(self):
        """Stops the motor."""
        self.pwm.ChangeDutyCycle(0)
        self.speed = 0
    
    def cleanup(self):
        """Cleans up GPIO resources."""
        self.pwm.stop()
        GPIO.cleanup()