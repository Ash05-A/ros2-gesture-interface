import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import socket
import threading

# ---------------- TCP SERVER SETUP ----------------
HOST = "0.0.0.0"  # listen on all interfaces on Windows
PORT = 5005       # choose any free port

client_conn = None
client_lock = threading.Lock()


def start_server():
    global client_conn
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(1)
    print(f"[TCP] Waiting for ROS2 client on port {PORT}...")
    conn, addr = srv.accept()
    print(f"[TCP] Client connected from {addr}")
    with client_lock:
        client_conn = conn


def send_line(msg: str):
    """Send a line to the client if connected."""
    global client_conn
    with client_lock:
        if client_conn is not None:
            try:
                client_conn.sendall((msg + "\n").encode("utf-8"))
            except Exception as e:
                print("[TCP] send error:", e)
                client_conn = None


# Start server thread
server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

# ---------------- MEDIAPIPE SETUP ----------------
model_path = r"C:\Users\yashd\gesture_project\hand_landmarker.task"

base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1
)
landmarker = vision.HandLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Could not open camera")
    exit(1)

last_gesture = None
last_wrist_x = None
last_wrist_y = None


def classify_gesture(hand_landmarks):
    """
    Classify hand as open/close/unknown based on finger tips vs PIP joints.
    Safely handles cases where landmarks list is shorter than expected.
    """
    tips_pips = [(8, 6), (12, 10), (16, 14), (20, 18)]
    fingers_extended = 0

    n = len(hand_landmarks)
    if n < 21:
        return "unknown"

    for tip_idx, pip_idx in tips_pips:
        if tip_idx >= n or pip_idx >= n:
            return "unknown"
        tip = hand_landmarks[tip_idx]
        pip = hand_landmarks[pip_idx]
        if tip.y < pip.y:
            fingers_extended += 1

    if fingers_extended >= 3:
        return "open"
    elif fingers_extended == 0:
        return "close"
    else:
        return "unknown"


# ---------------- MAIN LOOP ----------------
while True:
    ok, frame = cap.read()
    if not ok:
        print("No frame from camera")
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    result = landmarker.detect(mp_image)

    gesture = "none"
    movement = "none"

    if result.hand_landmarks:
        hand = result.hand_landmarks[0]

        # Extra safety: ensure enough landmarks before classification
        if len(hand) < 21:
            gesture = "unknown"
        else:
            gesture = classify_gesture(hand)

        # Wrist landmark index 0
        wrist = hand[0]
        wrist_x = wrist.x
        wrist_y = wrist.y

        # If we have a previous wrist position, compute delta
        if last_wrist_x is not None and last_wrist_y is not None:
            dx = wrist_x - last_wrist_x
            dy = wrist_y - last_wrist_y
            threshold = 0.03  # tune if needed

            if abs(dx) > abs(dy):
                if dx > threshold:
                    movement = "right"
                elif dx < -threshold:
                    movement = "left"
            else:
                if dy > threshold:
                    movement = "down"
                elif dy < -threshold:
                    movement = "up"

        # Update last wrist position
        last_wrist_x = wrist_x
        last_wrist_y = wrist_y

        # Draw landmarks
        for lm in hand:
            h, w, _ = frame.shape
            cx, cy = int(lm.x * w), int(lm.y * h)
            cv2.circle(frame, (cx, cy), 2, (0, 255, 0), -1)

    cv2.putText(frame, f"Gesture: {gesture}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, f"Move: {movement}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    cv2.imshow("Gesture (Windows)", frame)

    # Only send when meaningful
    if gesture in ("open", "close") and gesture != last_gesture:
        print("Gesture:", gesture)
        send_line(f"gesture:{gesture}")
        last_gesture = gesture

    if movement in ("left", "right", "up", "down"):
        print("Movement:", movement)
        send_line(f"movement:{movement}")

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Exiting gesture program.")