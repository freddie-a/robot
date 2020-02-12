# Eco-disaster

Hi there! I just thought I'd create a _readme_ to organise any thoughts, relevant information, and things to do for this challenge.

## The challenge

As of yet, we __don't know how many barrels there will be__, but we do have the relevant dimensions:

![Eco Disaster Layout](https://i0.wp.com/piwars.org/wp-content/uploads/2019/07/EcoDisasterPlanLabelled.png?ssl=1)

## Progress

##### Crucial points:
- [x] Interface with pixycam (Max).
- [x] Work out how to use Pixy API (Max again).
- [x] Work out how to estimate pixel directions.
- [ ] Make a pushing-attachment.
    * I don't think either of us has much knowledge of how to do this. We might have to beg for help.
- [ ] Interface with servo.
    * I don't know who's doing this. It might be us. It might not be. I'm not really very sure.
- [ ] Work out where barrels are relative to robot.
- [ ] Work out how to safely rotate out of start box.
- [ ] Work out **the plan** (i.e. *how we're actually going to collect the right barrels* and put them in the right place).

##### Coding:
- [x] Estimate pixel directions.
- [ ] Test program for pixel direction estimations.
- [ ] Test program for object tracking.
- [ ] Work out where objects are, given the direction of their centre from the camera.
- [ ] Reliably keep track of said information between frames, as well as metadata to keep track of how high quality this estimation is.
- [ ] Rotation.
- [ ] Make the robot do the right things.

##### Testing:
- [ ] Test pixel direction estimations.
- [ ] Test object tracking (maybe rotate to follow object?).
- [ ] Test pushing attachment.
    * Does it work?
    * Does it push over the barrels (hoping *not*?)
- [ ] Test barrel collection along a line of barrels.
- [ ] Test rotation out of starting spot.
- [ ] Test the whole thing together.

##### Current roadblocks
- We don't know if we're making the attachment.
- We don't know if we're making the servo work with the camera.

## What are all those files?
##### generate_camera_vectors.py:
This generates an array of camera vectors, in which each vector represents one pixel, and the direction we think it points relative to the camera.
##### camera_vectors.npy:
Refer to the above. It is in the form of a saved numpy array of shape (320, 200).
##### <span>code</span>.py:
I honestly don't know.
##### detect_colour.py
A link. We're not currently using it, since we're using the PixyCam's own built in detection.
Here it is: https://www.pyimagesearch.com/2014/08/04/opencv-python-color-detection/
