#!/usr/bin/env bash
# Pair ONE PS4 controller with ONE brick, and lock them together.
#
#   1. Plug in the brick (USB).
#   2. Hold SHARE + PS on the controller until the light bar double-flashes.
#   3. ./pair.sh ev3-2
#
# Any other controller this brick knew is forgotten, and the brick saves this
# controller's address so controller.py ignores every other controller.
set -euo pipefail
cd "$(dirname "$0")"
source ./lib.sh

need_brick "${1:-}"
BRICK="$1"
check_brick "$BRICK"

echo "==> Pairing a controller with $BRICK"
ssh "${SSH_OPTS[@]}" "$BRICK" 'bash -s' <<'REMOTE'
set -u
clean() { sed 's/\x1b\[[0-9;]*m//g'; }
bt() { printf '%s\n' "$@" | bluetoothctl >/dev/null 2>&1; }
controllers() {   # "MAC" of every known/paired Wireless Controller
  printf '%s\n' "$1" | bluetoothctl 2>/dev/null | clean \
    | grep -o 'Device [0-9A-F:]\{17\} Wireless Controller' | awk '{print $2}' | sort -u
}

bt "power on" "agent on" "default-agent"

# One brick, one controller: forget every controller this brick knew, so the
# scan below only sees controllers that are in pairing mode right now.
for m in $(controllers devices); do
  echo "Forgetting old controller $m"
  bt "remove $m"
done

echo "Scanning for a controller in pairing mode (up to 30 s)..."
( printf 'scan on\n'; sleep 30; printf 'scan off\n' ) | bluetoothctl >/dev/null 2>&1 &
SCAN=$!
FOUND=""; first=0
for i in $(seq 1 30); do
  sleep 1
  FOUND=$(controllers devices)
  [ -n "$FOUND" ] && [ "$first" -eq 0 ] && first=$i
  # Keep listening 6 s after the first one, to catch a second controller.
  [ "$first" -gt 0 ] && [ $((i - first)) -ge 6 ] && break
done
kill $SCAN 2>/dev/null || true
bt "scan off"

COUNT=$(printf '%s\n' "$FOUND" | grep -c . || true)
if [ "$COUNT" -eq 0 ]; then
  echo "!! No controller in pairing mode found."
  echo "   Hold SHARE + PS until the light bar DOUBLE-flashes, then run again."
  echo "   More help: TROUBLESHOOTING.md -> Controller."
  exit 1
fi
if [ "$COUNT" -gt 1 ]; then
  echo "!! $COUNT controllers are in pairing mode nearby:" $FOUND
  echo "   Only ONE controller may flash at a time, or the wrong one gets paired."
  echo "   Stop the others (hold PS 10 s to turn off) and run again."
  for m in $FOUND; do bt "remove $m"; done
  exit 1
fi
MAC="$FOUND"
echo "Found controller $MAC"

( printf 'scan on\n'; sleep 5; printf 'pair %s\n' "$MAC"; sleep 6;
  printf 'trust %s\n' "$MAC"; sleep 1; printf 'connect %s\n' "$MAC"; sleep 4;
  printf 'scan off\n' ) | bluetoothctl >/dev/null 2>&1

INFO=$(printf 'info %s\n' "$MAC" | bluetoothctl 2>/dev/null | clean)
if ! printf '%s' "$INFO" | grep -q 'Paired: yes'; then
  echo "!! Pairing failed. Put the controller back in pairing mode and run again."
  bt "remove $MAC"
  exit 1
fi

echo "$MAC" | tr 'A-F' 'a-f' > /home/robot/controller.mac
echo ""
echo "OK: $(hostname) is now locked to controller $MAC"
printf '%s\n' "$INFO" | grep -E 'Paired:|Trusted:|Connected:' | sed 's/^/   /'
REMOTE

echo ""
echo "==> Done. Put a sticker with '$BRICK' on this controller."
echo "    From now on, press PS on it to reconnect."
