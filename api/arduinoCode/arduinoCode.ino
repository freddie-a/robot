#include <ArduinoSTL.h>
#include <array>
#include <vector>

#include <Adafruit_MotorShield.h>
#include <NewPing.h>

// constants
#define PIN_A_INDEX 0
#define PIN_A_BITMASK_INDEX 1
#define PIN_B_INDEX 2
#define PIN_B_BITMASK_INDEX 3
#define LAST_STATE_INDEX 4

#define CURRENT_TICKS_INDEX 0
#define SHOW_TICKS_INDEX 1

#define PIN_A_REGISTER_INDEX 0
#define PIN_B_REGISTER_INDEX 1


#define MAX_PING_DISTANCE_CM 100
#define PING_INTERVAL_MS 35
#define DEFAULT_MOTOR_SPEED 0xC8
#define SPEED_INTERVAL 100000 // in uS


#define MOTOR_SPEEDS_QUERY 0x10
#define ULTRASONIC_QUERY 0x11
#define SET_CONTROLLER_MODE 0x12


#define UNKNOWN_COMMAND 0xF0
#define ILLEGAL_REQUEST_IN_CONTROLLER_MODE 0xF1
#define CONTROLLER_MODE_REQUEST_WITH_PENDING_ULTRASONIC 0xF2
#define ULTRASONIC_ALREADY_PENDING 0xF3
#define MISALIGN_DURING_RESET 0xF4
#define BAD_MESSAGE_ID 0xF5
#define SERIAL_RESET 0xFF
#define SERIAL_INIT 0xFE // previously 0x41

#define SERIAL_DEBUG false


// array of ultrasonic sensors
std::vector<NewPing> ultrasonic_sensors = {{
    // trigger pin, echo pin , max_distance
    {24, 25, MAX_PING_DISTANCE_CM},
    {26, 27, MAX_PING_DISTANCE_CM},
    {28, 29, MAX_PING_DISTANCE_CM}
}};

// array of motors
std::array<Adafruit_DCMotor*, 4> motors;


// motor feedback, which allows motor speeds to be measured
std::array<std::array<uint8_t, 5>, 4> motor_feedback = {{
    // 4 motors
    // 5 data
    // pin_a, pin_a bitmask
    // pin_b, pin_b bitmask
    // last_state
    {30, 0, 31, 0, 0},
    {32, 0, 33, 0, 0},
    {34, 0, 35, 0, 0},
    {36, 0, 37, 0, 0}
}};

// current motor speeds in ticks per time div, updated every time div, where time div is speed_interval (see below)
std::array<std::array<int, 2>, 4> motor_speeds = {{
    // current ticks, show ticks
    {0, 0},
    {0, 0},
    {0, 0},
    {0, 0}
}};
// motor feedback pin addresses
std::array<std::array<volatile uint8_t*, 2>, 4> motor_feedback_pins;

// results of ultrasonic pings in uS, where -1 is no echo (ie nothing found in range)
std::array<long, 4> ping_results = {{-1, -1, -1}};

Adafruit_MotorShield motor_shield = Adafruit_MotorShield();

// serial instruction
uint8_t instruction;
// data associated with instruction
uint8_t instruction_data;
// data sequence number
uint8_t seqn;
// last seen sequence number
uint8_t last_seqn = -1;

// index for counted for loops
uint8_t index;

// ultrasonic reads requested from serial
uint8_t requested_ultrasonic_reads = 0;
// current sensor in use
uint8_t current_sensor;
// whether ping has finished
bool all_pings_finished = true;
// result of ping (in uS)
unsigned long ping_result;
// next ping time
unsigned long next_ping_time;
// time taken between last motor read and current time
unsigned long time_taken;

bool pin_a_state;
bool pin_b_state;

// next time motor speed should be calculated in uS
unsigned long next_motor_read_time;

// whether the robot is using controller inputs
bool controller_mode = false;

// alignment data for resetting when an error occurs
char error_align_data[] = "RESET";

// verification byte for checking the reset worked
uint8_t verify_byte;

bool reset_once = false; // XXX remove


