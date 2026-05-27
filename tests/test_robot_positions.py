import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import time

class LLMCommander(Node):
    def __init__(self):
        super().__init__('llm_commander')
        self.publisher = self.create_publisher(String, 'target_point', 10)

    def send_command(self, command):
        msg = String()
        msg.data = command
        self.publisher.publish(msg)
        self.get_logger().info(f'Command sent: {command}')

def main():
    rclpy.init()
    commander_node = LLMCommander()
    commands = ["POINT_BANANA", "POINT_GLASS", "POINT_TOWEL"]
    try:
        while True:
            print("\nCommandes possibles :")
            for idx, cmd in enumerate(commands, 1):
                print(f"{idx}. {cmd}")
            print("0. Quitter")
            choice = input("Choisis une commande à envoyer (numéro) : ")
            if choice == "0":
                break
            if choice in [str(i) for i in range(1, len(commands)+1)]:
                cmd = commands[int(choice)-1]
                commander_node.send_command(cmd)
                time.sleep(0.2)
            else:
                print("Choix invalide.")
    except KeyboardInterrupt:
        pass
    commander_node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()