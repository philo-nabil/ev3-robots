#!/usr/bin/env bash
# Check everything between this computer and a brick. Changes nothing.
#
#   ./doctor.sh ev3-2
#
# Read the result top to bottom: the first FAIL is usually the real problem.
# Each FAIL names the section of TROUBLESHOOTING.md to read.
set -uo pipefail
cd "$(dirname "$0")"
source ./lib.sh
need_brick "${1:-}"
BRICK="$1"

ok()   { echo "  OK    $*"; }
warn() { echo "  WARN  $*"; }
fail() { echo "  FAIL  $*"; }

echo "== This computer"
if [ -f "$HOME/.ssh/id_ed25519_ev3" ]; then ok "SSH key ~/.ssh/id_ed25519_ev3 exists"
else fail "No key ~/.ssh/id_ed25519_ev3  -> SETUP.md 'Each coach'"; fi

target=$(ssh -G "$BRICK" 2>/dev/null | awk '/^hostname /{print $2}')
alias_=$(ssh -G "$BRICK" 2>/dev/null | awk '/^hostkeyalias /{print $2}')
if [ "$target" = "192.168.0.1" ] && [ "$alias_" = "$BRICK" ]; then
  ok "~/.ssh/config has an entry for $BRICK"
else
  fail "No proper '$BRICK' entry in ~/.ssh/config  -> SETUP.md step 'SSH config'"
fi

if ifconfig 2>/dev/null | grep -q 'inet 192.168.0.2 '; then
  ok "USB network link to a brick is up (this computer = 192.168.0.2)"
else
  fail "No USB link to any brick  -> TROUBLESHOOTING.md 'Connection'"
fi

gw=$(route -n get default 2>/dev/null | awk '/gateway:/{print $2}')
if [ "$gw" = "192.168.0.1" ]; then
  fail "Internet is routed through the brick  -> TROUBLESHOOTING.md 'Internet drops'"
else
  ok "Internet goes through ${gw:-?} (not the brick)"
fi

echo "== Brick $BRICK"
out=$(ssh "${SSH_OPTS[@]}" -o BatchMode=yes "$BRICK" 'bash -s' 2>&1 <<'REMOTE'
clean() { sed 's/\x1b\[[0-9;]*m//g'; }
echo "NAME $(hostname)"
v=$(cat /sys/class/power_supply/lego-ev3-battery/voltage_now 2>/dev/null)
echo "BATT $((${v:-0} / 1000))"
for p in /sys/class/lego-port/*; do
  a=$(cat $p/address)
  if [[ $a == *out* ]]; then echo "PORT ${a#*:} $(cat $p/status)"; fi
done
for m in /sys/class/tacho-motor/*; do
  [ -e "$m/address" ] && echo "MOTOR $(cat $m/address | cut -d: -f2) $(cat $m/driver_name)"
done
echo "BT $(printf 'show\n' | bluetoothctl 2>/dev/null | clean | grep -o 'Powered: [a-z]*' | head -1)"
printf 'paired-devices\n' | bluetoothctl 2>/dev/null | clean \
  | grep -o 'Device [0-9A-F:]\{17\} Wireless Controller' | awk '{print "PAIRED", $2}' | sort -u
echo "LOCK $(cat /home/robot/controller.mac 2>/dev/null)"
for d in /sys/class/input/event*; do
  n=$(cat $d/device/name 2>/dev/null)
  [ "$n" = "Wireless Controller" ] && echo "LIVE $(cat $d/device/uniq)"
done
ls /home/robot/*/controller.py 2>/dev/null | sed 's|^/home/robot/|CODE |'
pgrep -af 'python3.*\.py' | grep -v pgrep | sed 's/^/RUN /'
REMOTE
)
if ! printf '%s\n' "$out" | grep -q '^NAME '; then
  fail "Cannot log in to $BRICK:"
  printf '%s\n' "$out" | sed 's/^/          /' | head -5
  if printf '%s' "$out" | grep -qE 'timed out|No route|Network is unreachable'; then
    echo "        -> TROUBLESHOOTING.md 'Connection' (brick not reachable)"
  else
    echo "        -> TROUBLESHOOTING.md 'SSH' (host key warning = wrong brick plugged in)"
  fi
  exit 1
fi

name=$(printf '%s\n' "$out" | awk '/^NAME /{print $2}')
[ "$name" = "$BRICK" ] && ok "Logged in, brick is named $name" \
  || fail "Brick is named '$name', expected '$BRICK'  -> SETUP.md 'Name the brick'"

mv=$(printf '%s\n' "$out" | awk '/^BATT /{print $2}')
if [ "${mv:-0}" -ge 7500 ]; then ok "Battery ${mv} mV"
elif [ "${mv:-0}" -ge 7000 ]; then warn "Battery ${mv} mV is getting low"
else fail "Battery ${mv} mV is LOW: expect disconnects and weak motors. Charge it."; fi

printf '%s\n' "$out" | awk '/^PORT /{print $2, $3}' | while read -r port status; do
  case "$status" in
    no-motor)  echo "        port $port: empty" ;;
    error)     fail "port $port: something plugged in but not working  -> 'Motors'" ;;
    *)         echo "        port $port: $status" ;;
  esac
done
motors=$(printf '%s\n' "$out" | awk '/^MOTOR /{print $2" ("$3")"}' | tr '\n' ' ')
[ -n "$motors" ] && ok "Motors: $motors" || fail "No motors detected  -> TROUBLESHOOTING.md 'Motors'"

printf '%s\n' "$out" | grep -q '^BT Powered: yes' && ok "Bluetooth is on" \
  || fail "Bluetooth is off  -> brick menu: Wireless and Networks -> Bluetooth -> Powered"

paired=$(printf '%s\n' "$out" | awk '/^PAIRED /{print tolower($2)}')
lock=$(printf '%s\n' "$out" | awk '/^LOCK /{print $2}')
live=$(printf '%s\n' "$out" | awk '/^LIVE /{print $2}')
npaired=$(printf '%s\n' "$paired" | grep -c . || true)
if [ "$npaired" -eq 0 ]; then fail "No controller paired  -> run ./pair.sh $BRICK"
elif [ "$npaired" -gt 1 ]; then fail "$npaired controllers paired (should be 1)  -> run ./pair.sh $BRICK"
else ok "One controller paired: $paired"; fi
if [ -z "$lock" ]; then fail "Brick not locked to a controller  -> run ./pair.sh $BRICK"
elif [ "$lock" != "$paired" ]; then fail "Lock ($lock) doesn't match paired controller  -> run ./pair.sh $BRICK"
else ok "Locked to controller $lock"; fi
if [ -z "$live" ]; then warn "Controller not connected right now (press PS on it)"
elif [ "$live" = "$lock" ]; then ok "Controller connected"
else fail "A different controller ($live) is connected  -> TROUBLESHOOTING.md 'Wrong controller'"; fi

code=$(printf '%s\n' "$out" | awk '/^CODE /{print $2}' | tr '\n' ' ')
[ -n "$code" ] && ok "Programs on brick: $code" || warn "No programs on brick yet  -> ./deploy.sh $BRICK --copy"
running=$(printf '%s\n' "$out" | sed -n 's/^RUN [0-9]* //p')
[ -n "$running" ] && echo "        running now: $running"
exit 0