// setup serial connection and motor speeds
void setup() {
    Serial.begin(500000);
    Serial.setTimeout(0xFFFFFFFF);
    // wait for serial connection
    while (!Serial);
    // wait for init byte
    while (true) {
        if (Serial.read() == SERIAL_INIT) {
            break;
        }
        Serial.write(SERIAL_INIT);
        delay(100);
    }
    motor_shield.begin();
    index = 1;
    for(auto&& motor : motors) {
        motor = motor_shield.getMotor(index);
        index++;
    }
    // Serial.write(SERIAL_SUCCESS);
    index = 0;
    for(auto&& motor : motor_feedback) {
        // calculate pin a bitmask
        motor[PIN_A_BITMASK_INDEX] = digitalPinToBitMask(motor[PIN_A_INDEX]);
        // get pointer to register for pin a
        motor_feedback_pins[index][PIN_A_REGISTER_INDEX] = portInputRegister(digitalPinToPort(motor[PIN_A_INDEX]));
        // same stuff for pin b
        motor[PIN_B_BITMASK_INDEX] = digitalPinToBitMask(motor[PIN_B_INDEX]);
        motor_feedback_pins[index][PIN_B_REGISTER_INDEX] = portInputRegister(digitalPinToPort(motor[PIN_B_INDEX]));
        if (*motor_feedback_pins[index][PIN_A_REGISTER_INDEX] & motor[PIN_A_BITMASK_INDEX]) {
            motor[LAST_STATE_INDEX] = 1;
        }
        index++;
    }
    
    for(auto&& motor : motors) {
        // set motor speed to default
        motor->setSpeed(DEFAULT_MOTOR_SPEED);
        // stop motor
        motor->run(RELEASE);
    }
    // set last motor read time
    next_motor_read_time = micros() + SPEED_INTERVAL;
}

// checks for recieved ultrasonic pulses every 24 uS (eq 0.82cm @ 340ms-1)
void check_echo() {
    // if a response was recieved
    if (ultrasonic_sensors[current_sensor].check_timer()) {
        // set result in ping_results
        ping_result = ultrasonic_sensors[current_sensor].ping_result;
        ping_results[current_sensor] = ping_result;
    }
}

void serial_debug(uint8_t code) {
#if SERIAL_DEBUG
    Serial.write(0xC0);
    Serial.write(code);
#endif
}

void serial_error(uint8_t error, uint8_t data = 0) {
    Serial.write(error);
    Serial.write(data);
}

bool advance_sensor() {
    serial_debug(2);
    // for 8 possible sensors
    if (current_sensor > 0) {
        for (uint8_t i = current_sensor - 1; i >= 0; i--) {
            serial_debug(i);
            // if a read is pending for it, set as current sensor
            if (requested_ultrasonic_reads & (1 << i)) {
                current_sensor = i;
                // start ping timer interrupt
                serial_debug(10);
                ultrasonic_sensors[i].ping_timer(check_echo);
                next_ping_time = millis() + PING_INTERVAL_MS;
                return true;
            }
        }
    }
    // if we havent returned, there are no pings left; ret false
    return false;
}
void error_recovery(bool flag) {
    if (flag) {
        Serial.find(error_align_data); // change to error_align_data
    }
    while (!Serial.available());
    verify_byte = Serial.read();
    if (!all_pings_finished) {
        delay(PING_INTERVAL_MS); // ensure that any pings have finished
    }
    requested_ultrasonic_reads = 0;
    for (auto &&speeds : motor_speeds) {
        speeds.fill(0);
    }
    ping_results.fill(-1);
    next_motor_read_time = micros() + SPEED_INTERVAL;
    Serial.write(SERIAL_RESET);
    Serial.write(verify_byte);
    Serial.write(last_seqn);
    last_seqn = -1;
}

