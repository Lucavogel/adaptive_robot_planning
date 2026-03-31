#include <rclcpp/rclcpp.hpp>
#include <moveit/move_group_interface/move_group_interface.h>
#include <geometry_msgs/msg/pose.hpp>
#include <unordered_map>
#include <string>
#include <std_msgs/msg/string.hpp>
#include <std_msgs/msg/bool.hpp>
#include <moveit_msgs/msg/constraints.hpp>
#include <moveit_msgs/msg/joint_constraint.hpp>
#include <chrono>
#include <thread>

using namespace std::chrono_literals;

// Structure pour stocker une pose simple
struct SimplePose {
  double x, y, z, qx, qy, qz, qw;
};

// Dictionnaire des points connus
const std::unordered_map<std::string, SimplePose> NAMED_POINTS = {
  {"POINT_GLASS",  {-0.4974757730960846, 0.2704648971557617, 0.44947105646133423, -0.01543528214097023, 0.19247417151927948, -0.1641392707824707, 0.9673539996147156}},
  {"POINT_BANANA", {-0.515200674533844, -0.17847976088523865, 0.44864368438720703, -0.10198833048343658, 0.18502847850322723, 0.7221663594245911, 0.6586642265319824}},
  {"POINT_CUP",  {-0.47511497139930725, 0.014813380315899849, 0.39578431844711304, 0.09886115789413452, 0.07843184471130371, 0.8916751742362976, 0.43473020195961}}
};

// Fonction pour déplacer le robot vers un point nommé
bool move_to_named_point(
  const std::shared_ptr<rclcpp::Node>& node,
  moveit::planning_interface::MoveGroupInterface& move_group,
  const std::string& point_name)
{
  auto it = NAMED_POINTS.find(point_name);
  if (it == NAMED_POINTS.end()) {
    RCLCPP_ERROR(node->get_logger(), "Point inconnu: %s", point_name.c_str());
    return false;
  }

  const auto& pose = it->second;
  geometry_msgs::msg::Pose target_pose;
  target_pose.position.x = pose.x;
  target_pose.position.y = pose.y;
  target_pose.position.z = pose.z;
  target_pose.orientation.x = pose.qx;
  target_pose.orientation.y = pose.qy;
  target_pose.orientation.z = pose.qz;
  target_pose.orientation.w = pose.qw;

  // === Add joint constraints for joint_2 and joint_3 ===
  moveit_msgs::msg::Constraints constraints;

  moveit_msgs::msg::JointConstraint jc2;
  jc2.joint_name = "joint_2";
  jc2.position = 0.0; // Centered at 0
  jc2.tolerance_above = 1.396; // 80 deg in radians
  jc2.tolerance_below = 1.396;
  jc2.weight = 1.0;

  moveit_msgs::msg::JointConstraint jc3;
  jc3.joint_name = "joint_3";
  jc3.position = 0.0;
  jc3.tolerance_above = 1.5708; // 90 deg en radians
  jc3.tolerance_below = 1.5708; // 90 deg en radians
  jc3.weight = 1.0;

  constraints.joint_constraints.push_back(jc2);
  constraints.joint_constraints.push_back(jc3);

  move_group.setPathConstraints(constraints);

  move_group.setPoseTarget(target_pose);

  moveit::planning_interface::MoveGroupInterface::Plan plan;
  bool success = (move_group.plan(plan) == moveit::core::MoveItErrorCode::SUCCESS);

  // Remove constraints after planning to avoid affecting future plans
  move_group.clearPathConstraints();

  if (success) {
    RCLCPP_INFO(node->get_logger(), "Plan trouvé pour %s. Exécution...", point_name.c_str());
    move_group.execute(plan);
    return true;
  } else {
    RCLCPP_ERROR(node->get_logger(), "Échec de la planification pour %s.", point_name.c_str());
    return false;
  }
}

int main(int argc, char** argv)
{
  rclcpp::init(argc, argv);
  auto node = rclcpp::Node::make_shared("ik_move_cpp");

  moveit::planning_interface::MoveGroupInterface move_group(node, "Lynx_group");
  move_group.setGoalPositionTolerance(0.01);
  move_group.setGoalOrientationTolerance(0.01);

  // === Ajoute une variable pour mémoriser la dernière commande ===
  std::shared_ptr<std::string> last_command = std::make_shared<std::string>("");

  // Subscriber ROS2 pour les commandes de points
  auto subscription = node->create_subscription<std_msgs::msg::String>(
    "target_point", 10,
    [node, &move_group, last_command](const std_msgs::msg::String::SharedPtr msg) {
      const std::string& point_name = msg->data;
      RCLCPP_INFO(node->get_logger(), "Commande reçue : %s", point_name.c_str());

      if (NAMED_POINTS.count(point_name)) {
        *last_command = point_name; // mémorise la dernière commande
        move_to_named_point(node, move_group, point_name);
      } else {
        RCLCPP_WARN(node->get_logger(), "Point non reconnu : %s", point_name.c_str());
      }
    }
  );

  // Subscriber pour /execution_finished (Bool)
  auto exec_finished_sub = node->create_subscription<std_msgs::msg::Bool>(
    "/execution_finished", 10,
    [node, &move_group, last_command](const std_msgs::msg::Bool::SharedPtr msg) {
      RCLCPP_INFO(node->get_logger(), "Callback /execution_finished, last_command = %s", last_command->c_str());
      if (msg->data) {
        if (*last_command != "home") {
          RCLCPP_INFO(node->get_logger(), "Trajectoire terminée, attente 10s avant retour home...");
          rclcpp::sleep_for(std::chrono::seconds(5));
          RCLCPP_INFO(node->get_logger(), "Fin du sleep, retour à home !");
          move_group.setNamedTarget("home");
          moveit::planning_interface::MoveGroupInterface::Plan home_plan;
          bool home_success = (move_group.plan(home_plan) == moveit::core::MoveItErrorCode::SUCCESS);
          if (home_success) {
            move_group.execute(home_plan);
            RCLCPP_INFO(node->get_logger(), "Robot revenu à la position 'home'.");
            *last_command = "home"; // mémorise qu'on est à home
          } else {
            RCLCPP_ERROR(node->get_logger(), "Échec du retour à la position 'home'.");
          }
        } else {
          RCLCPP_INFO(node->get_logger(), "Déjà à home, pas de nouvel envoi.");
        }
      }
    }
  );

  // Affiche la position actuelle
  auto current_pose = move_group.getCurrentPose().pose;
  RCLCPP_INFO(node->get_logger(),
    "Position actuelle TCP: x=%.3f y=%.3f z=%.3f | qx=%.3f qy=%.3f qz=%.3f qw=%.3f",
    current_pose.position.x,
    current_pose.position.y,
    current_pose.position.z,
    current_pose.orientation.x,
    current_pose.orientation.y,
    current_pose.orientation.z,
    current_pose.orientation.w
  );

  // Garde le noeud vivant pour recevoir les commandes
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}

