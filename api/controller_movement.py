"""Controller interface for music"""
import time
import evdev
import serial

# Setting up serial connection to Arduino
PORT = "/dev/ttyACM0"
SERIAL_CONN = serial.Serial(PORT, 9600)
SERIAL_CONN.flushInput()
BUTTONS = {
    "triangle": 307,
    "square": 308,
    "x": 304,
    "circle": 305,
    "l2": 312,
    "r2": 313
}

def start():
    """Starts the controller button read loop"""
    for event in GAMEPAD.read_loop():
        # If buttons being pressed (gets rid of motion controls)
        if event.value == 1:
            print(event.code)
        # If triangle pressed, tell motors to go forwards until triangle is no longer held down
        if event.code == BUTTONS["triangle"]:
            while BUTTONS["triangle"] in GAMEPAD.active_keys():
                SERIAL_CONN.write(0)
                time.sleep(0.05)
        # If X pressed, tell motors to go backwards until X is no longer held down
        elif event.code == BUTTONS["x"]:
            while BUTTONS["x"] in GAMEPAD.active_keys():
                SERIAL_CONN.write(180)
                time.sleep(0.05)
        # If square pressed, tell motors to go left until square is no longer held down
        elif event.code == BUTTONS["square"]:
            while BUTTONS["square"] in GAMEPAD.active_keys():
                SERIAL_CONN.write(270)
                time.sleep(0.05)
        # If circle pressed, tell motors to go right until circle is no longer held down
        elif event.code == BUTTONS["square"]:
            while BUTTONS["square"] in GAMEPAD.active_keys():
                SERIAL_CONN.write(90)
                time.sleep(0.05)

#Setting up GAMEPAD as DS4 controller
GAMEPAD = evdev.InputDevice("/dev/input/event4")
if __name__ == "__main__":
    print("Initialising.")
    time.sleep(2)
    print("Ready")
    start()
