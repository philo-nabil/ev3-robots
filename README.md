# EV3 robots + PS4 controllers

Four LEGO EV3 robots (`ev3-1` … `ev3-4`), each driven by **its own** PS4 controller.
You edit code on your laptop, then copy it to a robot and run it.

| Guide | For |
|---|---|
| **README.md** (this file) | Coaches: everyday use and editing code |
| [SETUP.md](SETUP.md) | **Start here:** what to buy, making the SD card, setting up laptop, brick and controller |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Anything that goes wrong |

> **Golden rule:** brick, controller and sticker numbers always match.
> Controller `ev3-2` only drives brick `ev3-2`. The brick ignores any other controller.

## Driving

| Input | Action |
|---|---|
| Left stick up/down | Left motor |
| Right stick up/down | Right motor |
| L1 / R1 | Slower / faster (speed limit 20–100 %, starts at 75 %) |
| PS | Emergency stop (press again to resume). Also wakes/reconnects the controller |
| Options | Quit the program |

The motors stop by themselves if the controller disconnects, the program crashes,
or you press Ctrl+C.

## Everyday workflow

Plug the brick into your laptop with USB, then in Terminal:

```bash
cd ev3-robots          # this repo
git pull               # get everyone's latest code
./deploy.sh ev3-2      # copy code to brick 2 and run controller.py
```

Watch the output in Terminal; **Ctrl+C** stops the robot.

**To drive without the cable:** copy only, unplug, start on the brick itself:

```bash
./deploy.sh ev3-2 --copy
```
On the brick: **File Browser → ev3-robots → controller.py** → centre button
(the folder is named after your copy of this repo).

**Something wrong?** Run this first. It checks everything and tells you what to fix:
```bash
./doctor.sh ev3-2
```

## What you can edit

| File | Edit? |
|---|---|
| `controller.py`: the **Settings** block at the top | ✅ ports, invert, speed, deadzone, brake/coast |
| `controller.py`: `drive_session()` | ✅ add button actions |
| Your own programs: copy `controller.py` to e.g. `team_red.py` | ✅ run with `./deploy.sh ev3-2 team_red.py` |
| `deploy.sh`, `pair.sh`, `doctor.sh`, `lib.sh` | ❌ shared tools; ask before changing |

### Adding a button action

In `drive_session()`, next to the other buttons:

```python
elif ev.code == ecodes.BTN_SOUTH:        # Cross
    print('Cross pressed')
    # your code here
```

| Button | Code | | Stick / trigger | Code (0–255, centre ≈128) |
|---|---|---|---|---|
| Cross | `BTN_SOUTH` | | Left stick X / Y | `ABS_X` / `ABS_Y` |
| Circle | `BTN_EAST` | | Right stick X / Y | `ABS_RX` / `ABS_RY` |
| Triangle | `BTN_NORTH` | | L2 / R2 (analogue) | `ABS_Z` / `ABS_RZ` |
| Square | `BTN_WEST` | | D-pad | `ABS_HAT0X` / `ABS_HAT0Y` (−1, 0, 1) |
| L1 / R1 | `BTN_TL` / `BTN_TR` | | | |
| L2 / R2 (click) | `BTN_TL2` / `BTN_TR2` | | | |
| Share / Options / PS | `BTN_SELECT` / `BTN_START` / `BTN_MODE` | | | |
| Stick clicks | `BTN_THUMBL` / `BTN_THUMBR` | | | |

`Options`, `PS`, `L1` and `R1` are already used; reuse them only if you mean to.

### Python rules on the brick

- The brick runs **Python 3.5**: no f-strings. Write `'speed {}'.format(x)`, not `f'speed {x}'`.
- Motor library: [python-ev3dev2](https://python-ev3dev.readthedocs.io/en/ev3dev-stretch/).
- Python is slow to start on the brick: 5–10 s before the first output is normal.

## Sharing code (Git)

```bash
git pull                          # before you start
git add team_red.py
git commit -m "Red team: add claw on Cross"
git push
```

Never commit passwords or keys. `.gitignore` blocks the usual ones.

## Alternative: VS Code ev3dev extension

1. Plug in the brick, then click **Send workspace to device** in the EV3DEV DEVICE BROWSER.
   It copies to `/home/robot/ev3-robots`, the same folder `deploy.sh` uses.
2. Right-click your `.py` file on the device → **Run**. The stop button stops the motors.

This works on Windows too, without the shell scripts.
