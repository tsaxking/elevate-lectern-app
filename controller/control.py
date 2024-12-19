from typing import TypedDict
from system import System
import time
import asyncio

class TrapezoidalProfile(TypedDict):
    MAX_VELOCITY: float
    ACCELERATION: float
    DECELERATION: float
    tick_speed: int

def trapezoidal_velocity_control(current_pos: float, target_pos: float, current_vel: float, profile: TrapezoidalProfile):
    """Generates desired velocity from trapezoidal profile."""

    time_step = profile['tick_speed'] / 1000  # Convert to seconds
    DECELERATION = profile['DECELERATION']
    ACCELERATION = profile['ACCELERATION']
    MAX_VELOCITY = profile['MAX_VELOCITY']

    distance_to_target = target_pos - current_pos
    direction = 1 if distance_to_target > 0 else -1
    decel_distance = (current_vel ** 2) / (2 * DECELERATION)

    if abs(distance_to_target) <= decel_distance:
        # Deceleration phase
        target_velocity = max(0, current_vel - DECELERATION * time_step)
    elif abs(current_vel) < MAX_VELOCITY:
        # Acceleration phase
        target_velocity = min(MAX_VELOCITY, current_vel + ACCELERATION * time_step)
    else:
        # Constant velocity phase
        target_velocity = MAX_VELOCITY

    return direction * target_velocity




class PID(TypedDict):
    Kp: float
    Ki: float
    Kd: float
    integral: float
    previous_error: float
    tick_speed: int


def pid_control(setpoint: int, measured: int, pid: PID):
    """PID control logic."""

    time_step = pid['tick_speed'] / 1000  # Convert to seconds

    error = setpoint - measured
    pid['integral'] += error * time_step
    derivative = (error - pid['previous_error']) / time_step

    output = pid['Kp'] * error + pid['Ki'] * pid['integral'] + pid['Kd'] * derivative
    pid['previous_error'] = error

    # Clamp output to PWM range (0-100%)
    return max(0, min(100, output))



def loop_until(fn: callable, condition: callable, tick_speed: int):
    """Loops until a condition is met."""

    while not condition():
        if fn() == True:
            break
        time.sleep(tick_speed / 1000)  # Convert to seconds

async def async_loop_until(fn: callable, condition: callable, tick_speed: int):
    """Loops until a condition is met."""

    while not condition():
        if fn() == True:
            break
        await asyncio.sleep(tick_speed / 1000)  # Convert to seconds