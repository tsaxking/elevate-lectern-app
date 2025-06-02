import time

class PID:
    def __init__(self, kp, ki, kd):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.prev_error = 0
        self.integral = 0
        self.last_time = None

    def compute(self, target, actual):
        now = time.time()
        dt = (now - self.last_time) if self.last_time else 0.01
        self.last_time = now

        error = target - actual
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt if dt > 0 else 0
        self.prev_error = error

        return self.kp * error + self.ki * self.integral + self.kd * derivative
    
    def reset(self):
        self.prev_error = 0
        self.integral = 0
        self.last_time = None
        print("PID controller reset")
