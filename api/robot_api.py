"""Robot API"""

import struct
import logging
import math
import random
# import timeit

import serial
import trio

import angle_translation

## Libraries

## Global variables / constants
PORT = "/dev/ttyACM0"
BAUD = 115200
SPEED_OF_SOUND = 340
ULTRASONIC_SENSORS = dict(
    front=0x01, # XXX placeholder
    back=0x02,
    left=0x04
)

MOTORS = {
    "fl": 0x00,
    "bl": 0x01,
    "fr": 0x02,
    "br": 0x03
}
MOTOR_ACTIONS = {
    "forward": 0x00,
    "backward": 0x04,
    # "brake": 0x08,
    "release": 0x0C
}
READ_SIZES = {
    0x10: 4 * 4,
    0x11: None, # XXX DYNAMIC
    0x12: 1
}
ERROR_CODES = {
    0xF0: "Unknown command",
    0xF1: "Illegal request in controller mode",
    0xF2: "Controller mode requested with pending sensor",
    0xF3: "Misaligned data during reset",
    0xF4: "Bad message ID recieved"
}

class AsyncSerialConnection:
    """Asynchronous serial connection"""
    def __init__(self, port, baud):
        # setup serial connection and flush
        self.conn = serial.Serial(port, baud)
        self.conn.reset_input_buffer()
        # set data write channels, and recieve channels dict
        self.write_channel_in, self.write_channel_out = trio.open_memory_channel(256)
        self.recv_channels = {}
        self.current_commands = [None] * 256
        self.current_seqn = 0

    async def core_loop(self):
        while True:
            # write any pending data to the connection
            try:
                while True:
                    self.conn.write(self.write_channel_out.receive_nowait())
            except trio.WouldBlock:
                # theres nothing inthe write channel
                pass
            # if data is ready to receive
            if self.conn.in_waiting:
                # recieve command and calculate expected size
                command = self.conn.read(1)
                data = None
                if command >= 0xF0:
                    error_str = self.log_error_code(command)
                    if command in (0xF1, 0xF2):
                        await self.recv_channels[self.conn.read(1)].send(Exception(error_str)) # TODO better exception class
                elif command not in READ_SIZES:
                    LOGGER.critical("Recieved unknown command ({0::02X})".format(command))
                elif command not in self.recv_channels:
                    LOGGER.critical("Recieved data not prepared to receive")
                else:
                    data = self.conn.read(READ_SIZES[command])
                    seqn = int(self.conn.read(1))
                    if self.current_commands[seqn][0] != command:
                        LOGGER.error("Seqn translates to wrong command")
                        await self.reset_connection()
                    else:
                        # send data the appropriate listener
                        await self.recv_channels[command].send(data)
                # an error has occured
                if data is None:
                    await self.reset_connection()
            # sleep some at the end of every read/write check
            await trio.sleep(0.02) # TODO const tune

    def remove_command(self, command):
        # iterate backwards through remove command from current position
        index = self.current_seqn
        while True:
            if self.current_commands[index] == command:
                self.current_commands[index] = None
                break
            index -= 1

    def log_error_code(self, error_code):
        """Logs error code recieved from arduino"""
        error_details = ERROR_CODES.get(error_code, "no error code entry")
        error_str = "Error code {0::02X} ({1})".format(error_code, error_details)
        LOGGER.error(error_str)
        return error_str

    def get_message_id(self):
        """Calculates next message id"""
        next_id = self.current_seqn
        self.current_seqn = (next_id + 1) % 2 ** 8
        return next_id

    async def reset_connection(self):
        LOGGER.info("Resetting connection")
        verify_byte = random.randint(0x01, 0xFE)
        self.conn.write(bytes(0xFF, 0xFF, 0xFF, verify_byte))
        while True:
            while self.conn.in_waiting:
                data = self.conn.read(1)
                if data == 0xFF:
                    if self.conn.read(1) != verify_byte:
                        LOGGER.warning("Recieved 0xFF with bad verify")
                        continue
                    last_valid_seqn = int(self.conn.read(1))
                    LOGGER.info("Recieved reset OK")
                    break
                if data == 0xF3:
                    LOGGER.warning("Recieved error code during reset")
                    self.log_error_code(data)
                    self.conn.write(bytes(0xFF, 0xFF, 0xFF))
            await trio.sleep(0.05)
        self.current_seqn = 0
        while last_valid_seqn != self.current_seqn:
            data = self.current_commands[last_valid_seqn]
            if data is not None:
                await self.write_data(data[0], data[1:], write_now=True)
            last_valid_seqn += 1
        LOGGER.info("Pending commands resent")

    async def read_data(self, command):
        # create read channels with no buffering
        read_channel_in, read_channel_out = trio.open_memory_channel(0)
        # add channels to self.recv_channels
        self.recv_channels[command] = read_channel_in
        # wait for response
        data = await read_channel_out.recieve()
        # remove command from current commands as it has finished
        self.remove_command(command)
        # close channels
        await self.recv_channels.pop(command).aclose()
        await read_channel_out.aclose()
        if isinstance(data, Exception):
            raise data
        return data

    async def write_data(self, command, data, write_now=False):
        command_data = bytes(command, data)
        message_id = self.get_message_id()
        self.current_commands[message_id] = command_data
        message_data = bytes(command_data, message_id)
        if write_now:
            self.conn.write(message_data)
        else:
            await self.write_channel_in.send()

    async def run_command(self, command, data):
        if command in self.recv_channels:
            raise Exception("Cannot queue multiple instances of same command")
        self.current_commands[command] = data
        await self.write_data(command, data)
        return await self.read_data(command)


