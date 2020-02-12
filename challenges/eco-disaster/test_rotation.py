"""
Goal: To test the rotation of the robot, as well as the ability
to detect blocks.

Date: 12.2.20.
"""

import collections
import math
import trio

import fetch_blocks
import robot_api

async def main():
    """Run the test."""
    async with trio.open_nursery() as nursery:
        nursery.start_soon(robot_api.SERIAL_CONN.core_loop)
        nursery.start_soon(control_loop)

async def control_loop():
    """Run the test."""
    fetcher = fetch_blocks.BlockFetcher()
    queue = collections.deque(maxlen=15)
    while True:
        blocks = fetcher.fetch_blocks(
            colours=[fetcher.COLOUR_SIGNATURES["red"],]
        )[0]
        largest = fetcher.find_largest_block(blocks)
        position = largest[:2]      # In format [x, y].
        queue.append(position)
        length = len(queue)
        if length> 10:
            queue.popleft()
        average_x = 0
        for item in queue:
            average_x += item[0]
        average_x /= length
        if average_x > 180:
            # Rotate to the right.
            await robot_api.rotate(angle=math.inf)
        elif average_x < 140:
            # Rotate to the left.
            await robot_api.rotate(angle=-math.inf)
        else:
            # Stop rotating.
            await robot_api.release_all()
        await trio.sleep(0.05)

if __name__ == "__main__":
    trio.run(main)