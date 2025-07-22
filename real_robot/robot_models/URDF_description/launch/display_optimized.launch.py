from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution, Command
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Get the optimized URDF file
    urdf_file_path = PathJoinSubstitution([
        FindPackageShare('URDF_description'),
        'urdf',
        'lynx_ses900_optimized.urdf'
    ])

    # Read URDF content
    robot_description_content = Command(['cat ', urdf_file_path])

    # Robot state publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description_content}],
        output='screen'
    )

    # Joint state publisher GUI
    joint_state_publisher_gui = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        output='screen'
    )

    # RViz
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', PathJoinSubstitution([
            FindPackageShare('URDF_description'), 'rviz', 'display.rviz'
        ])],
        output='screen'
    )

    return LaunchDescription([
        robot_state_publisher,
        joint_state_publisher_gui,
        rviz
    ])