async def get_distance(sensors):
    """Gets distance using specified ultrasonic sensors

    Returns infinity if nothing is detected"""
    # calculate expected read size
    READ_SIZES[0x11] = str(bin(sensors)).count("1")
    data = await SERIAL_CONN.run_command(0x11, sensors)
    # unpack recieved data in to integers
    micros = struct.unpack(data, "{0}i".format(READ_SIZES[0x11]))
    results = []
    for item in micros:
        # if value is -1, there was no response so set time to inf
        if item == -1:
            item = math.inf
        # else calculate travel time with speed of sound
        else:
            item = (item / 1e9 * SPEED_OF_SOUND) / 2
        results.append(item)
    if len(results) == 1:
        return results[0]
    return results


async def rotate_degrees():
    # TODO - work out calculations for motor speed
    pass

async def get_speed():
    data = await SERIAL_CONN.run_command(0x10, 0x00)
    # unpack recieved data in to integers
    speeds = struct.unpack(data, "4i")
    # TODO calc from wheel angles
    return speeds



async def move(direction=0, vector=None, distance=None, sensor=None, speed=100):
    """Move in *direction* until *sensor* reads *distance*.

    Either *direction* or *vector* can be provided; vector takes
    precedence if both are given.

    Parameters:
    - direction
        - Angle in degrees clockwise about robot, with
        0 degrees straight ahead.
    - vector
        - A list in format [x, y]. x-axis is to the right
        of the robot, and y-axis straight ahead.
    - distance
        - The distance reading at which the motion will stop.
        Units are ____. If distance == None, then the motion will
        continue forever until something else is called to change it.
    - sensor
        - The sensor to be used.
    - speed
        - The speed, in range 0-100, of motion.
    """
    speed = speed * 2.55 # convert speed 0-255
    # calculate motor values
    if vector is None:
        motor_matrix = angle_translation.motor_settings_from_rotation(direction)
    else:
        motor_matrix = angle_translation.motor_settings_from_vector(vector)
    motor_data = []
    # multiply values by speed and calculate motor mode
    for motor, value in motor_matrix.items():
        value = round(value * speed)
        if value == 0:
            motor_mode = MOTOR_ACTIONS["release"]
        elif value > 0:
            motor_mode = MOTOR_ACTIONS["forward"]
        else:
            motor_mode = MOTOR_ACTIONS["backward"]
        motor_mode += MOTORS[motor]
        motor_data.append((motor_mode, abs(value)))
    # send to arduino
    for pair in motor_data:
        await SERIAL_CONN.write_data(*pair)
    if distance is not None:
        # wait until current distance is smaller than target
        while await get_distance(sensor) > distance:
            await trio.sleep(0.1)
        await release_all()


async def release_all():
    for motor in MOTORS.values():
        await SERIAL_CONN.write_data(MOTOR_ACTIONS["release"] + motor, 0x00)

async def set_controller_mode(enabled=False):
    data = 0x01 if enabled else 0x00
    await SERIAL_CONN.run_command(0x12, data)


async def full_test():
    print("Waiting for 5s (link warmup)")
    await trio.sleep(5)
    print("Getting frontside ultrasonic distance")
    distance = await get_distance(ULTRASONIC_SENSORS["front"])
    if distance == math.inf:
        print("No response")
    else:
        print("Distance: {0}m".format(distance))
    print("Moving forward for 1s")
    await move(0, speed=20)
    await trio.sleep(1)
    await release_all()
    print("Setting motors to slow speed, forward until 0.2m on front sensor")
    await move(0, 0.2, ULTRASONIC_SENSORS["front"], speed=20)
    print("Setting motors high speed, left until 0.2m on left sensor")
    await move(270, 0.2, ULTRASONIC_SENSORS["left"], speed=70)


async def main():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(SERIAL_CONN.core_loop)
        nursery.start_soon(full_test)

SERIAL_CONN = AsyncSerialConnection(PORT, BAUD)
LOGGER = logging.getLogger("robot_api")

if __name__ == "__main__":
    trio.run(main)
