# motor.py

import re
import serial

import motor_cmd as lssc


class Motor:
    def __init__(self, id = 0, bus =None, bus_lock = None):
        self._id = id
        self._serial_bus = bus
        self._bus_lock = bus_lock  # Placeholder for bus lock if needed in future

    def genericWrite(self, cmd, param = None):
        with self._bus_lock:
            if self._serial_bus is None:
                return False
            if param is None:
                self._serial_bus.write((lssc.LSS_CommandStart + str(self._id) + cmd + lssc.LSS_CommandEnd).encode())
            else:
                self._serial_bus.write((lssc.LSS_CommandStart + str(self._id) + cmd + str(param) + lssc.LSS_CommandEnd).encode())
            return True

    def genericRead_Blocking_int(self, cmd):
        if self._serial_bus is None:
            print(f"[Lynx] Error: Motor {self._id}: Serial bus is not initialized for read command '{cmd}'.")
            return None
        with self._bus_lock:
            try:
                # Get start of packet and discard header and everything before
                c = self._serial_bus.read()
                while (c.decode("utf-8") != lssc.LSS_CommandReplyStart):
                    c = self._serial_bus.read()
                    if (c.decode("utf-8") == ""):
                        # This indicates a timeout or end of stream before the start character
                        print(
                            f"[Lynx] Error: Motor {self._id}: Timeout or no data received before LSS reply start for command '{cmd}'.")
                        return (None)

                # Get packet
                # Use a higher timeout for read_until if expected response is long or network is slow
                data = self._serial_bus.read_until(lssc.LSS_CommandEnd.encode('utf-8'))

                # Parse packet
                # Ensure data is not empty after read_until
                if not data:
                    print(f"[Lynx] Error: Motor {self._id}: No data received for command '{cmd}'. Possibly a timeout.")
                    return None

                decoded_data = data.decode("utf-8")
                matches = re.match("(\d{1,3})([A-Z]{1,4})(-?\d{1,18})", decoded_data, re.I)

                # Check if matches are found
                if (matches is None):
                    print(
                        f"[Lynx] Error: Motor {self._id}: Received data '{decoded_data.strip()}' did not match expected LSS packet format for command '{cmd}'.")
                    return (None)

                # Check if all groups were captured (defensive check)
                if ((matches.group(1) is None) or (matches.group(2) is None) or (matches.group(3) is None)):
                    print(
                        f"[Lynx] Error: Motor {self._id}: Malformed LSS packet received for command '{cmd}'. Missing ID, identifier, or value in '{decoded_data.strip()}'.")
                    return (None)

                # Get values from match
                readID = matches.group(1)
                readIdent = matches.group(2)
                readValue = matches.group(3)

                # Check id
                if (readID != str(self._id)):
                    print(
                        f"[Lynx] Error: Motor {self._id}: Received packet for wrong motor ID (expected {self._id}, got {readID}) for command '{cmd}'.")
                    return (None)

                # Check identifier
                if (readIdent != cmd):
                    print(
                        f"[Lynx] Error: Motor {self._id}: Received packet for wrong command identifier (expected '{cmd}', got '{readIdent}') in '{decoded_data.strip()}'.")
                    return (None)

            except serial.SerialTimeoutException:
                print(f"[Lynx] Error: Motor {self._id}: Serial read timed out for command '{cmd}'. No response from motor.")
                return (None)
            except UnicodeDecodeError as ude:
                print(
                    f"[Lynx] Error: Motor {self._id}: Failed to decode serial data for command '{cmd}'. Received non-UTF-8 characters: {ude}")
                return (None)
            except serial.SerialException as se:
                print(f"[Lynx] Error: Motor {self._id}: Serial communication error during read for command '{cmd}': {se}")
                return (None)
            except Exception as e:
                # Catch any other unexpected errors during the process
                print(
                    f"[Lynx] Error: Motor {self._id}: An unexpected error occurred while processing read for command '{cmd}': {e}")
                return (None)

            # return value
            try:
                return int(readValue)
            except ValueError:
                print(
                    f"[Lynx] Error: Motor {self._id}: Received value '{readValue}' for command '{cmd}' is not a valid integer.")
                return (None)

    def genericRead_Blocking_int_legacy(self, cmd):
        if self._serial_bus is None:
            return None
        try:
            # Get start of packet and discard header and everything before
            c = self._serial_bus.read()
            while (c.decode("utf-8") != lssc.LSS_CommandReplyStart):
                c = self._serial_bus.read()
                if(c.decode("utf-8") == ""):
                    break
            # Get packet
            data = self._serial_bus.read_until(lssc.LSS_CommandEnd.encode('utf-8')) #Otherwise (without ".encode('utf-8')") the received LSS_CommandEnd is not recognized by read_until, making it wait until timeout.
            # Parse packet
            matches = re.match("(\d{1,3})([A-Z]{1,4})(-?\d{1,18})", data.decode("utf-8"), re.I)
            # print(data.decode("utf-8"))
            # Check if matches are found
            if(matches is None):
                print("1")
                return(None)
            if((matches.group(1) is None) or (matches.group(2) is None) or (matches.group(3) is None)):
                print("2")
                return(None)
            # Get values from match
            readID = matches.group(1)
            readIdent = matches.group(2)
            readValue = matches.group(3)
            # Check id
            if(readID != str(self._id)):
                print("3")
                return(None)
            # Check identifier
            if(readIdent != cmd):
                print("4")
                return(None)
        except:
            return(None)
        # return value
        return int(readValue)
    
    def genericRead_Blocking_str(self, cmd, numChars):
        if self._serial_bus is None:
            return None
        try:
            # Get start of packet and discard header and everything before
            c = self._serial_bus.read()
            while (c.decode("utf-8") != lssc.LSS_CommandReplyStart):
                c = self._serial_bus.read()
                if(c.decode("utf-8") == ""):
                    break
            # Get packet
            data = self._serial_bus.read_until(lssc.LSS_CommandEnd.encode('utf-8')) #Otherwise (without ".encode('utf-8')") the received LSS_CommandEnd is not recognized by read_until, making it wait until timeout.
            data = (data[:-1])
            # Parse packet
            matches = re.match("(\d{1,3})([A-Z]{1,4})(.{" + str(numChars) + "})", data.decode("utf-8"), re.I)
            # Check if matches are found
            if(matches is None):
                return(None)
            if((matches.group(1) is None) or (matches.group(2) is None) or (matches.group(3) is None)):
                return(None)
            # Get values from match
            readID = matches.group(1)
            readIdent = matches.group(2)
            readValue = matches.group(3)
            # Check id
            if(readID != str(id)):
                return(None)
            # Check identifier
            if(readIdent != cmd):
                return(None)
        except:
            return(None)
        # return value
        return(readValue)
    
    # Soft reset - revert all commands stored in EEPROM
    # If used, motor will be busy for a short moment while resetting
    def reset(self):
        return (self.genericWrite(lssc.LSS_ActionReset))
    

    ### ACTIONS ###

    # This action causes the servo to go "limp". The microcontroller will still be powered, 
    # but the motor will not. As an emergency safety feature, 
    # should the robot not be doing what it is supposed to or risks damage, use the 
    # broadcast ID to set all servos limp #254L<cr>.
    def limp(self):
        return (self.genericWrite(lssc.LSS_ActionLimp))
    
    # def emergency_stop(self):
    #     return (self.genericWrite(254, lssc.LSS_ActionLimp))
    
    # This command causes the servo to stop immediately and hold that angular position.
    def hold(self):
        return (self.genericWrite(lssc.LSS_ActionHold))
    
    # Move to position in degrees!
    def move_abs(self, pos):
        return (self.genericWrite(lssc.LSS_ActionMove, pos))
    
    def move_abs_with_speed(self, pos, speed):
        with self._bus_lock:
            if self._serial_bus is None:
                return False
            
            self._serial_bus.write((lssc.LSS_CommandStart + 
                                    str(self._id) + 
                                    lssc.LSS_ActionMove + 
                                    str(pos) + 
                                    lssc.LSS_ActionMaxSpeed + 
                                    str(speed) +
                                    lssc.LSS_CommandEnd).encode())
            return True
    
    # Move relative position in degrees
    def moveRelative(self, delta):
        return (self.genericWrite(lssc.LSS_ActionMoveRelative, delta))
    

    ### Status COmmands ###
    def getPosition(self):
        self.genericWrite(lssc.LSS_QueryPosition)
        return (self.genericRead_Blocking_int(lssc.LSS_QueryPosition))