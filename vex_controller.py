#!/usr/bin/env python3
"""VEX IQ style controller for the EV3 + PS4 controller.

Lets coaches who know VEX IQ write EV3 programs the same way:

    controller.ButtonEUp.pressing()          -> True while held
    controller.ButtonEUp.pressed(callback)   -> run callback once when pressed
    controller.ButtonEUp.released(callback)  -> run callback once when released
    controller.AxisA.position()              -> -100 .. 100 (percent)
    controller.AxisA.value()                 -> -127 .. 127
    controller.AxisA.changed(callback)       -> run callback when the value changes

VEX IQ axis layout (so VEX code ports 1:1):
    AxisA = left stick up/down      (up = +100)
    AxisB = left stick left/right   (right = +100)
    AxisC = right stick left/right  (right = +100)
    AxisD = right stick up/down     (up = +100)

Safety, built in:
  * If the controller disconnects, every stick reads 0, every button reads
    "not pressed" (released callbacks run), and the motors given to
    stop_motors_on_exit() are stopped. When the controller reconnects
    (press PS), everything carries on.
  * stop_motors_on_exit(left, right) also stops those motors on Ctrl+C,
    a crash, the VS Code stop button, or the USB/SSH connection dropping.
  * Only the controller this brick was paired with (pair.sh) is accepted.

Callbacks run one at a time, in order, in a background thread, so a slow
callback never stops the controller being read. Keep them short (or start
your own thread inside one for long jobs).

Works with the brick's software: ev3dev-stretch, Python 3.5, python-evdev 0.4.7.
See vex_example.py for a complete program.

Test your buttons:  ./deploy.sh ev3-N vex_controller.py   (prints every event)
"""

import atexit
import os
import queue
import signal
import sys
import threading
import time
import traceback

import evdev
from evdev import ecodes as e

# ---------------------------------------------------------------------------
# Mapping: VEX IQ name -> PS4 code (checked on the brick's 4.14 kernel).
# ---------------------------------------------------------------------------
BUTTON_MAP = {
    "ButtonLUp":   e.BTN_TL,      # L1
    "ButtonLDown": e.BTN_TL2,     # L2 (click)
    "ButtonRUp":   e.BTN_TR,      # R1
    "ButtonRDown": e.BTN_TR2,     # R2 (click)
    "ButtonEUp":   e.BTN_NORTH,   # Triangle
    "ButtonEDown": e.BTN_SOUTH,   # Cross
    "ButtonFUp":   e.BTN_WEST,    # Square
    "ButtonFDown": e.BTN_EAST,    # Circle
    "ButtonL3":    e.BTN_THUMBL,  # left stick click
    "ButtonR3":    e.BTN_THUMBR,  # right stick click
    # PS4 extras that VEX IQ doesn't have
    "ButtonShare":   e.BTN_SELECT,
    "ButtonOptions": e.BTN_START,
    "ButtonPS":      e.BTN_MODE,
}

# The D-pad arrives as a hat axis (-1 / 0 / +1); exposed as four buttons.
DPAD = {
    "ButtonUp":    (e.ABS_HAT0Y, -1),
    "ButtonDown":  (e.ABS_HAT0Y, +1),
    "ButtonLeft":  (e.ABS_HAT0X, -1),
    "ButtonRight": (e.ABS_HAT0X, +1),
}

# name -> (code, invert). PS4 sticks report "up" as the LOW value.
AXIS_MAP = {
    "AxisA": (e.ABS_Y,  True),
    "AxisB": (e.ABS_X,  False),
    "AxisC": (e.ABS_RX, False),
    "AxisD": (e.ABS_RY, True),
}

DEADBAND = 10   # percent; worn PS4 sticks don't rest exactly at centre

CONTROLLER_NAMES = ('Wireless Controller',
                    'Sony Interactive Entertainment Wireless Controller')
PAIRED_MAC_FILE = '/home/robot/controller.mac'   # written by pair.sh


# ---------------------------------------------------------------------------
# Callbacks: one background thread runs them in order.
# (A thread per event, as VEX does, would swamp the EV3's small CPU.)
# ---------------------------------------------------------------------------
_callbacks = queue.Queue()


def _run_callbacks():
    while True:
        cb = _callbacks.get()
        try:
            cb()
        except Exception:
            traceback.print_exc()


threading.Thread(target=_run_callbacks, daemon=True).start()


