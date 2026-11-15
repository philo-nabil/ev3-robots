# Troubleshooting

**Always start here:**
```bash
./doctor.sh ev3-N
```
It checks your laptop, the cable, the brick, the battery, the motors and the controller,
changes nothing, and points to the section below. **Fix the first FAIL first**:
later ones are often caused by it.

Jump to: [Connection](#connection) · [Internet drops](#internet-drops) · [SSH](#ssh) ·
[Controller](#controller) · [Wrong controller](#wrong-controller) · [Motors](#motors) ·
[Program](#program) · [Emergency stop](#emergency-stop)

---

## Connection

The laptop can't see the brick (`No USB link`, `No route to host`, `Operation timed out`).

| Symptom | Cause | Fix |
|---|---|---|
| Brick screen shows **no IP** at the top | Still booting, or the link isn't up | Wait 30 s. Brick: **Wireless and Networks → All Network Connections → Wired → Connect** |
| Brick shows **169.254.x.x** | Link came up before the address was assigned | Wait 20 s; it usually changes to `192.168.0.1`. If not, unplug and replug USB |
| Laptop sees **nothing at all** | Cable, port or hub | Cable in the brick's **PC** port (top, mini-USB), **straight into the laptop, no hub**. Try another cable: some only charge |
| `No route to host` in one app (e.g. Terminal) but it works in another | macOS **Local Network** permission | System Settings → Privacy & Security → **Local Network** → turn on that app ([SETUP 3.1](SETUP.md#31-macos-network-settings)) |
| Link **drops every minute or so**, or when you touch the motors | Loose cable, or **low battery** | `./doctor.sh` shows the battery; below ~7000 mV, charge it. Keep the USB cable away from motor cables |
| Works, then stops after the brick sat idle | Brick turned itself off | Wake or restart it: hold **Back + Centre** to restart |

## Internet drops

**Your laptop loses internet the moment a brick is plugged in.**
The brick offers itself as a route to the internet, and macOS believes it.
Fix: **System Settings → Network → ⋯ → Set Service Order… → Wi-Fi to the top**.
`doctor.sh` reports this as "Internet is routed through the brick".

If it still happens: click the brick's connection → **Details → TCP/IP → Configure IPv4: Manually**,
IP `192.168.0.2`, mask `255.255.255.0`, **Router empty**.

## SSH

| Message | Meaning | Fix |
|---|---|---|
| `WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!` | **Usually the wrong brick is plugged in**: you typed `ev3-2` but brick 3 is connected | Plug in the brick you named. This warning is the safety net doing its job |
| Same warning, and you **re-flashed** that brick's SD card | The brick really got a new identity | Only then: `ssh-keygen -R ev3-N`, connect again and answer `yes` |
| `The brick plugged in is named 'ev3-3', not 'ev3-2'` | Wrong brick plugged in | Plug in the right one |
| `…is named 'ev3dev'` | Brick never got its name | [SETUP 4.3](SETUP.md#43-name-the-brick) |
| `Permission denied (publickey…)` | Your key isn't on this brick | Ask the brick manager to add your `.pub` ([SETUP 4.6](SETUP.md#46-let-other-coaches-in-if-several-people-use-one-brick)) |
| Asks for `robot@…'s password` | Same: key not installed, or `~/.ssh/config` entry missing | `./doctor.sh` tells you which |
| `Could not resolve hostname ev3-2` | No SSH config entry | [SETUP 3.4](SETUP.md#34-get-the-code-and-the-brick-names) |
| Asks for your key passphrase every time | Keychain not used | Check `UseKeychain yes` is in your config entry |

**Never** "fix" SSH warnings with `StrictHostKeyChecking no`, by deleting `known_hosts`,
or with passwordless root. These remove the protection against connecting to the wrong
device.

## Controller

| Symptom | Fix |
|---|---|
| `pair.sh`: "No controller in pairing mode found" | Hold **Share + PS** until the light bar **double-flashes** (quick blink-blink, pause). A slow single flash is normal reconnect mode, not pairing. Then run again right away: pairing mode lasts about 60 s |
| `pair.sh`: "2 controllers are in pairing mode" | Only one controller may flash at a time. Turn the others off (hold PS 10 s) |
| Light bar flashes after PS, then goes dark | The controller is paired with a different device (another brick, PS4, phone, laptop) and is looking for it. Re-pair with the right brick: `./pair.sh ev3-N` |
| Pairing fails repeatedly | Charge the controller. Reset it: press the tiny button in the hole on the back for 5 s. Turn off Bluetooth on nearby PS4s and laptops that know it |
| Program says "Waiting for controller…" forever | Press **PS**. Run `./doctor.sh`: "Controller not connected" → re-pair |
| Controller drops while driving | Charge it; stay within a few metres. The robot stops; press **PS** to reconnect |
| Lag or jerky driving | Low controller or brick battery; or many Bluetooth devices nearby |

A PS4 controller remembers **only the last device it paired with**. Pairing controller 2
with brick 1, even by accident, makes it forget brick 2. Fix it with `./pair.sh ev3-2`.

## Wrong controller

The program prints `Ignoring controller xx:xx… - this brick belongs to yy:yy…`,
or `doctor.sh` says "a different controller is connected".

This is the lock working: each brick only accepts the controller saved by `pair.sh`.

1. Check the stickers: is this really controller `ev3-N`?
2. If the controller was replaced or the stickers were wrong, re-pair the right one:
   `./pair.sh ev3-N`. This also clears the old lock.

Want a different controller on this brick? Same thing: `./pair.sh ev3-N` with the new one flashing.

## Motors

`doctor.sh` lists each motor port as *empty*, a motor type, or **error**.

| Symptom | Cause | Fix |
|---|---|---|
| Program: `Motor error: … not connected` | No motor on the port in Settings | Check `LEFT_PORT` / `RIGHT_PORT` in `controller.py` match what doctor.sh lists |
| Port shows **error** | Bad contact or damaged cable | Push the plug in until it clicks; try another cable |
| Motor is detected, but **doesn't turn** ("stalled", 0°) | Cable passes the ID signal but not power, or the motor is jammed | Turn it by hand: it should spin freely. **Swap cables with a working motor**: if the problem follows the cable, replace the cable |
| One side drives **backwards** | Motor mounted the other way round | Set `LEFT_INVERT` / `RIGHT_INVERT = True` |
| Left and right are **swapped** | Ports swapped | Swap `LEFT_PORT` and `RIGHT_PORT` |
| Motors weak or sluggish | Low battery | Charge (doctor.sh shows mV) |
| Robot creeps when sticks are released | Worn sticks | Raise `DEADZONE` to `0.15` |

To find a bad cable without a laptop: on the brick, **Device Browser → Motors**, then plug
the motors in one at a time.

## Program

| Symptom | Fix |
|---|---|
| `SyntaxError` pointing at `f'...'` | The brick has Python 3.5: use `'{}'.format(x)` |
| `/usr/bin/env: 'python3\r': No such file` | File saved with Windows line endings. `.gitattributes` prevents this for Git users; in VS Code click **CRLF** in the status bar → **LF** |
| Program not listed in the brick's File Browser, or won't start there | It must start with `#!/usr/bin/env python3` and be executable: `./deploy.sh ev3-N --copy` fixes both |
| Nothing happens for 10 s after starting | Normal: Python loads slowly on the brick |
| Program ends when the USB cable is pulled | Programs started by `deploy.sh` run *through* the cable. Use `--copy` and start from the brick's File Browser |
| `ImportError: No module named evdev` | Brick image is missing it: `ssh -t ev3-N 'sudo apt-get install python3-evdev'` |
| Changes don't seem to arrive | Did you `git pull`? Did deploy name the right brick? `./doctor.sh` lists the programs on the brick |

## Emergency stop

In order of preference:

1. **PS** on the controller: the motors stop, and PS again resumes.
2. **Options** on the controller, or **Ctrl+C** in Terminal: the program quits and stops the motors.
3. **Back** button on the brick: stops a program started from the File Browser.
4. Program frozen, motors still running:
   ```bash
   ssh ev3-N 'for m in /sys/class/tacho-motor/*; do echo reset > $m/command; done'
   ```
5. Last resort: pull a battery.
