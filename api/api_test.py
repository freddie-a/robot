"""A collection of short tests for the API"""
import logging
import math
import time

import trio

import robot_api


async def movement_test():
    """Full movement test with ultrasonic bounds"""
    LOGGER.info("Getting frontside ultrasonic distance")
    distance = await robot_api.get_distance(robot_api.ULTRASONIC_SENSORS["front"])
    if distance == math.inf:
        LOGGER.info("No response")
    else:
        LOGGER.info("Distance: {0}m".format(distance))
    LOGGER.info("Moving forward for 1s")
    await robot_api.move(0, speed=20)
    await trio.sleep(1)
    await robot_api.release_all()
    LOGGER.info("Setting motors to slow speed, forward until 0.2m on front sensor")
    await robot_api.move(0, 0.2, robot_api.ULTRASONIC_SENSORS["front"], speed=20)
    LOGGER.info("Done")
    LOGGER.info("Setting motors high speed, left until 0.2m on left sensor")
    await robot_api.move(270, 0.2, robot_api.ULTRASONIC_SENSORS["left"], speed=70)
    LOGGER.info("Done")

async def movement_test2():
    """Sets robot to move forward infinitely"""
    await robot_api.move(0, speed=50)

async def movement_test3():
    """Takes an angle and speed and then moves according to them, asking for input"""
    while True:
        try:
            angle = float(input("Enter angle: "))
            speed = float(input("Enter speed: "))
            await robot_api.move(angle, speed=speed)
            await trio.sleep(0.5)
        except KeyboardInterrupt as e:
            print(e)
            await robot_api.release_all()
            await trio.sleep(0.5)


async def ultrasonic_test():
    """Continuously fetches ultrasonic sensor values (with timing)"""
    # start = time.time()
    while True:
        print(await robot_api.get_distance(0x01))
        # print(time.time() - start)
        # start = time.time()

async def speed_test():
    """Continuously fetches current robot speed"""
    while True:
        print(await robot_api.get_speed())
        await trio.sleep(0.1)

async def error_test():
    """Performs an error handling test with special 0xD0 testing command, then runs ultrasonic"""
    LOGGER.info("Starting error test")
    await robot_api.SERIAL_CONN.run_command(0xD0, 0x00)
    LOGGER.info("Error test done")
    await ultrasonic_test()

async def controller_mode_test():
    """Runs a controller mode based max move commands/sec test, then starts speed test"""
    await robot_api.set_controller_mode(True)
    # await robot_api.get_speed()
    with trio.move_on_after(5):
        while True:
            await robot_api.move(direction=0, speed=80)
             # about the maximum 125 sets/s  500 coms/s 1500B/s 12kbps 2.4% 500k baud
            await trio.sleep(0.008)
    await robot_api.set_controller_mode(False)
    await speed_test()

async def main():
    """Main function"""
    async with trio.open_nursery() as nursery:
        nursery.start_soon(robot_api.SERIAL_CONN.core_loop)
        nursery.start_soon(ultrasonic_test)

LOGGER = logging.getLogger("api_test")

if __name__ == "__main__":
    trio.run(main)
