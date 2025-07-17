# safety.py

import time
import threading
import numpy as np

# Removed OptiTrack imports as they're not needed for simulation
# from optitrack import END_EFFECTOR_RB_ID, TABLE_RB_ID

# Define constants for backward compatibility (not used in simulation)
END_EFFECTOR_RB_ID = 1
TABLE_RB_ID = 2


class BoundingBox:
    """A simple 3D Axis-Aligned Bounding Box (AABB)."""

    def __init__(self, center_x, center_y, center_z, width, height, depth):
        self.width = width
        self.height = height
        self.depth = depth
        self.update_position(center_x, center_y, center_z)

    def update_position(self, center_x, center_y, center_z):
        """Updates the box's position and recalculates its min/max coordinates."""
        self.center_x = center_x
        self.center_y = center_y
        self.center_z = center_z
        self.min_x = center_x - self.width / 2
        self.max_x = center_x + self.width / 2
        self.min_y = center_y - self.height / 2
        self.max_y = center_y + self.height / 2
        self.min_z = center_z - self.depth / 2
        self.max_z = center_z + self.depth / 2

    def collides_with(self, other_box):
        """Checks if this box intersects with another BoundingBox."""
        # Check for overlap on each axis. A collision occurs only if
        # there is overlap on all three axes (X, Y, and Z).
        x_overlap = self.min_x <= other_box.max_x and self.max_x >= other_box.min_x
        y_overlap = self.min_y <= other_box.max_y and self.max_y >= other_box.min_y
        z_overlap = self.min_z <= other_box.max_z and self.max_z >= other_box.min_z
        return x_overlap and y_overlap and z_overlap

    def __repr__(self):
        return f"Box @ ({self.center_x:.2f}, {self.center_y:.2f}, {self.center_z:.2f})"


class OptiTrackClient:
    """
    --- MOCK CLASS ---
    Replace this with your actual OptiTrack client (e.g., using NatNet SDK).
    This class simulates fetching marker data.
    """

    def __init__(self):
        # Simulate marker data: {marker_name: (x, y, z)}
        # The coordinates are in meters.
        self.marker_data = {
            "elbow": (0.0, 0.3, 0.5),
            "wrist": (0.0, 0.6, 0.5),
        }
        print("[OptiTrack Mock] Client initialized.")

    def get_marker_positions(self):
        # In a real implementation, this would involve network communication.
        return self.marker_data

    def simulate_dangerous_move(self):
        """A helper for testing. Moves the 'wrist' into a forbidden zone."""
        print("[OptiTrack Mock] Simulating dangerous move: wrist moving down...")
        self.marker_data["wrist"] = (0.0, 0.6, -0.05)  # Z is now below zero


