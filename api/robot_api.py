"""Robot API"""

import logging
import math
import random
import struct
import time

import serial
import trio

import angle_translation
import logging_setup



## Constants
PORT = "/dev/ttyACM0"
BAUD = 500000 # previously 115200
SPEED_OF_SOUND = 340
ULTRASONIC_SENSORS = dict(
    front=0x01, # XXX placeholder values
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
    # "brake": 0x08, # brake is defined as a constant but not implemented in the adafruit library
    "release": 0x0C
}
READ_SIZES = {
    0x10: 4 * 2,
    0x11: None, # XXX dynamic read size
    0x12: 1,
    0xD0: 1, # XXX remove, error testing
    0xC0: 1 # XXX debug code
}
ERROR_CODES = {
    0xF0: "Unknown command",
    0xF1: "Illegal request in controller mode",
    0xF2: "Controller mode requested with pending sensor",
    0xF3: "Ultrasonic request already pending",
    0xF4: "Misaligned data during reset",
    0xF5: "Bad message ID recieved"
}
SERIAL_INIT = 0xFE # ord("A") # 0x41
# SERIAL_SUCCESS = 0x42

class AsyncSerialConnection:
    """Asynchronous serial connection"""
    def __init__(self, port, baud):
        # setup serial connection and flush
        self.conn = serial.Serial(port, baud)
        # set data write channels, and recieve channels dict
        self.write_channel_in, self.write_channel_out = trio.open_memory_channel(256)
        self.recv_channels = {}
        self.current_commands = [None] * 256
        self.current_seqn = 0
        self.serial_connect()

    def serial_connect(self):
        """Connect to arduino over serial"""
        LOGGER.info("Connecting to arduino")
        while True:
            data = self.conn.read()[0]
            print(data)
            if data == SERIAL_INIT:
                self.conn.write(bytes([SERIAL_INIT]))
                time.sleep(0.2)
                self.conn.reset_input_buffer()
                break
        LOGGER.info("Connected successfully")

    async def core_loop(self):
        """Async core read / write loop"""
        # TODO wrap socket as async
        while True:
            # write any pending data to the connection
            try:
                while True:
                    self.debug_write(
                        self.append_message_id(self.write_channel_out.receive_nowait())
                    )
            except trio.WouldBlock:
                # theres nothing inthe write channel
                pass
            # if data is ready to receive
            if self.conn.in_waiting:
                # recieve command and calculate expected size
                command = self.conn.read()[0]
                # print(command)
                data = None
                if command >= 0xF0:
                    # receive the error data byte
                    error_data = self.conn.read()[0]
                    error_str = self.log_error_code(command, error_data)
                    # propagate an exception if possible, only 0xF1 and F2 should be user error
                    if command in (0xF1, 0xF2):
                        # TODO better exception class
                        await self.recv_channels[error_data].send(Exception(error_str))
                elif command == 0xC0:
                    data = self.conn.read(1)[0]
                    LOGGER.info("Debug state {0}".format(data))
                elif command not in READ_SIZES:
                    LOGGER.critical("Recieved unknown command ({0:02X})".format(command))
                elif command not in self.recv_channels:
                    LOGGER.critical("Recieved data not prepared to receive")
                else:
                    data = self.conn.read(READ_SIZES[command])
                    # send data the appropriate listener
                    await self.recv_channels[command].send(data)
                # if nothing sets data, an error has occured
                if data is None:
                    await self.reset_connection()
            # sleep some at the end of every read/write check
            await trio.sleep(0.02) # TODO const tune

    def remove_command(self, command):
        """Remove a command from the current command array"""
        # iterate backwards through remove command from current position
        index = self.current_seqn - 1
        # print(self.current_commands, self.current_seqn, command)
        while True:
            if self.current_commands[index][0] == command:
                self.current_commands[index] = None
                break
            index -= 1

    def log_error_code(self, error_code, error_data):
        """Logs error code recieved from arduino"""
        error_details = ERROR_CODES.get(error_code, "no error code entry")
        error_str = ("Error code {0:02X} with data {1:02X} ({2})"
                     .format(error_code, error_data, error_details))
        LOGGER.error(error_str)
        return error_str

    def get_message_id(self):
        """Calculates next message id"""
        next_id = self.current_seqn
        self.current_seqn = (next_id + 1) % 2 ** 8
        return next_id

    async def reset_connection(self):
        """Reset serial connection"""
        # TODO handle an arduino reset during conn reset
        # TODO add option to manually reset
        LOGGER.info("Resetting connection")
        verify_byte = random.randint(0x01, 0xFE)
        LOGGER.info("Sending reset confirmation data")
        self.conn.write(bytes("RESET", "ascii"))
        self.conn.write(bytes([verify_byte]))
        reset_ok = False
        while not reset_ok:
            while self.conn.in_waiting:
                data = self.conn.read()[0]
                if data == 0xFF:
                    verify_challenge = self.conn.read()[0]
                    if verify_challenge != verify_byte:
                        LOGGER.warning("Recieved 0xFF with bad verify {0} {1}"
                                       .format(verify_byte, verify_challenge))
                        continue
                    last_valid_seqn = self.conn.read()[0]
                    LOGGER.info("Recieved reset OK")
                    reset_ok = True
                    break
                # data misalign
                if data == 0xF3:
                    LOGGER.warning("Recieved misalign during reset")
                    self.log_error_code(data, self.conn.read()[0])
                    self.conn.write(bytes("RESET", "ascii"))
                    self.conn.write(bytes([verify_byte]))
                else:
                    LOGGER.debug("Recieved garbage during reset {0}".format(data))
            await trio.sleep(0.05)

        last_sent_seqn = self.current_seqn
        self.current_seqn = 0
        while last_valid_seqn != last_sent_seqn:
            data = self.current_commands[last_valid_seqn]
            if data is not None:
                await self.write_data(data[0], data[1], write_now=True)
            last_valid_seqn = (last_valid_seqn + 1) % 2 ** 8
        # self.current_commands = [None] * 256
        LOGGER.info("Pending commands resent")

    async def read_data(self, command):
        """Reads the reponse to a command"""
        # create read channels with no buffering
        read_channel_in, read_channel_out = trio.open_memory_channel(0)
        # add channels to self.recv_channels
        self.recv_channels[command] = read_channel_in
        # wait for response
        data = await read_channel_out.receive()
        # remove command from current commands as it has finished
        self.remove_command(command)
        # close channels
        await self.recv_channels.pop(command).aclose()
        await read_channel_out.aclose()
        if isinstance(data, Exception):
            raise data
        return data

    def debug_write(self, data):
        """Prints data being sent to the arduino"""
        print(*data)
        self.conn.write(data)

    async def write_data(self, command, data, write_now=False):
        """Writes commands to the serial connection"""
        command_data = bytes([command, data])
        if write_now:
            print("d", end="")
            self.debug_write(self.append_message_id(command_data))
        else:
            await self.write_channel_in.send(command_data)

    def append_message_id(self, buf):
        """Appends message id to data being sent"""
        message_id = self.get_message_id()
        self.current_commands[message_id] = buf
        return buf + bytes([message_id])


    async def run_command(self, command, data):
        """Runs a command with data"""
        if command in self.recv_channels:
            raise Exception("Cannot queue multiple instances of same command")
        # self.current_commands[command] = data
        await self.write_data(command, data)
        return await self.read_data(command)


