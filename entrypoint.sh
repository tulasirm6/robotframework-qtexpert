#!/usr/bin/env bash
set -e

# Start Xvfb virtual framebuffer on display :99
Xvfb :99 -screen 0 1024x768x24 -ac &
XVFB_PID=$!
export DISPLAY=:99
sleep 1

# Setup VNC password ('secret') for macOS Screen Sharing compatibility
mkdir -p /root/.vnc
x11vnc -storepasswd secret /root/.vnc/passwd > /dev/null 2>&1 || true

# Start x11vnc server with password
x11vnc -display :99 -rfbauth /root/.vnc/passwd -forever -shared -bg -quiet > /dev/null 2>&1 || true

# Start Openbox Window Manager for movable/resizable windows with titlebars
openbox &

# Start tint2 taskbar so minimized windows can be seen and restored with a click
tint2 &

echo "=== Headless Xvfb Display :99 Started (PID: ${XVFB_PID}) ==="
echo "=== VNC Server Started on port 5900 (Password: secret) ==="
echo "=== Connect from macOS via: open vnc://:secret@localhost:5900 ==="

# Run the provided command or default tests
if [ $# -eq 0 ]; then
    robot --pythonpath src --outputdir results tests/preload_test.robot
else
    "$@"
fi