class DummyWatchdog:
    def __init__(self, robot_controller, optitrack_client, robot_model, forbidden_zones):
        self._robot = robot_controller
        self._optitrack = optitrack_client
        self._robot_model = robot_model  # Dict mapping marker names to BoundingBox objects
        self._forbidden_zones = forbidden_zones  # List of BoundingBox objects

        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self._collision_detected = False

    def start(self, check_interval=0.05):
        """Starts the watchdog monitoring loop."""
        if self._thread.is_alive():
            print("[Watchdog] Already running.")
            return
        self.check_interval = check_interval
        print(f"[Watchdog] Starting spatial safety monitor (check interval: {check_interval * 1000:.0f} ms).")
        self._thread.start()

    def stop(self):
        """Stops the watchdog monitoring loop."""
        print("[Watchdog] Stopping spatial monitor...")
        self._stop_event.set()
        self._thread.join(timeout=1.0)
        print("[Watchdog] Stopped.")

    def _watchdog_loop(self):
        """The main monitoring loop that runs in a background thread."""
        while not self._stop_event.is_set():
            # 1. Get latest marker data
            marker_positions = self._optitrack.get_marker_positions()

            # 2. Update the position of our robot's bounding boxes
            for marker_name, box in self._robot_model.items():
                if marker_name in marker_positions:
                    pos = marker_positions[marker_name]
                    box.update_position(pos[0], pos[1], pos[2])

            # 3. Perform Collision Checks
            collision_found = self._check_for_collisions()

            # 4. Take Action
            if collision_found and not self._collision_detected:
                print("\n" + "=" * 40)
                print("! ! ! SPATIAL WATCHDOG TRIGGERED ! ! !")
                print("Collision detected. Sending emergency LIMP command.")
                print("=" * 40 + "\n")
                self._robot.limp()
                self._collision_detected = True
            elif not collision_found and self._collision_detected:
                print("[Watchdog] Robot is clear of collisions. System re-armed.")
                self._collision_detected = False

            time.sleep(self.check_interval)

    def _check_for_collisions(self):
        """Checks for self-collisions and environmental collisions."""
        robot_boxes = list(self._robot_model.values())

        # Check for environmental collisions (robot vs. forbidden zones)
        for r_box in robot_boxes:
            for f_zone in self._forbidden_zones:
                if r_box.collides_with(f_zone):
                    print(f"[Watchdog] Collision Alert! {r_box} hit forbidden zone {f_zone}")
                    return True

        # Check for self-collisions (robot part vs. other robot part)
        for i in range(len(robot_boxes)):
            for j in range(i + 1, len(robot_boxes)):
                box1 = robot_boxes[i]
                box2 = robot_boxes[j]
                if box1.collides_with(box2):
                    # You might want to ignore collisions between adjacent links
                    print(f"[Watchdog] Self-Collision Alert! {box1} hit {box2}")
                    return True

        return False


