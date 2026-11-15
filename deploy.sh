#!/usr/bin/env bash
# Copy your programs to a brick and run one, streaming its output here.
#
#   ./deploy.sh ev3-2                      copy all .py files, run controller.py
#   ./deploy.sh ev3-2 my_robot.py          copy all .py files, run my_robot.py
#   ./deploy.sh ev3-2 --copy               copy only (then unplug and start it
#                                          from the brick's File Browser)
#
# Ctrl+C stops the program and the motors.
set -euo pipefail
cd "$(dirname "$0")"
source ./lib.sh

need_brick "${1:-}"
BRICK="$1"
ARG="${2:-controller.py}"
# Same folder the VS Code ev3dev extension uses: /home/robot/<repo folder name>
REMOTE_DIR="/home/robot/$(basename "$PWD")"

check_brick "$BRICK"

echo "==> Copying programs to $BRICK:$REMOTE_DIR"
ssh "${SSH_OPTS[@]}" "$BRICK" "mkdir -p '$REMOTE_DIR'"
scp -q "${SSH_OPTS[@]}" ./*.py "$BRICK:$REMOTE_DIR/"
# Executable so they also start from the brick's File Browser.
ssh "${SSH_OPTS[@]}" "$BRICK" "chmod +x '$REMOTE_DIR'/*.py"
ls ./*.py | sed 's|^\./|    |'

if [ "$ARG" = "--copy" ]; then
  echo "==> Copied. Start it on the brick: File Browser -> $(basename "$PWD") -> program."
  exit 0
fi

if [ ! -f "$ARG" ]; then
  echo "!! No such program here: $ARG" >&2
  exit 1
fi

echo "==> Running $ARG on $BRICK (Ctrl+C stops the robot)"
# -t gives a terminal so Ctrl+C reaches the program and it stops the motors.
exec ssh -t "${SSH_OPTS[@]}" "$BRICK" "cd '$REMOTE_DIR' && python3 -u '$ARG'"
