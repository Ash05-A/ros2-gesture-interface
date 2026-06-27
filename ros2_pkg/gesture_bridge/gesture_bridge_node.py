import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import socket
import threading

# Windows host IP from: `ip route | grep default` in WSL2
WINDOWS_IP = "172.22.96.1"
PORT = 5005


class GestureBridgeNode(Node):
    def __init__(self):
        super().__init__("gesture_bridge_node")
        self.gesture_pub = self.create_publisher(String, "gesture", 10)
        self.movement_pub = self.create_publisher(String, "movement", 10)

        self.get_logger().info(f"Connecting to Windows at {WINDOWS_IP}:{PORT}...")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((WINDOWS_IP, PORT))
            self.get_logger().info("Connected to gesture server.")
        except Exception as e:
            self.get_logger().error(f"Failed to connect: {e}")
            raise

        self.thread = threading.Thread(target=self.reader_loop, daemon=True)
        self.thread.start()

    def reader_loop(self):
        buffer = ""
        while rclpy.ok():
            try:
                data = self.sock.recv(1024)
                if not data:
                    self.get_logger().warn("Connection closed by server.")
                    break
                buffer += data.decode("utf-8")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    self.handle_line(line)
            except Exception as e:
                self.get_logger().error(f"Socket error: {e}")
                break

    def handle_line(self, line: str):
        self.get_logger().info(f"Received: {line}")
        if line.startswith("gesture:"):
            value = line.split(":", 1)[1]
            msg = String()
            msg.data = value
            self.gesture_pub.publish(msg)
            self.get_logger().info(f"Published gesture: {value}")
        elif line.startswith("movement:"):
            value = line.split(":", 1)[1]
            msg = String()
            msg.data = value
            self.movement_pub.publish(msg)
            self.get_logger().info(f"Published movement: {value}")
        else:
            self.get_logger().warn(f"Unknown line: {line}")


def main(args=None):
    rclpy.init(args=args)
    node = GestureBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
