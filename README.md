# ROS2 Gesture Interface

A real-time hand gesture recognition system that bridges a webcam-based MediaPipe/OpenCV pipeline (running on Windows) to a ROS2 node (running on Ubuntu/WSL2) via TCP, publishing recognized gestures and hand movements as ROS2 topics.

## What it does

- Detects hand gestures (**open**, **close**) and wrist movement direction (**up**, **down**, **left**, **right**) from a live webcam feed using MediaPipe's Hand Landmarker.
- Streams detected events over TCP from a Windows host to a ROS2 node running in WSL2/Ubuntu.
- The ROS2 node publishes these events as standard ROS2 topics (`/gesture` and `/movement`), making them available to any ROS2-based system — for example, a robot arm or mobile robot controller.

This project is a step toward gesture-based human-robot interaction: instead of a keyboard or joystick, hand gestures and motion become a control input that any ROS2 node can subscribe to.

## Current status

- ✅ Hand gesture detection (open/close) — working
- ✅ Wrist movement detection (up/down/left/right) — working
- ✅ TCP bridge from Windows → WSL2 — working
- ✅ ROS2 topic publishing (`/gesture`, `/movement`) — working
- 🔧 Physical robot integration — in progress, not yet connected
- 🔧 Config file / environment variables for IP, port, model path — not yet added (currently hardcoded)

## Architecture

```text
┌─────────────────────────────┐         TCP (port 5005)        ┌────────────────────────────────┐
│   Windows (gesture_win.py)  │ ─────────────────────────────▶ │  WSL2/Ubuntu (gesture_bridge_node) │
│   OpenCV + MediaPipe        │                                │  ROS2 node                         │
│   Hand Landmarker detection │                                │  Publishes /gesture, /movement     │
└─────────────────────────────┘                                └────────────────────────────────┘
```

- Windows side:
  - Captures webcam frames
  - Runs MediaPipe Hand Landmarker
  - Classifies gesture + movement
  - Sends text messages (`gesture:open`, `movement:left`, etc.) over a TCP socket.

- WSL2/ROS2 side:
  - Connects to the Windows TCP server as a client
  - Parses incoming messages
  - Publishes them as `std_msgs/String` on `/gesture` and `/movement`.

## Tech stack

- **Computer Vision**: OpenCV, MediaPipe (Tasks API — HandLandmarker)
- **Robotics**: ROS2 (Humble), rclpy, std_msgs
- **Communication**: Raw TCP sockets (Windows ↔ WSL2)
- **Environment**: Windows (PowerShell) + WSL2/Ubuntu 22.04

## Repository structure

```text
gesture_win.py              # Main detection script — runs on Windows
hand_landmarker.task         # MediaPipe Hand Landmarker model file
ros2_pkg/                    # ROS2 package (run inside WSL2/Ubuntu)
  ├── package.xml
  ├── setup.py
  ├── setup.cfg
  └── gesture_bridge/
      ├── __init__.py
      └── gesture_bridge_node.py   # ROS2 node: TCP client + topic publisher
```

## How to run

> This currently requires two terminals — one on Windows, one in WSL2.

### Terminal 1 — Windows (PowerShell)

```powershell
cd C:\Users\yashd\gesture_project
python gesture_win.py
```

Starts the camera feed and MediaPipe detector, then waits for the ROS2 node to connect on port 5005.

### Terminal 2 — WSL2/Ubuntu

```bash
cd ~/arm_project_ws
source install/setup.bash
ros2 run gesture_bridge gesture_bridge_node
```

Connects to the Windows TCP server and starts publishing to `/gesture` and `/movement`.

To verify it's working, open additional terminals in WSL2 and run:

```bash
ros2 topic echo /gesture
ros2 topic echo /movement
```

## Setup notes

- Requires **WSL2** (not native Linux) since the system bridges a Windows-side camera/MediaPipe process to a Linux-side ROS2 node.
- The WSL2 → Windows IP address is currently found manually via:
  ```bash
  ip route | grep default
  ```
  and hardcoded into `gesture_bridge_node.py`. This will differ between machines/sessions.
- The MediaPipe model path (`hand_landmarker.task`) is currently a hardcoded Windows path.
- No `requirements.txt` yet — install manually:
  ```bash
  pip install opencv-python mediapipe
  ```
- ROS2 package dependencies are listed in `package.xml` / `setup.py`. Build with:
  ```bash
  cd ~/arm_project_ws
  colcon build
  source install/setup.bash
  ```

## Roadmap

- [ ] Move hardcoded IP/port/paths into a config file or environment variables
- [ ] Add a `requirements.txt`
- [ ] Connect `/gesture` and `/movement` topics to an actual robot arm or mobile base controller
- [ ] Expand gesture vocabulary beyond open/close
- [ ] Add a single-command launch script instead of manual two-terminal startup
