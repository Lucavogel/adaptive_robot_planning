from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import generate_demo_launch
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    moveit_config = MoveItConfigsBuilder("lynx_ses900", package_name="lynx_moveit_config").to_moveit_configs()
    
    # Charger les paramètres de trajectory execution
    trajectory_execution_file = os.path.join(
        get_package_share_directory("lynx_moveit_config"),
        "config",
        "trajectory_execution.yaml",
    )
    
    # Créer la configuration MoveIt avec nos paramètres personnalisés
    trajectory_execution_parameters = {
        "moveit_manage_controllers": True,
        "trajectory_execution.allowed_start_tolerance": 0.1,
        "trajectory_execution.allowed_goal_tolerance": 0.1,
        "trajectory_execution.allowed_goal_duration_margin": 2.0,
    }
    
    # Ajouter les paramètres à la configuration MoveIt
    moveit_config.trajectory_execution_parameters.update(trajectory_execution_parameters)
    
    return generate_demo_launch(moveit_config)
