#!/usr/bin/env python3
"""Drive an EV3 with a PS4 (DualShock 4) controller over Bluetooth.

Runs on the brick (ev3dev-stretch, Python 3.5 - so no f-strings).
Uses the kernel's hid-sony driver through python3-evdev and python-ev3dev2.

Controls (tank drive):
  Left stick  up/down   -> left motor
  Right stick up/down   -> right motor
  L1 / R1               -> lower / raise the speed limit
  PS                    -> emergency stop (press again to resume)
  Options               -> quit
"""

import os
import select
import signal
import sys
import time

import evdev
from evdev import ecodes
from ev3dev2.motor import LargeMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D

# ---- Settings (coaches: change these) ---------------------------------------
LEFT_PORT = OUTPUT_A
RIGHT_PORT = OUTPUT_D
LEFT_INVERT = False      # True if the left side drives backwards
RIGHT_INVERT = False     # True if the right side drives backwards
DEADZONE = 0.10          # fraction of stick travel ignored around centre
MAX_SPEED = 75           # starting speed limit, percent
SPEED_STEP = 10          # how much L1/R1 change the limit
MIN_LIMIT, MAX_LIMIT = 20, 100
STOP_ACTION = 'brake'    # 'coast', 'brake' or 'hold'
# The hid-sony driver names the main gamepad device "Wireless Controller"
# (the motion sensors and touchpad show up as separate devices).
CONTROLLER_NAMES = ('Wireless Controller',
                    'Sony Interactive Entertainment Wireless Controller')
# Written by pair.sh. This brick only accepts the controller listed here,
# so a controller paired to another brick can never drive this robot.
# It lives outside the code folder so deploying never overwrites it.
PAIRED_MAC_FILE = '/home/robot/controller.mac'
# -----------------------------------------------------------------------------


class Shutdown(Exception):
    pass


def on_signal(signum, frame):
    # SIGTERM (VS Code stop button) / SIGHUP (ssh dropped) -> clean exit.
    raise Shutdown()


def dev_path(dev):
    # Older python-evdev (Debian stretch) calls the path .fn, newer .path.
    return getattr(dev, 'path', None) or getattr(dev, 'fn', '?')


def controller_mac(dev):
    """Bluetooth address of an input device, read from sysfs ('' if none)."""
    node = os.path.basename(dev_path(dev))
    try:
        with open('/sys/class/input/{}/device/uniq'.format(node)) as f:
            return f.read().strip().lower()
    except (OSError, IOError):
        return ''


def paired_mac():
    try:
        with open(PAIRED_MAC_FILE) as f:
            return f.read().strip().lower()
    except (OSError, IOError):
        return ''


def find_controller(allowed, warned):
    """Return this brick's gamepad InputDevice, or None."""
    for path in evdev.list_devices():
        try:
            dev = evdev.InputDevice(path)
        except OSError:
            continue
        if dev.name not in CONTROLLER_NAMES:
            dev.close()
            continue
        mac = controller_mac(dev)
        if allowed and mac and mac != allowed:
            if mac not in warned:
                print('Ignoring controller {} - this brick belongs to {}. '
                      'See TROUBLESHOOTING.md.'.format(mac, allowed))
                warned.add(mac)
            dev.close()
            continue
        return dev
    return None


def axis_ranges(dev):
    """Map axis code -> (min, max) as reported by the driver."""
    caps = dev.capabilities(absinfo=True).get(ecodes.EV_ABS, [])
    return {code: (info.min, info.max) for code, info in caps}


def normalise(value, lo, hi):
    """Scale a raw axis value to -1.0 .. 1.0 with a deadzone."""
    mid = (lo + hi) / 2.0
    half = (hi - lo) / 2.0 or 1.0
    x = (value - mid) / half
    if abs(x) < DEADZONE:
        return 0.0
    # Rescale so output starts at 0 just outside the deadzone.
    sign = 1.0 if x > 0 else -1.0
    return sign * min(1.0, (abs(x) - DEADZONE) / (1.0 - DEADZONE))


