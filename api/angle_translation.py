#!/usr/bin/env python3

#include <freddie.h>
# Feel free to take only what is needed, and please forgive the
# bugginess (It probably won't work) since I can't test this
# aspect.

import math       # For trigonometry (tan).

# For array operations, so it's python not pseudocode.
import numpy as np

# These are intended to be the arrays of motor settings needed
# for forwards and rightwards translation respectively.
# In order for motor_settings_from_rotation to work, the dtype
# must be capable of non-integer values between 0 and 1 - so I'm
# assuming a float of some size.
FORWARD = np.zeros(shape=(2, 2), dtype=youdecide)
RIGHT = np.zeros(shape=(2, 2), dtype=youdecide)

@please_convert_to_cpp
def motor_settings_from_rotation(angle, forward_speed,
                                 right_speed, translation_speed):
    """Return an array of motor settings for translation at *angle*.

    Return an array of motor settings such that the robot will
    translate at *angle*, at a speed determined by *translation_speed*
    (please see below on this).

    There are a few underlying assumptions which may be misplaced
    - as such, this code may not work as expected.

    Parameters:
    - angle
        - This is the desired angle of translation. It is measured
        anticlockwise in radians about the robot, where 0c means right.
    - forward_speed
    - right_speed
        - These two need to be be in correct proportion to each other
        (i.e. the ratio forward_speed/right_speed is correct) but the
        exact magnitudes do not matter.
    - translation_speed
        - Apologies, this is somewhat misleading. What I mean by this
        is the desired speed as a proportion of the maximum speed in
        the given direction (given by *angle*). It is intended to
        be a float in the range 0-1, but a given value of, say, 0.5,
        will result in different speeds in different directions.
        It is just used as a multiplier at the end.
    """
    # We will work out the desired mix of *FORWARD* and *RIGHT* based
    # on the intersection of two lines.
    # First, we will determine the gradient and intercept of the first
    # line. This line is of the form y = mx + c and is used to
    # correctly interpolate between forwards and rightwards motion.

    # Initialise the variables.
    gradient = 0
    intercept = 0

    # Wrap angle around if greater than 360 degrees (2 pi).
    angle %= 2*math.pi

    # Assign gradient and intercept their correct values.
    # You could probably split this out into two if-elses if
    # you wanted to; one for gradient and one for y-intercept.
    if 0 <= angle <= (math.pi/2):
        # 0-90 degrees.
        gradient = -(forward_speed/right_speed)
        intercept = forward_speed
    elif (math.pi/2) < angle <= math.pi:
        # 90-180 degrees.
        gradient = forward_speed/right_speed
        intercept = forward_speed
    elif math.pi < angle <= 3 * (math.pi/2):
        # 180-270 degrees.
        gradient = -(forward_speed/right_speed)
        intercept = -forward_speed
    else:
        # Must be 270-360 degrees.
        gradient = forward_speed/right_speed
        intercept = -forward_speed

    # The second line is that of y = (tan(*angle*))*x.
    # Here, we solve the equations to find the coordinates
    # at which they intersect (inlining could be a good idea here).
    x_intersect_coord = intercept / (math.tan(angle)-gradient)
    y_intersect_coord = math.tan(angle) * x_intersect_coord
    # Assuming the magnitudes of forward_speed and
    # right_speed are accurate, the magnitude of the resultant
    # speed may be found by the formula (x_intersect_coord ** 2 + y_intersect_coord ** 2) ** 0.5
    x_multiplier = x_intersect_coord / right_speed
    y_multiplier = y_intersect_coord / forward_speed
    # Set settings_arr.
    settings_arr = y_multiplier * FORWARD
    settings_arr += x_multiplier * RIGHT
    # At this point, settings_arr represents the motor settings
    # so as to achieve the maximum possible speed in the given
    # direction.
    # We now adjust it based on the desired speed.
    settings_arr *= translation_speed

    # Maybe we should clip to protect against values > 1 or < -1?
    # This shouldn't be necessary though, if everything's gone to plan.
    settings_arr = np.clip(settings_arr, -1, 1)

    return settings_arr