# ---------------------------------------------------------------------------
# Safety: motors that must stop on exit or disconnect.
# ---------------------------------------------------------------------------
_safety_motors = []
_safety_installed = [False]


def _stop_safety_motors():
    for m in _safety_motors:
        try:
            m.stop()
        except Exception:
            pass


def _exit_on_signal(signum, frame):
    sys.exit(0)     # runs the atexit handler below, which stops the motors


def stop_motors_on_exit(*motors):
    """Stop these motors on Ctrl+C, crash, stop button, or controller loss.

    Call it once, from the main program, right after creating the motors.
    """
    _safety_motors.extend(motors)
    if not _safety_installed[0]:
        _safety_installed[0] = True
        atexit.register(_stop_safety_motors)
        signal.signal(signal.SIGTERM, _exit_on_signal)   # VS Code stop button
        signal.signal(signal.SIGHUP, _exit_on_signal)    # SSH / USB dropped


# ---------------------------------------------------------------------------
# Finding this brick's controller
# ---------------------------------------------------------------------------
def _dev_path(dev):
    # python-evdev before 1.0 (the brick has 0.4.7) calls it .fn
    return getattr(dev, 'path', None) or getattr(dev, 'fn', '?')


def _dev_mac(dev):
    node = os.path.basename(_dev_path(dev))
    try:
        with open('/sys/class/input/{}/device/uniq'.format(node)) as f:
            return f.read().strip().lower()
    except (OSError, IOError):
        return ''


def _paired_mac():
    try:
        with open(PAIRED_MAC_FILE) as f:
            return f.read().strip().lower()
    except (OSError, IOError):
        return ''


def _find_controller(allowed, warned):
    for path in evdev.list_devices():
        try:
            dev = evdev.InputDevice(path)
        except OSError:
            continue
        if dev.name not in CONTROLLER_NAMES:
            dev.close()
            continue
        mac = _dev_mac(dev)
        if allowed and mac and mac != allowed:
            if mac not in warned:
                print('Ignoring controller {} - this brick belongs to {}.'.format(mac, allowed))
                warned.add(mac)
            dev.close()
            continue
        return dev
    return None


def _axis_ranges(dev):
    # capabilities(absinfo=True) works on old evdev; dev.absinfo() needs 1.3+.
    caps = dev.capabilities(absinfo=True).get(e.EV_ABS, [])
    return {code: (info.min, info.max) for code, info in caps}


# ---------------------------------------------------------------------------
# Buttons and axes
# ---------------------------------------------------------------------------
class Button:
    def __init__(self, name):
        self.name = name
        self._state = False
        self._pressed_cbs = []
        self._released_cbs = []

    def pressing(self):
        """True while the button is held."""
        return self._state

    def pressed(self, callback):
        """Run callback() once each time the button goes down."""
        self._pressed_cbs.append(callback)

    def released(self, callback):
        """Run callback() once each time the button comes up."""
        self._released_cbs.append(callback)

    def _update(self, new_state):
        if new_state == self._state:
            return
        self._state = new_state
        for cb in (self._pressed_cbs if new_state else self._released_cbs):
            _callbacks.put(cb)


class Axis:
    def __init__(self, name, invert):
        self.name = name
        self._invert = invert
        self._min, self._max = 0, 255     # PS4 default; updated on connect
        self._value = 0                   # -100..100
        self._raw = 0                     # -127..127
        self._changed_cbs = []
        self._queued = False              # coalesce: at most one pending

    def position(self, units="percent"):
        """-100 .. 100 (percent)."""
        return self._value

    def value(self):
        """-127 .. 127, like VEX."""
        return self._raw

    def changed(self, callback):
        """Run callback() when the value changes (bursts are merged)."""
        self._changed_cbs.append(callback)

    def _set_range(self, lo, hi):
        self._min, self._max = lo, hi

    def _update(self, raw):
        centre = (self._min + self._max) / 2.0
        half = (self._max - self._min) / 2.0 or 1.0
        norm = (raw - centre) / half
        if self._invert:
            norm = -norm
        norm = max(-1.0, min(1.0, norm))
        if abs(norm) * 100 < DEADBAND:
            norm = 0.0
        else:
            # rescale so the value starts at 0 just outside the deadband
            sign = 1.0 if norm > 0 else -1.0
            norm = sign * (abs(norm) - DEADBAND / 100.0) / (1.0 - DEADBAND / 100.0)
        self._set(int(round(norm * 100)), int(round(norm * 127)))

    def _set(self, pct, raw):
        if raw == self._raw:
            return
        self._raw, self._value = raw, pct
        if self._changed_cbs and not self._queued:
            self._queued = True
            _callbacks.put(self._fire_changed)

    def _fire_changed(self):
        self._queued = False
        for cb in self._changed_cbs:
            cb()


