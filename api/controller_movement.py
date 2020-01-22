"""Controller interface for robot"""
import logging

import evdev
import trio

import logging_setup
import robot_api

BUTTONS = {
    "triangle": 307,
    "square": 308,
    "x": 304,
    "circle": 305,
    "l2": 312,
    "r2": 313
}

async def main():
    """Runs serial and controller read loop"""
    with trio.open_nursery() as nursery:
        nursery.start_soon(robot_api.SERIAL_CONN.core_loop)
        nursery.start_soon(controller_read_loop)

async def controller_read_loop():
    """Controller button read loop"""
    await trio.sleep(2)
    LOGGER.debug("Ready")
    robot_api.set_controller_mode(enabled=True)
    for event in GAMEPAD.read_loop():
        # If buttons being pressed (gets rid of motion controls)
        if event.value == 1:
            print(event.code)
        # If triangle pressed, tell motors to go forwards until triangle is no longer held down
        if event.code == BUTTONS["triangle"]:
            await robot_api.move(0, speed=40)
            while BUTTONS["triangle"] in GAMEPAD.active_keys():
                await trio.sleep(0.05)
        # If X pressed, tell motors to go backwards until X is no longer held down
        elif event.code == BUTTONS["x"]:
            await robot_api.move(180, speed=40)
            while BUTTONS["x"] in GAMEPAD.active_keys():
                await trio.sleep(0.05)
        # If square pressed, tell motors to go left until square is no longer held down
        elif event.code == BUTTONS["square"]:
            await robot_api.move(270, speed=40)
            while BUTTONS["square"] in GAMEPAD.active_keys():
                await trio.sleep(0.05)
        # If circle pressed, tell motors to go right until circle is no longer held down
        elif event.code == BUTTONS["square"]:
            await robot_api.move(90, speed=40)
            while BUTTONS["square"] in GAMEPAD.active_keys():
                await trio.sleep(0.05)
        else:
            await robot_api.release_all()
            await trio.sleep(0.05)

logging_setup.add_handlers()
LOGGER = logging.getLogger("controller_movement")


#Setting up GAMEPAD as DS4 controller
GAMEPAD = evdev.InputDevice("/dev/input/event4")
if __name__ == "__main__":
    trio.run(main)
