# robot.py

import os
import time
import serial
import atexit
import subprocess
import threading

import motor_cmd as lssc
import motor


class Robot:

    def __init__(self, portname="/dev/ttyACM0"):
        self._bus = None
        self._bus_lock = threading.Lock()
        self._motor_ids = [0,1,2,3,4,5]
        self._portname = portname
        self._motors = []
        atexit.register(self.close_bus)

        # NEW: Emergency state attributes
        self._in_emergency_state = False
        self._emergency_thread = None
        self.home_position = [0, 0, 0, 0, 0, 0]  # Define a safe home position

        # NEW: Store the last read joint angles (in degrees)
        self._current_joint_angles_deg = [0.0] * len(self._motor_ids)

    def init_bus(self):
        print(f"[Lynx] Attempting to open serial port: {self._portname}")
        try:
            if not os.path.exists(self._portname):
                print(f"\n[Lynx] Error: Serial port '{self._portname}' does not exist. Is the device connected?")
                self._bus = None
                return False

            self._bus = serial.Serial(self._portname, lssc.LSS_DefaultBaud )
            self._bus.timeout = 0.1
            print("[Lynx] Serial bus opened successfully.")
            return True

        except serial.SerialException as e:
            if "Permission denied" in str(e) and "[Errno 13]" in str(e):
                print(f"\n[Lynx] Warning: Permission denied for serial port '{self._portname}'.")
                print("Attempting to grant temporary permissions via sudo. You may be prompted for your password.")
                try:
                    # Attempt to change permissions using sudo
                    # WARNING: This is temporary and insecure for a general application.
                    # It will prompt for sudo password.
                    subprocess.run(["sudo", "chmod", "666", self._portname], check=True)
                    print(f"Permissions for {self._portname} temporarily updated. Retrying bus initialization...")
                    # Retry opening the serial port after changing permissions
                    self._bus = serial.Serial(self._portname, lssc.LSS_DefaultBaud )
                    self._bus.timeout = 0.1
                    print("[Lynx] Serial bus opened successfully after permission attempt.")
                    return True
                except subprocess.CalledProcessError as sub_e:
                    print(f"\n[Lynx] Error: Failed to change permissions using sudo: {sub_e}")
                    print("Please ensure your user is in the sudoers file and try again.")
                except serial.SerialException as retry_e:
                    print(f"\n[Lynx] Error: Failed to open port even after attempting permission change: {retry_e}")
                except Exception as other_e:
                    print(f"\n[Lynx] Error: An unexpected error occurred during permission attempt: {other_e}")

                print("\n**RECOMMENDED SOLUTION (Permanent & Secure):**")
                print(f"  1. Add your user to the 'dialout' group (or 'uucp'):")
                print(f"     sudo usermod -a -G dialout {os.getlogin()}")
                print(f"  2. **Log out and log back in** (or reboot).")
                print(f"Original error: {e}\n")

            else:
                print(f"\n[Lynx] Error: Could not open serial port '{self._portname}'.")
                print(f"Reason: {e}\n")
            self._bus = None
            return False
        except Exception as e:
            print(f"\n[Lynx] Error: An unexpected error occurred during bus initialization: {e}\n")
            self._bus = None
            return False
    

    def close_bus(self):
        if self._bus is not None:
            print("[Lynx] Closed the bus")
            self._bus.close()
            del self._bus
            self._bus = None

    def init_motors(self):
        if self._bus is None:
            return None
        
        self._motors = []
        for idx in self._motor_ids:
            m = motor.Motor(id = idx, bus=self._bus, bus_lock=self._bus_lock)
            self._motors.append(m)

    def get_Position(self):
        """
        Queries each motor for its position (in centi-degrees), converts
        to degrees (float), and returns a list of [pos] or [None] if reading failed.
        Also updates the internal _current_joint_angles_deg attribute.
        """
        # Store temporary raw readings from motors (can contain None for failed reads)
        pos_all_raw_from_motors = []
        
        # Initialize a new list for _current_joint_angles_deg, starting with its current values.
        # This ensures new_current_joint_angles_deg always has a full list of numerical values.
        # If _current_joint_angles_deg is shorter than expected (e.g., due to an init bug),
        # pad it with 0.0s for missing elements to ensure correct length before updates.
        new_current_joint_angles_deg = ([0.0] * len(self._motor_ids))
        for i in range(min(len(self._current_joint_angles_deg), len(self._motor_ids))):
            new_current_joint_angles_deg[i] = self._current_joint_angles_deg[i]

        for i, m in enumerate(self._motors):
            raw = m.getPosition() # Get raw reading (e.g., 1800, or None)
            pos_all_raw_from_motors.append(raw) # Store this for the original return value format

            if raw is None:
                # If read failed, new_current_joint_angles_deg[i] retains its existing value (from previous cycle or init).
                # Print a more informative message about what value is being retained.
                print(f"[Lynx] Warning: Motor {m._id} returned no data (None). Retaining previous valid angle ({new_current_joint_angles_deg[i]:.2f}°).")
                continue # Skip conversion if raw is None

            try:
                # raw is an integer count of centi-degrees
                deg = float(raw) / 100.0
                new_current_joint_angles_deg[i] = deg # Update with the new, valid degree
            except (TypeError, ValueError) as e:
                # If conversion failed, new_current_joint_angles_deg[i] retains its existing value.
                print(f"[Lynx] Warning: Motor {m._id} returned invalid data '{raw}': {e}. Retaining previous valid angle ({new_current_joint_angles_deg[i]:.2f}°).")
                # No action needed - value already retained

        # Always update the internal state _current_joint_angles_deg with the best available data
        self._current_joint_angles_deg = new_current_joint_angles_deg

        # Return value for external functions (e.g., for debugging or other logic)
        # still signals which original reads failed by conforming to the expected [[pos], [None]] format.
        return [[p] if p is not None else [None] for p in pos_all_raw_from_motors]
    
    def move_abs(self, action): # 'action' here is a list of absolute target positions in degrees
        if self._in_emergency_state:
            print("[Lynx] In emergency state, ignoring move_abs() command.")
            return

        action = list(action)
        assert len(action) == len(self._motors)

        for idx, a in enumerate(action):
            # The low level protocol expects ints (centi-degrees)
            a_cd = int( a * 100) # Convert degrees to centi-degrees
            self._motors[idx].move_abs(a_cd)

    def move_abs_admin(self, action): # 'action' here is a list of absolute target positions in degrees
        # Skip the emergency state check for admin commands
        action = list(action)
        assert len(action) == len(self._motors)

        for idx, a in enumerate(action):
            # The low level protocol expects ints (centi-degrees)
            a_cd = int( a * 100) # Convert degrees to centi-degrees
            self._motors[idx].move_abs(a_cd)

    def move_abs_with_speed(self, action, speed): # 'action' here is a list of absolute target positions in degrees
        if self._in_emergency_state:
            print("[Lynx] In emergency state, ignoring move_abs() command.")
            return

        action = list(action)
        assert len(action) == len(self._motors)

        for idx, a in enumerate(action):
            # The low level protocol expects ints (centi-degrees)
            a_cd = int( a * 100) # Convert degrees to centi-degrees
            self._motors[idx].move_abs_with_speed(a_cd, speed)

    def limp(self):
        for m in self._motors:
            print(f'[Lynx] motor {m._id} limping')
            m.limp()

    def hold(self):
        for m in self._motors:
            print(f'[Lynx] motor {m._id} holding')
            m.hold()

    def limp_broadcast(self):
        print("[Lynx] Setting all motors to LIMP.")
        # This uses the broadcast ID #254, which is a good way
        # to override any specific motor commands. We'll create a broadcast motor object.
        broadcast_motor = motor.Motor(id=lssc.LSS_BroadcastID, bus=self._bus, bus_lock=self._bus_lock)
        broadcast_motor.limp()

    def hold_broadcast(self):
        print("[Lynx] Setting all motors to HOLD.")
        # This uses the broadcast ID #254, which is a good way
        # to override any specific motor commands. We'll create a broadcast motor object.
        broadcast_motor = motor.Motor(id=lssc.LSS_BroadcastID, bus=self._bus, bus_lock=self._bus_lock)
        broadcast_motor.hold()

    def enter_emergency_recovery(self):
        """Triggers the uninterruptible emergency recovery sequence."""
        # Prevent starting multiple recovery threads
        if self._in_emergency_state:
            return

        self._in_emergency_state = True
        # Run the recovery in a separate thread so it doesn't block anything
        self._emergency_thread = threading.Thread(target=self._emergency_recovery_task, daemon=True)
        self._emergency_thread.start()

    def _emergency_recovery_task(self):
        """The actual recovery sequence: HOLD, wait, then go home."""
        print("\n" + "=" * 40)
        print("! ! ! ROBOT ENTERING EMERGENCY RECOVERY ! ! !")

        # 1. HOLD all joints immediately
        print("[Emergency] Holding all joints...")

        self.hold_broadcast()
        self.hold_broadcast()
        self.hold_broadcast()
        self.hold_broadcast()
        self.hold_broadcast()
        self.hold()
        self.hold()
        self.hold()
        self.hold()
        self.hold()


        # 2. Wait for 3 seconds
        print("[Emergency] Holding position for 3 seconds...")
        time.sleep(3)

        # 3. Move slowly back to the predefined home position
        # We call the internal _move_and_wait method to ensure it's uninterruptible
        print(f"[Emergency] Moving to safe home position: {self.home_position}")
        self._move_and_wait_admin(self.home_position)

        print("[Emergency] Home position reached. Resuming normal operation.")
        print("=" * 40 + "\n")

        # 4. Cancel emergency mode
        self._in_emergency_state = False

    def _move_and_wait(self, target_position):
        """An internal move command that is not blocked by the emergency flag."""
        self.move_abs(target_position)

        # Wait until the position is reached
        while not self._is_at_target(target_position):
            time.sleep(0.2)  # Check every 200ms

    def _move_and_wait_admin(self, target_position, sim_steps_per_check=50):
        """An internal move command that is not blocked by the emergency flag, for admin use."""
        self.move_abs_admin(target_position)

        # Wait until the position is reached
        while not self._is_at_target(target_position):
            time.sleep(0.2)

    def _is_at_target(self, target_position, tolerance=2.0):
        """Checks if the robot is at the target position within a tolerance."""
        current_pos_list = self.get_Position()
        current_pos = [p[0] for p in current_pos_list if p[0] is not None]

        if len(current_pos) != len(target_position):
            return False  # Can't confirm if a joint position is unknown

        for i in range(len(target_position)):
            if abs(current_pos[i] - target_position[i]) > tolerance:
                return False  # At least one joint is not at its target

        return True  # All joints are within the tolerance of their target

    def shutdown(self):
        print("[Lynx] Shutting down...")

        # Stop the spatial watchdog if it exists
        if hasattr(self, 'safety_watchdog') and self.safety_watchdog:
            self.safety_watchdog.stop()

        # NEW: Stop the joint watchdog if it exists
        if hasattr(self, 'joint_watchdog') and self.joint_watchdog:
            self.joint_watchdog.stop()

        # NEW: Wait for emergency recovery to finish if it's active
        # This is critical to ensure the robot completes its safe state transition
        # before the serial bus is closed.
        if hasattr(self, '_emergency_thread') and self._emergency_thread and self._emergency_thread.is_alive():
            print("[Lynx] Waiting for active emergency recovery to complete before closing bus...")
            self._emergency_thread.join() # Wait for the thread to finish
            self._in_emergency_state = False # Ensure state is reset after recovery

        self.close_bus()
        print("[Lynx] Shutdown complete.")