class Drive:
    def __init__(self):
        self.left = LargeMotor(LEFT_PORT)
        self.right = LargeMotor(RIGHT_PORT)
        for m in (self.left, self.right):
            m.stop_action = STOP_ACTION
        self.running = False
        self.last = (None, None)

    def set(self, left_pct, right_pct):
        left_pct, right_pct = int(left_pct), int(right_pct)
        if (left_pct, right_pct) == self.last:
            return
        if left_pct == 0 and right_pct == 0:
            self.stop()
            return
        if not self.running:
            # run-direct: duty cycle changes take effect immediately,
            # which feels much more responsive than re-issuing run-forever.
            self.left.duty_cycle_sp = 0
            self.right.duty_cycle_sp = 0
            self.left.run_direct()
            self.right.run_direct()
            self.running = True
        self.left.duty_cycle_sp = left_pct
        self.right.duty_cycle_sp = right_pct
        self.last = (left_pct, right_pct)

    def stop(self):
        for m in (self.left, self.right):
            try:
                m.stop()
            except Exception:
                pass
        self.running = False
        self.last = (0, 0)


def drive_session(dev, drive):
    """Read the controller until it disconnects. Returns True to quit."""
    ranges = axis_ranges(dev)
    axes = {ecodes.ABS_Y: 0.0, ecodes.ABS_RY: 0.0}
    limit = MAX_SPEED
    estop = False
    print('Connected: {} {} ({})'.format(dev.name, controller_mac(dev),
                                         dev_path(dev)))
    print('Speed limit {}%. PS = e-stop, Options = quit.'.format(limit))

    while True:
        r, _, _ = select.select([dev.fd], [], [], 0.2)
        if not r:
            continue
        for ev in dev.read():   # raises OSError when the controller drops
            if ev.type == ecodes.EV_ABS and ev.code in axes:
                lo, hi = ranges.get(ev.code, (0, 255))
                axes[ev.code] = normalise(ev.value, lo, hi)
            elif ev.type == ecodes.EV_KEY and ev.value == 1:  # key down
                if ev.code == ecodes.BTN_START:          # Options
                    print('Options pressed - quitting.')
                    return True
                elif ev.code == ecodes.BTN_MODE:         # PS
                    estop = not estop
                    print('EMERGENCY STOP' if estop else 'Resumed')
                elif ev.code == ecodes.BTN_TL:           # L1
                    limit = max(MIN_LIMIT, limit - SPEED_STEP)
                    print('Speed limit {}%'.format(limit))
                elif ev.code == ecodes.BTN_TR:           # R1
                    limit = min(MAX_LIMIT, limit + SPEED_STEP)
                    print('Speed limit {}%'.format(limit))

        if estop:
            drive.stop()
        else:
            # Stick Y is negative when pushed up, so invert it.
            left = -axes[ecodes.ABS_Y] * limit
            right = -axes[ecodes.ABS_RY] * limit
            drive.set(-left if LEFT_INVERT else left,
                      -right if RIGHT_INVERT else right)


def main():
    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGHUP, on_signal)

    try:
        drive = Drive()
    except Exception as e:
        print('Motor error: {}'.format(e))
        print('Check that large motors are plugged into the ports in '
              'LEFT_PORT / RIGHT_PORT.')
        sys.exit(1)

    allowed = paired_mac()
    if allowed:
        print('This brick accepts only controller {}.'.format(allowed))
    else:
        print('WARNING: no {} - accepting any PS4 controller. '
              'Run ./pair.sh to lock this brick to its controller.'
              .format(PAIRED_MAC_FILE))
    warned = set()

    try:
        waiting_msg = True
        while True:
            dev = find_controller(allowed, warned)
            if dev is None:
                if waiting_msg:
                    print('Waiting for controller... (press PS to connect)')
                    waiting_msg = False
                time.sleep(1)
                continue
            try:
                if drive_session(dev, drive):
                    break
            except OSError as e:
                print('Controller disconnected ({}). Motors stopped.'.format(e))
            finally:
                drive.stop()
                try:
                    dev.close()
                except Exception:
                    pass
            waiting_msg = True
    except (KeyboardInterrupt, Shutdown):
        print('\nStopping.')
    finally:
        drive.stop()
        print('Motors stopped.')


if __name__ == '__main__':
    main()