void loop() {
    // if 3 or more bytes of data available, each instruction is 2 bytes + seqn (except for reset which has 4th verify byte)
    if (Serial.available() >= 3) {
        instruction = Serial.read();
        instruction_data = Serial.read();
        seqn = Serial.read();
        if (instruction == SERIAL_RESET) {
            if (instruction_data != 0xFF || seqn != 0xFF) {
                serial_error(MISALIGN_DURING_RESET);
                error_recovery(true);
            } else {
                error_recovery(false);
            }
        } else if ((uint8_t)(seqn - 1) != last_seqn) {
            serial_error(BAD_MESSAGE_ID, last_seqn);
            error_recovery(true);
        } else {
            last_seqn = seqn;
            if (instruction <= 0x0F) {
                // set motor between 0x00 and 0x0F 
                uint8_t motor_id = instruction % 4;
                uint8_t mode = (instruction / 4) + 1;
                motors[motor_id]->setSpeed(instruction_data);
                motors[motor_id]->run(mode);
            // speeds / ultrasonic (shared error handling)
            } else if (instruction == MOTOR_SPEEDS_QUERY || instruction == ULTRASONIC_QUERY) {
                // return error if speed or ultrasonic requested when controller mode enabled
                if (controller_mode) {
                    serial_error(ILLEGAL_REQUEST_IN_CONTROLLER_MODE, instruction);
                    error_recovery(true);
                // speeds
                } else if (instruction == MOTOR_SPEEDS_QUERY) {
                        // write response instruction code
                        Serial.write(MOTOR_SPEEDS_QUERY);
                        // write integers, longs = 32 bits / 4 bytes
                        for(auto&& speed : motor_speeds) {
                            // cast to 4 long buffer and write
                            Serial.write((char *) &speed[SHOW_TICKS_INDEX], 2);
                        }
                // must be ultrasonic
                } else {
                    // set pending and requested reads, and the current sensor

                    // this should be an impossible state
                    if (!all_pings_finished) {
                        Serial.write(ULTRASONIC_ALREADY_PENDING);
                    } else {
                        all_pings_finished = false;
                        current_sensor = 9;
                        requested_ultrasonic_reads = instruction_data;
                        ping_results.fill(-1);
                        serial_debug(1);
                        advance_sensor();
                    }
                }
            // switch controller mode
            } else if (instruction == SET_CONTROLLER_MODE) {
                // if there are ultrasonic reads pending send error and reset
                // use requested rather than pending due to interrupt
                if (!all_pings_finished) {
                    serial_error(CONTROLLER_MODE_REQUEST_WITH_PENDING_ULTRASONIC, instruction);
                    error_recovery(true);
                } else {
                    controller_mode = instruction_data;
                    Serial.write(instruction);
                    Serial.write((uint8_t)0x00);
                }
            } else {
                // unknown command, error
                serial_error(UNKNOWN_COMMAND, instruction);
                error_recovery(true);
            }
        }
    }
    // only calculate speeds / check ultrasonic when not using a controller
    if (!controller_mode) {
        index = 0;
        for (auto &&motor : motor_speeds) {
            pin_a_state = *motor_feedback_pins[index][PIN_A_REGISTER_INDEX] & motor_feedback[index][PIN_A_BITMASK_INDEX];
            pin_b_state = *motor_feedback_pins[index][PIN_B_REGISTER_INDEX] & motor_feedback[index][PIN_B_BITMASK_INDEX];
            if (pin_a_state != motor_feedback[index][LAST_STATE_INDEX]) {
                // if pin a and b are the same, motor rotating forward
                if (pin_a_state == pin_b_state) {
                    motor[CURRENT_TICKS_INDEX]++;
                } else {
                    motor[CURRENT_TICKS_INDEX]--;
                }
                motor_feedback[index][LAST_STATE_INDEX] = pin_a_state;
            }
            index++;
        }
        // calculate time since last motor speed update
        // if above threshold, update
        if (micros() > next_motor_read_time) {
            time_taken = micros() - next_motor_read_time + SPEED_INTERVAL;
            for (auto&& speed : motor_speeds) {
                // speed in ticks per second
                speed[SHOW_TICKS_INDEX] = speed[CURRENT_TICKS_INDEX] / (time_taken / SPEED_INTERVAL);
                // reset ticks to 0 after reading
                speed[CURRENT_TICKS_INDEX] = 0;
            }
            // set last read time to current time
            next_motor_read_time = micros() + SPEED_INTERVAL;
        }
        if (!all_pings_finished && millis() > next_ping_time) {
            if (!advance_sensor()) {
                all_pings_finished = true;
                serial_debug(13);
                Serial.write(ULTRASONIC_QUERY);
                for (uint8_t i = 0; i <= 8; i++) {
                    // if the sensor was requested, write its data
                    if (requested_ultrasonic_reads & (1 << i)) {
                        Serial.write((char *) &ping_results[i], 4);
                    }
                }
            }
        }
    }
}
