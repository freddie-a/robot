"""Controller interface for robot"""
import logging
import math
import time

import evdev
import trio

import robot_api

BUTTONS = {
    "triangle": 307,
    "square": 308,
    "x": 304,
    "circle": 305,
    "l2": 312,
    "r2": 313
}

MIN_MOVE_INTERVAL = 1 / 50 # 50 moves per sec

async def main():
    """Runs serial and controller read loop"""
    async with trio.open_nursery() as nursery:
        nursery.start_soon(robot_api.SERIAL_CONN.core_loop)
        nursery.start_soon(controller_read_loop)

async def controller_read_loop():
    """Controller analog stick read loop"""
    await trio.sleep(2)
    LOGGER.debug("Ready")
    robot_api.set_controller_mode(enabled=True)
    fileno = GAMEPAD.fileno()
    cur_x = 0
    cur_y = 0
    last_send = time.monotonic()
    while True:
        await trio.hazmat.wait_readable(fileno)
        event = GAMEPAD.read_one()
        # we're in business
        if event.type == 3:
            if event.code == 0:
                cur_x = event.value - 125
            elif event.code == 1:
                cur_y = (event.value - 125) * -1
            else:
                continue
            # rate limit commands to min_move_interval
            if time.monotonic() - MIN_MOVE_INTERVAL > last_send:
                print("send")
                last_send = time.monotonic()
                mag = math.sqrt(cur_x ** 2 + cur_y ** 2)
                # dead zone to prevent small movements from joystick drift
                if mag > 10:
                    # 1.84 comes from rt(2* 130**2) / 100
                    await robot_api.move(speed=mag / 1.84, vector=[cur_x, cur_y])
                else:
                    await robot_api.release_all()

LOGGER = logging.getLogger("controller_movement")


# DS4 on event2 with no other peripherals
# TODO implement event indentification / detection
GAMEPAD = evdev.InputDevice("/dev/input/event2")
if __name__ == "__main__":
    trio.run(main)