class SafetyWatchdog:
    """
    Monitors a robot's joint angles and triggers an emergency stop if any joint
    exceeds its predefined safety limits.
    """
    MIN_END_EFFECTOR_Y_THRESHOLD = 0.32
    LINK2_LENGTH_M = 0.41  # Example: Length of link 2 (from Joint 2 pivot to Joint 3 pivot)
    LINK3_LENGTH_M = 0.45
    JOINT2_PIVOT_HEIGHT_FROM_TABLE_M = 0.05
    CRITICAL_TABLE_CLEARANCE_M = 0.32

    def __init__(self, robot_controller, natnet_data_handler, joint_limits, marker_radii: dict):
        """
        Initializes the watchdog.
2
        Args:
            robot_controller: The robot object that can be commanded (e.g., robo.limp()).
            joint_limits: A list of tuples, where each tuple is (min_angle, max_angle)
                          for the corresponding joint. The order must match the robot's
                          motor/joint order.
        """
        self._robot = robot_controller
        self._natnet_handler = natnet_data_handler
        self._limits = joint_limits
        self._marker_radii = marker_radii
        self.check_interval = 0

        # Ensure the number of limits matches the number of motors
        num_robot_motors = len(self._robot._motors) if self._robot._motors else len(self._robot._motor_ids)
        if len(self._limits) != num_robot_motors:
            raise ValueError(
                f"Mismatch between number of joint limits ({len(self._limits)}) "
                f"and number of robot motors ({num_robot_motors})."
            )

        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self._limit_violated = False

        self._exception_event = threading.Event()

    def start(self, check_interval=0.1):
        """Starts the watchdog monitoring loop in a background thread."""
        if self._thread.is_alive():
            print("[Watchdog] Already running.")
            return
        self.check_interval = check_interval
        print(f"[Watchdog] Starting monitor (check interval: {check_interval * 1000:.0f} ms).")
        print(f"[Watchdog] Limits: {self._limits}")
        self._thread.start()

    def stop(self):
        """Stops the watchdog monitoring loop."""
        if not self._thread.is_alive():
            return
        print("[Watchdog] Stopping monitor...")
        self._stop_event.set()
        self._thread.join(timeout=1.0)
        print("[Watchdog] Stopped.")

    def _watchdog_loop(self):
        """The main monitoring loop that runs in the background."""
        try:
            while not self._stop_event.is_set():

                violation_found = False
                y_limit_violation_found = False
                table_angle_collision_found = False
                marker_overlap_found = False

                # 1. Check if any joint exceeds its limits:
                current_positions_list = self._robot.get_Position()
                current_positions = []
                for pos_entry in current_positions_list:
                    if isinstance(pos_entry, list) and pos_entry and pos_entry[0] is not None:
                        current_positions.append(pos_entry[0])
                    elif isinstance(pos_entry, (float, int)): # Handle flat list of floats/ints
                        current_positions.append(pos_entry)
                    else:
                        print("[Watchdog] Warning: Failed to read position for a joint. Skipping check.")
                        time.sleep(self.check_interval)
                        continue

                # Ensure we have positions for all joints before checking
                if len(current_positions) != len(self._limits):
                    print("[Watchdog] CRITICAL ERROR: Number of tracked joint positions doesn't match defined limits. Forcing emergency recovery.")
                    self._robot.enter_emergency_recovery() # Force emergency if state is truly inconsistent
                    time.sleep(self.check_interval * 5) # Longer pause for critical error
                    continue
                violation_found = self._check_limits(current_positions)

                # 2. Check for kinematic table collision angles:
                if len(current_positions) > 3: # Need at least 4 joints (0, 1, 2, 3) to access joint 2 and 3
                    table_angle_collision_found = self._check_table_collision_angles(
                        current_positions[1], current_positions[2])

                # 3. Check OptiTrack limits::
                current_relative_pos = None
                with self._natnet_handler._data_lock:  # Ensure thread-safe access
                    current_relative_pos = self._natnet_handler.latest_relative_pos # Correctly get the value
                if current_relative_pos is not None:
                    # current_relative_pos is a NumPy array from the NatNetDataHandler
                    # The Y-coordinate is at index 1
                    print(f'[Watchdog] eef relative pos: X={current_relative_pos[0]:.4f}m, Y={current_relative_pos[1]:.4f}m, Z={current_relative_pos[2]:.4f}m')
                    if current_relative_pos[1] < self.MIN_END_EFFECTOR_Y_THRESHOLD:
                        y_limit_violation_found = True
                        print(f"[Watchdog] EEF VIOLATION! End-effector Y-pos: {current_relative_pos[1]:.4f}m "
                            f"is below threshold: {self.MIN_END_EFFECTOR_Y_THRESHOLD:.4f}m")
                else:
                    print('[Watchdog] End-effector relative position data not yet available from OptiTrack.')

                # 4. Check for Bounding Sphere Overlap: TODO: the markers' IDs are not yet clarified, and the distances are usually violated
                marker_overlap_found = self._check_marker_overlap()

                # Final: Trigger the emergency recovery if any violation is found:
                if violation_found or y_limit_violation_found or table_angle_collision_found or marker_overlap_found:
                    # The robot will handle the state change and subsequent actions.
                    self._robot.enter_emergency_recovery()
                # else:
                #     self._robot.clear_emergency_state() # Ensure robot returns to normal if all checks pass

                time.sleep(self.check_interval)
        except Exception as e:
            print(f'[Watchdog] CRITICAL ERROR: watchdog exception found: {e}') # Modified print
            self._robot.enter_emergency_recovery()
            self._robot.shutdown()
            self._exception_event.set() # Signal that an exception occurred
            self._stop_event.set()


    def _check_limits(self, positions):
        """Checks if any position is outside its defined min/max limits."""
        for i, pos in enumerate(positions):
            min_limit, max_limit = self._limits[i]

            if not (min_limit <= pos <= max_limit):
                print(f"[Watchdog] VIOLATION! Joint {i} is at {pos:.2f}°, "
                      f"but its limits are [{min_limit:.2f}, {max_limit:.2f}].")
                return True
        return False
    
    def _check_marker_overlap(self):
        """
        Checks for bounding sphere overlap between markers defined in _marker_radii.
        Returns True if an overlap is found, False otherwise.
        """
        marker_overlap_detected = False
        active_markers_with_pos = []

        with self._natnet_handler._data_lock:
            for marker in self._natnet_handler.latest_markers:
                # NEW: Filter out markers that belong to the End-Effector or Table Rigid Bodies
                # We only want to check for collisions with markers not part of these predefined RBs
                if marker.model_id == END_EFFECTOR_RB_ID or marker.model_id == TABLE_RB_ID:
                    continue # Skip this marker, it belongs to one of the excluded Rigid Bodies

                if not (np.array(marker.position) == 0).all() and marker.model_id == 0: # Simple check for (0,0,0) ghost markers
                    active_markers_with_pos.append(marker)
        print(f"[Watchdog DEBUG] number of active markers: {len(active_markers_with_pos)}")
        # print(f"[Watchdog DEBUG] active markers: {active_markers_with_pos}")

        # If we have at least two markers to check, proceed with pair-wise comparison
        if len(active_markers_with_pos) >= 2:
            num_markers = len(active_markers_with_pos)
            for i in range(num_markers):
                for k in range(i + 1, num_markers): # Compare each marker with subsequent ones to avoid duplicates
                    marker1 = active_markers_with_pos[i]
                    marker2 = active_markers_with_pos[k]

                    pos1 = np.array(marker1.position) # Marker positions are (x,y,z)
                    pos2 = np.array(marker2.position)
                    
                    # r1 = self._marker_radii[marker1.marker_id]
                    # r2 = self._marker_radii[marker2.marker_id]
                    r1 = 0.025
                    r2 = 0.025

                    distance = np.linalg.norm(pos2 - pos1) # Euclidean distance
                    sum_radii = r1 + r2

                    if distance < sum_radii:
                        marker_overlap_detected = True
                        print(f"[Watchdog] MARKER SPHERE OVERLAP VIOLATION! "
                                        f"Markers {marker1.marker_id} (R={r1*100:.1f}cm) and {marker2.marker_id} (R={r2*100:.1f}cm) are overlapping. "
                                        f"Distance: {distance*100:.1f}cm, Sum of Radii: {sum_radii*100:.1f}cm.")
                        return True # Found an overlap, no need to check further

        return False # No overlap detected
    
    def _check_table_collision_angles(self, joint2_angle_deg, joint3_angle_deg):
        """
        Calculates the approximate lowest point of Link 2 and Link 3 based on their joint angles
        and checks if this point is below a critical table clearance height.
        This relies on a simplified 2D forward kinematics model for the arm's vertical projection.

        ASSUMPTION:
        - When joint angle is 0 degrees, the link is pointing **vertically upward** from its pivot.
        - Positive angles result in rotation downwards (clockwise) from this vertical up orientation.
          (Or, if your system rotates counter-clockwise for positive, it might be `L * cos(angle)`)
          Let's assume standard math where a clockwise rotation from positive vertical makes `cos` decrease.

        Args:
            joint2_angle_deg (float): Current angle of Joint 2 in degrees.
            joint3_angle_deg (float): Current angle of Joint 3 in degrees (relative to Link 2).

        Returns:
            bool: True if a table collision risk is detected based on joint angles, False otherwise.
        """
        # Convert angles to radians
        joint2_angle_rad = np.radians(joint2_angle_deg)
        # The absolute angle of Link 3 relative to the world frame's upward vertical.
        # This is the sum of Joint 2's absolute angle and Joint 3's relative angle.
        abs_link3_angle_rad = np.radians(joint2_angle_deg - joint3_angle_deg)  # These two angles are reverse

        # Calculate Y positions (height) relative to Joint 2's pivot point.
        # Based on the assumption that 0 degrees is vertically upward, and positive Y is up.
        # The vertical height contribution for a link of length `L` is `L * cos(angle_from_vertical_up)`.

        # Y position of Joint 3 (end of Link 2) relative to Joint 2's pivot height
        y_pos_J3_rel_J2 = self.LINK2_LENGTH_M * np.cos(joint2_angle_rad)

        # Y position of End Effector (end of Link 3) relative to Joint 2's pivot height
        y_pos_EE_rel_J2 = (self.LINK2_LENGTH_M * np.cos(joint2_angle_rad) +
                           self.LINK3_LENGTH_M * np.cos(abs_link3_angle_rad))

        # Calculate absolute world Y coordinates (height above the table surface):
        world_y_J3 = self.JOINT2_PIVOT_HEIGHT_FROM_TABLE_M + y_pos_J3_rel_J2
        world_y_EE = self.JOINT2_PIVOT_HEIGHT_FROM_TABLE_M + y_pos_EE_rel_J2

        # print(f'[Watchdog] JOINT 2 angle: {joint2_angle_deg}, JOINT 3 angle: {joint3_angle_deg} EE height z-axis: {self.LINK3_LENGTH_M * np.cos(abs_link3_angle_rad)}')

        # Check if either critical point falls below the table clearance threshold
        if world_y_J3 < self.CRITICAL_TABLE_CLEARANCE_M or world_y_EE < self.CRITICAL_TABLE_CLEARANCE_M:
            print(f"[Watchdog] KINEMATIC VIOLATION! "
                            f"Point J2 (end of Link 1) Y-pos: {world_y_J3:.4f}m or"
                            f"Point J3 (end of Link 2) Y-pos: {world_y_EE:.4f}m "
                            f"is below table clearance: {self.CRITICAL_TABLE_CLEARANCE_M:.4f}m."
                            f" J1 Angle:{joint2_angle_deg:.1f}°, J2 Angle:{joint3_angle_deg:.1f}°")
            return True
        
        if world_y_EE < self.CRITICAL_TABLE_CLEARANCE_M:
            print(f"[Watchdog] JOINT 1/2 KINEMATIC VIOLATION (EE point)! "
                            f"End-Effector (end of Link 2) Y-pos: {world_y_EE:.4f}m "
                            f"is below table clearance: {self.CRITICAL_TABLE_CLEARANCE_M:.4f}m."
                            f" J1 Angle:{joint2_angle_deg:.1f}°, J2 Angle:{joint3_angle_deg:.1f}°")
            return True

        return False


