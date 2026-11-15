# Shared helpers for deploy.sh, pair.sh and doctor.sh. Not run directly.
# Works with the bash 3.2 that ships with macOS.

SSH_OPTS=(-o ConnectTimeout=8 -o ServerAliveInterval=5)

# Usage check: every script takes the brick name (ev3-1 ... ev3-4) first.
need_brick() {
  case "${1:-}" in
    ev3-[0-9]*) ;;
    *) echo "Usage: $(basename "$0") ev3-N ...   (e.g. ev3-2)" >&2; exit 2 ;;
  esac
}

# Log in and make sure the plugged-in brick really is the one named.
# All bricks share 192.168.0.1 over USB, so this stops you deploying to,
# or pairing a controller with, the wrong robot.
check_brick() {
  local brick="$1" name
  if ! name=$(ssh "${SSH_OPTS[@]}" "$brick" hostname); then
    echo "" >&2
    echo "!! Could not log in to $brick." >&2
    echo "   Run ./doctor.sh $brick and see TROUBLESHOOTING.md (Connection / SSH)." >&2
    exit 1
  fi
  if [ "$name" != "$brick" ]; then
    echo "!! The brick plugged in is named '$name', not '$brick'." >&2
    echo "   Plug in the right brick, or see SETUP.md part 4.3 if it was never named." >&2
    exit 1
  fi
}
