# Setup guide: from zero to driving

This guide takes you from an empty SD card to driving your robot with a PS4 controller.
No programming knowledge needed: follow the steps in order and copy the commands exactly.

**Time:** about 1 hour the first time (half of it is waiting for downloads and copying).
**Written for:** Mac laptops. Windows: see the note at the very end.
**Stuck?** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md), or ask the person who runs the robots.

| Part | What | Done once per |
|---|---|---|
| [0](#part-0-what-to-prepare) | What to prepare | person |
| [1](#part-1-make-the-sd-card) | Make the SD card | brick |
| [2](#part-2-start-the-brick) | Start the brick | brick |
| [3](#part-3-set-up-your-laptop) | Set up your laptop | laptop |
| [4](#part-4-connect-laptop-brick-and-controller) | Connect laptop, brick and controller | brick |
| [5](#part-5-drive) | Drive! | |

---

## Part 0: What to prepare

### Hardware

| Item | Notes |
|---|---|
| **LEGO MINDSTORMS EV3 brick** | |
| **Batteries** | The LEGO rechargeable pack, **fully charged**, or 6 fresh AA batteries. Low batteries cause most "random" disconnects |
| **microSD card, 2 GB to 32 GB** | Must be **microSD or microSDHC**. **Cards larger than 32 GB (SDXC) do NOT work** in the EV3. 8 or 16 GB is ideal. Brand-name (SanDisk, Samsung, Kingston) |
| **SD card reader** for your laptop | Only if your laptop has no SD slot. A USB-C/USB reader that takes microSD (or microSD → SD adapter) |
| **USB cable: USB-A or USB-C → mini-USB** | Must be a **data** cable (some only charge). It's the same cable that came with the EV3. Plug it **straight into the laptop, no hub** |
| **PS4 controller (DualShock 4)** | Charged, with its USB charging cable. **PS5 and Xbox controllers do NOT work** |
| **2 large motors** + cables | Already on your robot. Spare cables are handy: a bad cable is common |
| **Stickers / tape and a marker** | To label brick + controller with the same number |

### Accounts and information

| Item | Where |
|---|---|
| **Your brick number** (1, 2, 3 or 4) | Ask the person who runs the robots. Brick number = controller number = sticker |
| **GitHub account** | Free at [github.com](https://github.com). Send your username to the person who runs the robots, so they can invite you to the code |
| **A password manager** or a safe note | For the brick password you'll create. Never put passwords in the code or in chat |

### Software to download (all free)

| Program | Get it from | What it's for |
|---|---|---|
| **ev3dev operating system** | [ev3dev-stretch-ev3-generic-2020-04-10.zip](https://github.com/ev3dev/ev3dev/releases/download/ev3dev-stretch-2020-04-10/ev3dev-stretch-ev3-generic-2020-04-10.zip) (373 MB). Official page: [ev3dev.org/downloads](https://www.ev3dev.org/downloads/) | The brick's new "brain software". Do **not** unzip it |
| **Raspberry Pi Imager** | [raspberrypi.com/software](https://www.raspberrypi.com/software/) | Copies ev3dev onto the SD card |
| **Visual Studio Code** | [code.visualstudio.com](https://code.visualstudio.com/) | Editing code (optional but nice) |
| **ev3dev-browser** extension | In VS Code: Extensions (⇧⌘X) → search `ev3dev-browser` → Install | See and control the brick from VS Code |

> **Don't worry about the brick:** ev3dev runs entirely from the SD card. Take the card out
> and the brick starts the normal LEGO software again, unchanged.

---

## Part 1: Make the SD card

Do this on your laptop. **Everything on the SD card will be erased.**

1. Put the microSD card into your laptop (or card reader).
2. Open **Raspberry Pi Imager**.
3. **Choose Device**: pick **No filtering** (or skip it if your version doesn't have this button).
4. **Choose OS** → scroll to the **bottom** → **Use custom** → select the file
   `ev3dev-stretch-ev3-generic-2020-04-10.zip` (in Downloads). Don't unzip it first.
5. **Choose Storage** → select your **SD card**.
   ⚠️ Check the size matches your card (e.g. "16 GB"), so you never erase the wrong disk.
6. Click **Next**.
7. It asks *"Would you like to apply OS customisation settings?"* → click **No**.
   (Those settings are for Raspberry Pi computers, not the EV3.)
8. Confirm **Yes** to erase. macOS may ask for **your Mac password**: that's normal, since Imager needs
   it to write the card.
9. Wait for **Writing** and **Verifying** to finish (5–15 minutes).
10. When it says *"Write Successful"*, remove the card. If macOS says *"The disk you inserted was not
    readable"*, click **Ignore** or **Eject**. That's normal: macOS can't read Linux cards.

**If the brick won't start from this card later** (Part 2), flash it again with
**balenaEtcher version 1.17.0**, the version the ev3dev project recommends
([download 1.17.0](https://github.com/balena-io/etcher/releases/tag/v1.17.0); newer Etcher versions
don't work with ev3dev): *Flash from file* → the same `.zip` → *Select target* → your card → *Flash*.

---

## Part 2: Start the brick

1. **Turn the brick off.** Unplug all motors, sensors and USB for the first start.
2. Slide the microSD card into the **SD slot on the side of the brick**. It only fits one way; don't force it.
3. Press the **centre button** to turn it on.
4. What you'll see on the **first** start (it's slow, about **3–5 minutes**):
   - LEGO MINDSTORMS logo, red lights
   - ev3dev logo, **orange** lights
   - the screen goes **blank for about a minute**. This is normal on the first start only.
   - *"brickman loading…"*
   - **Green lights and a menu** = done ✅
5. **Nothing after 5 minutes?** Flash the card again (Part 1, or with Etcher 1.17.0), try another
   SD card, and check the batteries.

Later starts take about 1–2 minutes.
**To turn it off:** hold the **Back** button (top left) → **Power Off**.

Now plug the motors back in. Put a sticker **`ev3-N`** (your number, e.g. `ev3-2`) on the
brick **and** on its controller.

---

## Part 3: Set up your laptop

Every coach does this once on their own laptop. All commands go into the **Terminal** app:
press **⌘ Space**, type `Terminal`, press Enter. Paste a command with **⌘ V**, then press **Enter**.

### 3.1 macOS network settings

These two settings prevent the two most confusing problems:

1. **Keep your internet on Wi-Fi.** Plug the brick into the laptop with USB, turned on.
   Then **System Settings → Network → ⋯** (button at the bottom of the list) → **Set Service Order…**
   → drag **Wi-Fi** to the top → **OK**.
   *Without this, plugging in the brick cuts your internet.*
2. **Allow local network access.** **System Settings → Privacy & Security → Local Network**
   → turn on **Terminal** and **Visual Studio Code**. If a pop-up asks to *"find devices on your
   local network"*, click **Allow**.
   *Without this you get `No route to host` even though the cable is fine.*

### 3.2 Git

Check it's installed:
```bash
git --version
```
If a window offers to install *"command line developer tools"*, click **Install** and wait.

### 3.3 Your SSH key

An SSH key is a digital house key: it lets your laptop into the brick without a password.
**Everyone makes their own. Never share or copy someone else's.**

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_ev3 -C "ev3 - YOUR NAME"
```
It asks for a passphrase. Choose one and remember it (macOS saves it for you), or press Enter
twice for none.

### 3.4 Get the code and the brick names

1. Accept the GitHub invitation (check your email, or [github.com/notifications](https://github.com/notifications)).
2. Download the code into your Documents folder:
   ```bash
   cd ~/Documents && git clone https://github.com/philo-nabil/ev3-robots.git && cd ev3-robots
   ```
   The first time, git asks you to sign in to GitHub in the browser.
3. Teach your laptop the names `ev3-1` … `ev3-4`. This adds the contents of
   [ssh_config.example](ssh_config.example) to your settings file:
   ```bash
   touch ~/.ssh/config && chmod 600 ~/.ssh/config && cat ssh_config.example >> ~/.ssh/config
   ```
   (Do it only once. Running it twice adds the entries twice. That's harmless, but messy.)

From now on, always open Terminal in this folder first:
```bash
cd ~/Documents/ev3-robots
```

---

## Part 4: Connect laptop, brick and controller

Replace **`N`** with your brick number everywhere (e.g. `ev3-2`).
Plug the brick into the laptop with USB and wait until its screen shows an IP address at the top
(usually `192.168.0.1`; `169.254…` at first is normal, give it 20 seconds).

> Steps 4.1–4.3 are the **only** times you type a password. After that, everything works without one.

### 4.1 Put your key on the brick

```bash
ssh-copy-id -i ~/.ssh/id_ed25519_ev3.pub ev3-N
```
- *"Are you sure you want to continue connecting?"* → type `yes`
- Password: **`maker`** (the default for every new ev3dev card). Nothing shows while you type.

### 4.2 Change the brick password

```bash
ssh -t ev3-N passwd
```
Current password: `maker`. New password: **at least 8 characters**, different for every brick.
Save it in your password manager.

### 4.3 Name the brick

Every new brick is called `ev3dev`. This renames it to `ev3-N`, so code can never go to the wrong brick.
Replace **both** `ev3-N` inside the quotes:
```bash
ssh -t ev3-N 'sudo hostnamectl set-hostname ev3-N && sudo sed -i "s/ev3dev/ev3-N/g" /etc/hosts && sudo reboot'
```
It asks for the **new brick password** from 4.2. The brick restarts: wait about a minute
until the IP shows again.

### 4.4 Check

```bash
./doctor.sh ev3-N
```
Everything should be **OK**, except the controller lines (that's next). Fix any other FAIL first:
the message says where to look.

### 4.5 Pair the controller

1. Make sure **no other PS4 controller nearby is flashing**.
2. On the controller with your sticker, hold **Share + PS** together until the light bar
   **double-flashes** (blink-blink, pause, blink-blink).
3. Run, right away:
   ```bash
   ./pair.sh ev3-N
   ```
4. It should end with *"OK: ev3-N is now locked to controller …"*.

The brick now only obeys this controller. From now on, pressing **PS** is enough to reconnect.

### 4.6 Let other coaches in (if several people use one brick)

Each extra coach sends you their **public** key file `~/.ssh/id_ed25519_ev3.pub`.
The `.pub` file is safe to share; the file without `.pub` is **never** shared. Save it,
e.g. as `sara.pub`, then:
```bash
ssh ev3-N 'cat >> ~/.ssh/authorized_keys' < sara.pub
```
They do Part 3 on their laptop and can then skip straight to Part 5.

### 4.7 Motors and first test

```bash
./doctor.sh ev3-N
```
Look at the **Motors** line, e.g. `outA … outD`. Open `controller.py`; at the top under
**Settings**, make `LEFT_PORT` and `RIGHT_PORT` match (e.g. `OUTPUT_A`, `OUTPUT_D`).
Then:
```bash
./deploy.sh ev3-N
```
Lift the robot off the table and push the sticks. **Ctrl+C** stops it.

---

## Part 5: Drive!

**With the cable** (see messages on your laptop):
```bash
./deploy.sh ev3-N
```

**Without the cable** (free driving):
```bash
./deploy.sh ev3-N --copy
```
Unplug USB. On the brick: **File Browser → ev3-robots → controller.py** → centre button.
Press **PS** on the controller.

| Controller | Action |
|---|---|
| Left / right stick | Left / right motor |
| L1 / R1 | Slower / faster |
| PS | Emergency stop (press again to continue) |
| Options | Quit |

Next: [README.md](README.md) explains how to change the code.

---

## Checklist

- [ ] SD card 2–32 GB flashed with `ev3dev-stretch-ev3-generic-2020-04-10.zip`
- [ ] Brick starts to the green-light menu
- [ ] Brick and controller have the same `ev3-N` sticker
- [ ] Laptop: Wi-Fi first in service order, Local Network allowed
- [ ] SSH key made, code cloned, SSH config added
- [ ] Key on brick, password changed from `maker`, brick renamed
- [ ] `./doctor.sh ev3-N`: all OK
- [ ] Controller paired with `./pair.sh ev3-N`
- [ ] Robot drives

---

### Note for Windows laptops

Parts 0–2 are the same: Raspberry Pi Imager exists for Windows. For Part 3 onwards, the
`.sh` scripts need **Git Bash** (installed with [Git for Windows](https://git-scm.com/download/win)),
and the macOS-only steps (3.1) don't apply. The simplest path on Windows is the
**VS Code ev3dev-browser** extension: it connects to the brick with the password, and you use
**Send workspace to device** and **Run**. Pairing (4.5) still needs `pair.sh` from Git Bash,
or ask someone with a Mac to do it.