async def get_distance(sensors):
    """Gets distance using specified ultrasonic sensors

    Returns infinity if nothing is detected"""
    # calculate expected read size
    READ_SIZES[0x11] = str(bin(sensors)).count("1") * 4
    data = await SERIAL_CONN.run_command(0x11, sensors)
    # unpack recieved data in to integers
    micros = struct.unpack("{0}i".format(READ_SIZES[0x11] // 4), data)
    results = []
    for item in micros:
        # if value is -1, there was no response so set time to inf
        if item == -1:
            item = math.inf
        # else calculate travel time with speed of sound
        else:
            item = (item / 1e6 * SPEED_OF_SOUND) / 2
        results.append(item)
    if len(results) == 1:
        return results[0]
    return results


async def rotate_degrees(angle):
    # TODO - work out calculations for motor speed
    raise NotImplementedError("Rotation by x degrees not yet implemented")

async def get_speed():
    data = await SERIAL_CONN.run_command(0x10, 0x00)
    # unpack recieved data in to integers
    speeds = struct.unpack("4h", data)
    # TODO calc from wheel angles
    return speeds



async def move(direction=0, distance=None, sensor=None, speed=100, vector=None):
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
        Units are m. If distance is None, then the motion will
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
    print(motor_matrix)
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
            pass
        await release_all()


async def release_all():
    """Stops all motors"""
    for motor in MOTORS.values():
        await SERIAL_CONN.write_data(MOTOR_ACTIONS["release"] + motor, 0x00)

async def set_controller_mode(enabled=False):
    """Sets controller mode"""
    await SERIAL_CONN.run_command(0x12, int(enabled))


logging_setup.add_handlers()
LOGGER = logging.getLogger("robot_api")
SERIAL_CONN = AsyncSerialConnection(PORT, BAUD)
