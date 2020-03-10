#!/usr/bin/env python3

# Feel free to take only what is needed, and please forgive the
# bugginess (It probably won't work) since I can't test this
# aspect.

import math       # For trigonometry (tan).
import random

# These are intended to be the arrays of motor settings needed
# for forwards and rightwards translation respectively.
# In order for motor_settings_from_rotation to work, the dtype
# must be capable of non-integer values between 0 and 1 - so I'm
# assuming a float of some size.


MOTOR_VALUES = { # TODO find true vals
    "fl": dict(forward=1, right=-1),
    "bl": dict(forward=1, right=1),
    "fr": dict(forward=1, right=1),
    "br": dict(forward=1, right=-1)
}

# These two need to be be in correct proportion to each other
# (i.e. the ratio forward_speed/right_speed is correct) but the
# exact magnitudes do not matter.
FORWARD_SPEED = 1.0
RIGHT_SPEED = 0.6 # TODO find real speed

def motor_settings_from_rotation(bearing):
    """Return an array of motor settings for translation at *angle*.

    There are a few underlying assumptions which may be misplaced
    - as such, this code may not work as expected.

    Parameters:
    - bearing
        - This is the desired bearing for translation, measured
        in degrees clockwise around the origin.
    """
    # We will work out the desired mix of *FORWARD* and *RIGHT* based
    # on the intersection of two lines.
    # First, we will determine the gradient and intercept of the first
    # line. This line is of the form y = mx + c and is used to
    # correctly interpolate between forwards and rightwards motion.

    # Initialise the variables.
    gradient = 0
    intercept = 0

    # Calculate angle in radians anticlockwise around the origin
    # with 0c to the right.
    # We could just rework the logic instead, but I've converted
    # since I'm not sure if we'll make future changes (depending on
    # what we get from the joystick input).
    angle = (90 - bearing) * (math.pi / 180)
    # Wrap angle around if greater than 360 degrees (2 pi).
    angle %= 2 * math.pi

    # Assign gradient and intercept their correct values.
    # You could probably split this out into two if-elses if
    # you wanted to; one for gradient and one for y-intercept.
    if 0 <= angle <= (math.pi / 2):
        # 0-90 degrees.
        gradient = -(FORWARD_SPEED / RIGHT_SPEED)
        intercept = FORWARD_SPEED
    elif (math.pi / 2) < angle <= math.pi:
        # 90-180 degrees.
        gradient = FORWARD_SPEED / RIGHT_SPEED
        intercept = FORWARD_SPEED
    elif math.pi < angle <= 3 * (math.pi / 2):
        # 180-270 degrees.
        gradient = -(FORWARD_SPEED / RIGHT_SPEED)
        intercept = -FORWARD_SPEED
    else:
        # Must be 270-360 degrees.
        gradient = FORWARD_SPEED / RIGHT_SPEED
        intercept = -FORWARD_SPEED

    # The second line is that of y = (tan(*angle*))*x.
    # Here, we solve the equations to find the coordinates
    # at which they intersect (inlining could be a good idea here).
    x_intersect_coord = intercept / (math.tan(angle)-gradient)
    y_intersect_coord = math.tan(angle) * x_intersect_coord
    # Assuming the magnitudes of forward_speed and
    # right_speed are accurate, the magnitude of the resultant
    # speed may be found by the formula (x_intersect_coord ** 2 + y_intersect_coord ** 2) ** 0.5
    x_multiplier = x_intersect_coord / RIGHT_SPEED
    y_multiplier = y_intersect_coord / FORWARD_SPEED
    # Set settings_arr.
    # settings_arr = y_multiplier * FORWARD
    # settings_arr += x_multiplier * RIGHT
    settings_arr = {}
    for motor, settings in MOTOR_VALUES.items():
        settings_arr[motor] = (
            y_multiplier * settings["forward"]
            + x_multiplier * settings["right"]
        )
    # At this point, settings_arr represents the motor settings
    # so as to achieve the maximum possible speed in the given
    # direction.

    # Maybe we should clip to protect against values > 1 or < -1?
    # This shouldn't be necessary though, if everything's gone to plan.
    # settings_arr = np.clip(settings_arr, -1, 1)

    return settings_arr

def motor_settings_from_vector(vector):
    """Return an array of motor settings for translation at *vector*.

    There are a few underlying assumptions which may be misplaced
    - as such, this code may not work as expected.

    Parameters:
    - vector
        - A list in format [x, y]. x-axis is to the right
        of the robot, and y-axis straight ahead.
    """
    right_multiplier = FORWARD_SPEED / RIGHT_SPEED
    # Ensure direction kept while all values kept <= 1.
    multiplier = abs(right_multiplier*vector[1]) + abs(vector[0])
    for i in range(2):
        vector[i] /= multiplier
    vector[1] *= right_multiplier
    # Fill dictionary.
    settings_arr = {}
    for motor, settings in MOTOR_VALUES.items():
        settings_arr[motor] = (
            vector[1] * settings["forward"]
            + vector[0] * settings["right"]
        )
    return settings_arr