# ---------------------------------------------------------------------------
# The controller
# ---------------------------------------------------------------------------
class Controller:
    def __init__(self, wait=True):
        """Create the controller. Waits until it is connected (press PS).

        wait=False returns at once; check controller.connected() yourself.
        """
        self._buttons_by_code = {}
        for name, code in BUTTON_MAP.items():
            b = Button(name)
            setattr(self, name, b)
            self._buttons_by_code[code] = b

        self._dpad_by_code = {}
        for name, (code, direction) in DPAD.items():
            b = Button(name)
            setattr(self, name, b)
            self._dpad_by_code.setdefault(code, []).append((direction, b))

        self._axes_by_code = {}
        for name, (code, invert) in AXIS_MAP.items():
            a = Axis(name, invert)
            setattr(self, name, a)
            self._axes_by_code[code] = a

        self._connected = threading.Event()
        self._allowed = _paired_mac()
        if self._allowed:
            print('This brick accepts only controller {}.'.format(self._allowed))
        else:
            print('WARNING: no {} - accepting any PS4 controller. '
                  'Run ./pair.sh to lock this brick to its controller.'.format(PAIRED_MAC_FILE))

        threading.Thread(target=self._read_forever, daemon=True).start()

        if wait and not self._connected.wait(0.5):
            print('Waiting for controller... (press PS)')
            self._connected.wait()

    def connected(self):
        """True while the controller is connected."""
        return self._connected.is_set()

    def _read_forever(self):
        warned = set()
        while True:
            dev = _find_controller(self._allowed, warned)
            if dev is None:
                time.sleep(1)
                continue
            ranges = _axis_ranges(dev)
            for code, axis in self._axes_by_code.items():
                axis._set_range(*ranges.get(code, (0, 255)))
            print('Controller connected: {} ({})'.format(_dev_mac(dev), _dev_path(dev)))
            self._connected.set()
            try:
                for ev in dev.read_loop():   # raises OSError when it drops
                    self._handle(ev)
            except (OSError, IOError) as err:
                print('Controller disconnected ({}). Motors stopped. Press PS to reconnect.'.format(err))
            finally:
                self._connected.clear()
                self._release_everything()
                _stop_safety_motors()
                try:
                    dev.close()
                except Exception:
                    pass

    def _handle(self, ev):
        if ev.type == e.EV_KEY and ev.code in self._buttons_by_code:
            self._buttons_by_code[ev.code]._update(ev.value != 0)  # 1 down, 2 repeat, 0 up
        elif ev.type == e.EV_ABS:
            if ev.code in self._axes_by_code:
                self._axes_by_code[ev.code]._update(ev.value)
            elif ev.code in self._dpad_by_code:
                for direction, b in self._dpad_by_code[ev.code]:
                    b._update(ev.value == direction)

    def _release_everything(self):
        # A lost controller must look like "hands off": sticks centred,
        # buttons up (so released callbacks run and held actions stop).
        for axis in self._axes_by_code.values():
            axis._set(0, 0)
        for b in self._buttons_by_code.values():
            b._update(False)
        for pairs in self._dpad_by_code.values():
            for _, b in pairs:
                b._update(False)


def dump():
    """Print every button/stick event, to check the mapping."""
    warned = set()
    dev = None
    print('Waiting for controller... (press PS)')
    while dev is None:
        dev = _find_controller(_paired_mac(), warned)
        if dev is None:
            time.sleep(1)
    print('Reading from', _dev_path(dev), dev.name, '- Ctrl+C to stop')
    names = dict((code, name) for name, code in BUTTON_MAP.items())
    try:
        for ev in dev.read_loop():
            if ev.type == e.EV_KEY:
                print('button', names.get(ev.code, ev.code), 'down' if ev.value else 'up')
            elif ev.type == e.EV_ABS:
                print('axis', e.ABS.get(ev.code, ev.code), ev.value)
    except KeyboardInterrupt:
        pass
    except (OSError, IOError):
        print('Controller disconnected.')


if __name__ == '__main__':
    dump()
