#!/usr/bin/env python3
"""VEX IQ style example: arcade drive with a PS4 controller.

Run it:   ./deploy.sh ev3-N vex_example.py
Copy this file (e.g. team_red_vex.py) to write your own program.

  Left stick up/down     drive forward / back   (AxisA)
  Right stick left/right turn                   (AxisC)
  Triangle               beep                   (ButtonEUp)
  Left stick click       hold to stop           (ButtonL3)
  Options                quit
"""

import time

from ev3dev2.motor import LargeMotor, OUTPUT_A, OUTPUT_D, SpeedPercent
from ev3dev2.sound import Sound

from vex_controller import Controller, stop_motors_on_exit

# ---- Settings (coaches: change these) ---------------------------------------
left = LargeMotor(OUTPUT_A)
right = LargeMotor(OUTPUT_D)
MAX_SPEED = 75        # percent
# -----------------------------------------------------------------------------

stop_motors_on_exit(left, right)   # ALWAYS right after creating the motors
sound = Sound()
controller = Controller()          # waits until the controller is connected

running = [True]


def quit_program():
    print('Options pressed - quitting.')
    running[0] = False


# Event callbacks, like Controller.ButtonEUp.pressed(...) in VEX IQ
controller.ButtonEUp.pressed(sound.beep)
controller.ButtonOptions.pressed(quit_program)


def clamp(x):
    return max(-100, min(100, x))


def drive(motor, pct):
    if pct == 0:
        motor.off()
    else:
        motor.on(SpeedPercent(pct))


last = (None, None)
while running[0]:
    forward = controller.AxisA.position()
    turn = controller.AxisC.position()
    l = clamp(forward + turn) * MAX_SPEED // 100
    r = clamp(forward - turn) * MAX_SPEED // 100
    if controller.ButtonL3.pressing():
        l = r = 0
    if (l, r) != last:          # only talk to the motors when something changed
        drive(left, l)
        drive(right, r)
        last = (l, r)
    time.sleep(0.02)            # like wait(20, MSEC)