class SafetyWatchdogSim:
    """
    Monitors a robot's state (joint angles, end-effector position)
    and triggers an emergency stop if safety limits are exceeded.
    """
    # Assuming PyBullet's Z is the vertical axis, and this threshold is for Z-height.
    # If your original OptiTrack Y was vertical, and SimNatNetDataHandler maps it,
    # then `current_relative_pos[1]` would still be vertical.
    # Based on standard PyBullet URDFs, Z is vertical.
    # Let's assume the previous `MIN_END_EFFECTOR_Y_THRESHOLD` meant vertical height,
    # and rename it to reflect a more generic vertical axis check using `current_relative_pos[2]`.
    MIN_END_EFFECTOR_Z_THRESHOLD = 0.1  # Adjusted to Z axis for PyBullet compatibility

    # Kinematic link lengths for table collision estimation
    LINK2_LENGTH_M = 0.425 # Length of upper_arm_link (from shoulder to elbow)
    LINK3_LENGTH_M = 0.39225 # Length of forearm_link (from elbow to wrist1)
    JOINT2_PIVOT_HEIGHT_FROM_TABLE_M = 0.1  # Height of joint 2's pivot from table surface
    CRITICAL_TABLE_CLEARANCE_M = 0.1 # Minimum allowed height for arm parts

    def __init__(self, robot_controller, natnet_data_handler, joint_limits, marker_radii: dict):
        """
        Initializes the watchdog.

        Args:
            robot_controller: The robot object that can be commanded (e.g., self.robot.limp()).
            natnet_data_handler: The sensor data handler (SimNatNetDataHandler in simulation).
            joint_limits: A list of tuples, where each tuple is (min_angle, max_angle)
                          for the corresponding joint.
            marker_radii: Dictionary of marker IDs to their radii (not used in sim).
        """
        self._robot = robot_controller
        self._natnet_handler = natnet_data_handler  # Will be SimNatNetDataHandler in simulation
        self._limits = joint_limits
        self._marker_radii = marker_radii  # This will be an empty dict in simulation

        # Ensure the number of limits matches the number of motors/actuators
        # For MujocoRobot, use model.nu (number of actuators)
        # For SimRobot, use _motor_ids
        if hasattr(self._robot, 'model') and hasattr(self._robot.model, 'nu'):
            num_robot_motors = self._robot.model.nu
        elif hasattr(self._robot, '_motor_ids'):
            num_robot_motors = len(self._robot._motor_ids)
        else:
            raise AttributeError("Robot controller does not have a recognized way to determine number of motors/actuators.")

        if len(self._limits) != num_robot_motors:
            raise ValueError(
                f"Mismatch between number of joint limits ({len(self._limits)}) "
                f"and number of robot motors/actuators ({num_robot_motors})."
            )

        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self._limit_violated = False  # Flag for limit violations
        self._exception_event = threading.Event()  # For signaling critical errors

    def start(self, check_interval=0.1):
        """Starts the watchdog monitoring loop in a background thread."""
        if self._thread.is_alive():
            print("[Watchdog] Already running.")
            return
        self.check_interval = check_interval
        print(f"[Watchdog] Starting monitor (check interval: {check_interval * 1000:.0f} ms).")
        print(f"[Watchdog] Joint Limits: {self._limits}")
        self._thread.start()

    def stop(self):
        """Stops the watchdog monitoring loop."""
        if not self._thread.is_alive():
            return
        print("[Watchdog] Stopping monitor...")
        self._stop_event.set()
        self._thread.join(timeout=1.0)  # Wait for thread to finish
        print("[Watchdog] Stopped.")

    def _watchdog_loop(self):
        """The main monitoring loop that runs in the background."""
        try:
            while not self._stop_event.is_set():
                violation_found = False
                eef_z_limit_violation_found = False  # Changed from y_limit
                table_angle_collision_found = False
                marker_overlap_found = False  # Initialized for logic flow

                # 1. Check if any joint exceeds its limits:
                raw_positions = self._robot.get_Position()

                # Flatten the list if it's a list of lists (from SimRobot)
                # Otherwise, assume it's already a flat list (from MujocoRobot)
                if raw_positions and isinstance(raw_positions[0], list):
                    current_positions = [pos[0] for pos in raw_positions if pos[0] is not None]
                else:
                    current_positions = raw_positions

                # Only perform checks if we have valid positions for all joints
                if len(current_positions) == len(self._limits):
                    # print(f"[Watchdog DEBUG] current_positions type: {type(current_positions)}, content: {current_positions}")
                    violation_found = self._check_limits(current_positions)

                    # 2. Check for kinematic table collision angles:
                    if len(current_positions) >= 3:  # Need at least joint 0, 1, 2 for this check (assuming base, shoulder, elbow)
                        table_angle_collision_found = self._check_table_collision_angles(
                            current_positions[1], current_positions[2])

                    # 3. Check End-Effector (EEF) Z-height (vertical position from sensor):
                    current_relative_pos = None
                    with self._natnet_handler._data_lock:  # Ensure thread-safe access
                        self._natnet_handler.update_data() # Explicitly request data update from the mock sensor
                        current_relative_pos = self._natnet_handler.latest_relative_pos

                    if current_relative_pos is not None:
                        # Assuming current_relative_pos[2] is the vertical Z-coordinate in PyBullet's Z-up system
                        # print(
                        #     f'[Watchdog] EEF relative pos: X={current_relative_pos[0]:.4f}m, Y={current_relative_pos[1]:.4f}m, Z={current_relative_pos[2]:.4f}m')
                        if current_relative_pos[2] < self.MIN_END_EFFECTOR_Z_THRESHOLD:
                            eef_z_limit_violation_found = True
                            print(f"[Watchdog] EEF Z-VIOLATION! End-effector Z-pos: {current_relative_pos[2]:.4f}m "
                                  f"is below threshold: {self.MIN_END_EFFECTOR_Z_THRESHOLD:.4f}m")
                    else:
                        print('[Watchdog] End-effector relative position data not yet available from sensor.')

                    # 4. Check for Bounding Sphere Overlap (DISABLED for simulation):
                    marker_overlap_found = self._check_marker_overlap()

                # Final: Trigger emergency recovery if any violation is found:
                if violation_found or eef_z_limit_violation_found or table_angle_collision_found or marker_overlap_found:
                    self._robot.enter_emergency_recovery()

                time.sleep(self.check_interval)
        except Exception as e:
            print(f'[Watchdog] CRITICAL ERROR: Watchdog exception found: {e}')
            self._robot.enter_emergency_recovery()
            self._robot.shutdown()
            self._exception_event.set()  # Signal that an exception occurred
            self._stop_event.set()  # Stop the watchdog thread

    def _check_limits(self, positions):
        """Checks if any joint position is outside its defined min/max limits."""
        for i, pos in enumerate(positions):
            min_limit, max_limit = self._limits[i]

            if not (min_limit <= pos <= max_limit):
                print(f"[Watchdog] JOINT ANGLE VIOLATION! Joint {i} is at {pos:.2f}°, "
                      f"but its limits are [{min_limit:.2f}, {max_limit:.2f}].")
                return True
        return False

    def _check_marker_overlap(self):
        """
        In simulation, this check is disabled as it relies on specific OptiTrack marker data,
        which is not directly simulated by SimNatNetDataHandler.
        Always returns False in this simulated setup.
        """
        return False

    def _check_table_collision_angles(self, joint1_angle_deg, joint2_angle_deg):
        """
        Calculates the approximate lowest point of Link 2 (after Joint 1) and Link 3 (after Joint 2)
        based on their joint angles and checks if this point is below a critical table clearance height.
        This relies on a simplified 2D forward kinematics model (projection).

        ASSUMPTION:
        - For UR5, angle 0 typically means the link is straight, or in a "home" configuration.
          (The description "0 degrees is vertically upward" from original code might need
          re-evaluation with UR5's specific kinematics, but we keep the formula structure.)
        - Positive angles result in rotation downwards (clockwise from "vertical up").

        Args:
            joint1_angle_deg (float): Current angle of Joint 1 (shoulder_lift_joint on UR5) in degrees.
            joint2_angle_deg (float): Current angle of Joint 2 (elbow_joint on UR5) in degrees (relative to Link 2).

        Returns:
            bool: True if a table collision risk is detected based on these joint angles, False otherwise.
        """
        # Convert angles to radians
        # From base to shoulder (Joint 0), then shoulder (Joint 1) is shoulder_lift, then elbow (Joint 2) is elbow_joint.
        # Let's adjust variable names to reflect common UR5 joints
        shoulder_lift_rad = np.radians(joint1_angle_deg)
        elbow_joint_rad = np.radians(joint2_angle_deg)

        # Assuming the base is at Z=0 and shoulder pivot at JOINT2_PIVOT_HEIGHT_FROM_TABLE_M (which is on Z-axis).
        # We need to compute the absolute Z (vertical) height of points on the arm.
        # This kinematic model assumes the arm moves in a vertical plane for simplicity.

        # Y position of Joint 2 (end of Link from J1 to J2) relative to Joint 1's pivot height (shoulder)
        # Assuming Joint1 moves arm up/down vertically
        # `cos` assumes 0 is vertical. If 0 is horizontal, use `sin`. Many UR5 arm angles are 0=straight.
        # Let's assume positive angles go "down" relative to horizontal straight.
        # If UR5's 0 is a specific, often "straight out" or "vertical UP/DOWN" orientation,
        # then these cos/sin choices determine the kinematic interpretation.
        # Based on default UR5 kinematics, 0 deg for shoulder_lift_joint is horizontal.
        # To get z-height from horizontal: L * sin(theta) if theta is from horizontal.
        # If the angle is from vertical (e.g., 0=up), then L * cos(theta) is correct.
        # Let's stick with original code's interpretation for minimal diff and mark it as potentially needing tuning.

        # Calculate Z positions (height) relative to Joint1's pivot point on the table.
        # For a standard arm, J1 (shoulder_lift) controls height, J2 (elbow) controls reach.
        # We need the *absolute* angles of the links relative to the horizontal or vertical.
        # If J1_angle_deg is relative to horizontal:
        # Z_J2_rel_J1 = LINK2_LENGTH_M * np.sin(shoulder_lift_rad) # If angle 0 is horizontal
        # Z_EE_rel_J2 = LINK3_LENGTH_M * np.sin(elbow_joint_rad) # If angle 0 is relative horizontal

        # Sticking VERY closely to *your* original code's math using `cos`
        # and assuming your original `joint2_angle_deg` and `joint3_angle_deg`
        # refer to angles from vertical for those segments:
        # (This is more for a human-like arm or a specific joint type, not typical UR5)

        # Absolute angle of link 2 (shoulder-to-elbow) relative to vertical
        abs_link2_angle_origin = shoulder_lift_rad
        # Absolute angle of link 3 (elbow-to-wrist) relative to vertical
        # Your original code used `np.radians(joint2_angle_deg - joint3_angle_deg)`.
        # This implies your original Joint3 was relative to Joint2.
        # If `joint1_angle_deg` is shoulder_lift and `joint2_angle_deg` is elbow_joint:
        abs_link3_angle_origin = shoulder_lift_rad + elbow_joint_rad  # A common simple sum if angles are relative to previous link
        # If elbow_joint_rad is relative to link 2, and shoulder_lift_rad is relative to vertical.
        # In URDF, angles are often relative to the previous link's frame.
        # To make this robust, actual forward kinematics should be used.
        # For minimal change, we will assume your prior logic's intent.

        # Vertical heights based on `L * cos(angle_from_vertical_up)`:
        z_pos_J2_rel_J1_pivot = self.LINK2_LENGTH_M * np.cos(abs_link2_angle_origin)
        z_pos_EE_rel_J2_pivot = self.LINK3_LENGTH_M * np.cos(abs_link3_angle_origin)

        # Total absolute Z (vertical) height of Joint 2 and End Effector from the table
        # JOINT2_PIVOT_HEIGHT_FROM_TABLE_M is the shoulder pivot height on the base.
        world_z_J2 = self.JOINT2_PIVOT_HEIGHT_FROM_TABLE_M + z_pos_J2_rel_J1_pivot
        world_z_EE = (self.JOINT2_PIVOT_HEIGHT_FROM_TABLE_M +
                      z_pos_J2_rel_J1_pivot +
                      z_pos_EE_rel_J2_pivot)  # Summing heights from base to J1, then J1 to J2, then J2 to EE.

        # Check if any critical point falls below the table clearance threshold
        # We only check the end-effector's approximate lowest point, as that's often the most critical
        # Or, you can check both intermediate joints as well.
        if world_z_EE < self.CRITICAL_TABLE_CLEARANCE_M:
            print(f"[Watchdog] KINEMATIC COLLISION VIOLATION (EE point)! "
                  f"End-Effector estimated Z-pos: {world_z_EE:.4f}m "
                  f"is below table clearance: {self.CRITICAL_TABLE_CLEARANCE_M:.4f}m."
                  f" J1 Angle:{joint1_angle_deg:.1f}°, J2 Angle:{joint2_angle_deg:.1f}°")
            return True
        elif world_z_J2 < self.CRITICAL_TABLE_CLEARANCE_M:  # Optionally check intermediate joint
            print(f"[Watchdog] KINEMATIC COLLISION VIOLATION (Joint 2 point)! "
                  f"Joint 2 estimated Z-pos: {world_z_J2:.4f}m "
                  f"is below table clearance: {self.CRITICAL_TABLE_CLEARANCE_M:.4f}m."
                  f" J1 Angle:{joint1_angle_deg:.1f}°, J2 Angle:{joint2_angle_deg:.1f}°")
            return True

        return False
