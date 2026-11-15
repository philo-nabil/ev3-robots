# Setup

Do **A** once on every laptop, and **B** once on every brick.
Brick 1 was set up by hand earlier: for it, see **C**.

Everything runs in the macOS **Terminal** app. You never need `sudo` on your Mac.

---

## A. Each laptop (each coach)

### A1. macOS network settings (stops the two most common problems)

1. **Keep the internet on Wi-Fi.** Plug in any brick, then go to
   **System Settings → Network → ⋯ (bottom of the list) → Set Service Order…**,
   drag **Wi-Fi** to the top, and click OK.
   *Without this, plugging in a brick cuts your internet.*
2. **Allow local network access.** **System Settings → Privacy & Security → Local Network**:
   turn on **Terminal** and **Visual Studio Code**. If macOS asks
   "allow … to find devices on your local network", click **Allow**.
   *Without this you get `No route to host` even though the cable is fine.*

### A2. Your own SSH key

Every coach makes **their own** key. Never share or copy a private key.

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_ev3 -C "ev3 - YOUR NAME"
```
Choose a passphrase. macOS remembers it in the keychain.

Send your **public** key (`~/.ssh/id_ed25519_ev3.pub`, safe to share) to whoever
manages the bricks, so they can add it (B7).

### A3. SSH config

Look at [ssh_config.example](ssh_config.example), then add it to your config:

```bash
touch ~/.ssh/config && chmod 600 ~/.ssh/config && cat ssh_config.example >> ~/.ssh/config
```

If you already had `ev3-…` entries in `~/.ssh/config`, remove the old ones first
(`open -e ~/.ssh/config`).

### A4. Get the code

```bash
git clone <repo URL> ev3-robots
cd ev3-robots
```

---

## B. Each brick (once, about 15 minutes)

Pick its number **N** (1–4). Put a sticker `ev3-N` on the brick **and** on its controller.

### B1. SD card
Flash the **ev3dev-stretch** image to the SD card (balenaEtcher), insert it, boot the brick,
plug USB into the brick's **PC** port, straight into the laptop (no hub).
Wait until the brick's screen shows an IP at the top.

### B2. Install your key (asks for the default password `maker`)
```bash
ssh-copy-id -i ~/.ssh/id_ed25519_ev3.pub ev3-N
```
On the fingerprint question answer `yes`. This is the brick's identity being remembered as `ev3-N`.

### B3. Change the password
```bash
ssh -t ev3-N passwd
```
Current: `maker`; new: **8+ characters, different per brick**. Store it in a password manager
(not in the repo, not in chat).

### B4. Name the brick
`sudo` asks for the brick password from B3. The brick reboots afterwards.
```bash
ssh -t ev3-N 'sudo hostnamectl set-hostname ev3-N && sudo sed -i "s/ev3dev/ev3-N/g" /etc/hosts && sudo reboot'
```
(Replace **both** `ev3-N` inside the quotes, e.g. `ev3-3`.) Wait about a minute for it to boot.

The name also shows up in Bluetooth and is what every script checks, so code can
never land on the wrong brick.

### B5. Check it
```bash
./doctor.sh ev3-N
```
Everything except the controller lines should be OK.

### B6. Pair its controller (one controller only)
1. Make sure **no other controller nearby is flashing**.
2. On the controller with this brick's sticker, hold **Share + PS** until the light bar **double-flashes**.
3. Run:
   ```bash
   ./pair.sh ev3-N
   ```
   The brick forgets any old controller, pairs this one, and locks itself to it.

### B7. Add the other coaches' keys
For each coach's public key file (e.g. `sara.pub`):
```bash
ssh ev3-N 'cat >> ~/.ssh/authorized_keys' < sara.pub
```
To remove a coach later: `ssh ev3-N 'nano ~/.ssh/authorized_keys'` and delete their line.

### B8. Motors and code
Plug in the motors, then run `./doctor.sh ev3-N` and check the motor ports match the
**Settings** in `controller.py`. Then copy the code over and test:
```bash
./deploy.sh ev3-N
```

---

## C. Brick 1 (already partly set up)

It already has your key and a new password, and its controller is paired.
It still needs a name, the per-brick SSH entry and the controller lock:

1. Do **A1** and **A3** if you haven't.
2. Name it. The first time, SSH asks about the fingerprint for `ev3-1`: answer `yes`.
   ```bash
   ssh -t ev3-1 'sudo hostnamectl set-hostname ev3-1 && sudo sed -i "s/ev3dev/ev3-1/g" /etc/hosts && sudo reboot'
   ```
3. Re-pair to lock it to its controller (Share + PS until it double-flashes):
   ```bash
   ./pair.sh ev3-1
   ```
4. Remove the old entry for the raw IP, so nothing connects to "whatever brick is
   at 192.168.0.1" without a name:
   ```bash
   ssh-keygen -R 192.168.0.1
   ```

---

## D. Make the GitHub repo (once)

```bash
git init
git add .
git commit -m "EV3 robots with PS4 controllers"
gh repo create ev3-robots --private --source . --push
```
Then on GitHub: **Settings → Collaborators**, and invite each coach.
Keep it **private**: it describes your robots' setup.
