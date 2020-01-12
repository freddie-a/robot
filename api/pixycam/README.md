# Pixy Cam shenanigans

I (Max) have tried (mostly succesfully) to connect a pixy cam to a rasberry pi. Here are my findings:

2 useful tutorials:

1. <https://docs.pixycam.com/wiki/doku.php?id=wiki:v2:building_libpixyusb_as_a_python_module_on_linux> tells you all about how to use python with the pixy cam
2. <https://docs.pixycam.com/wiki/doku.php?id=wiki:v2:hooking_up_pixy_to_a_raspberry_pi> is much the same thing, but on a more broad basis (doens't talk about python much)

These are both tell you everything that I have learned pretty much, but here it is anyway (mostly for my purposes)

## My conclusions (which you can get from the above tutorials...)

* Clone the github library <https://github.com/charmedlabs/pixy2> to get started. It has most of what you need (you need to install git first to do this)
* You will also need various other things (I think that they are called dependencies?) which you get using `apt-get install`. These are:
..* libusb-1.0-0-dev
..* g++
..* build_essential
..* swig
* Now, you can build the python thingymabob...
..* Go into the directory pixy2/scrips
..* Run ./build_whatever... (in this case ./build_python_demos.sh
..* This will create a folder called python_demos in /pixy2/build/
..* Now you can run some of the python demos (get_blocks_python_demo.py seems to be most useful to us)

That's pretty much it ¯\\_(ツ)_/¯

## What to do now?

We can use the important files in python_demos/ to provide the basis for our pixy cam API (for example pixy.py and _pixy.so. Subsequently, we can look at the demo get_blocks_python_demo.py as our basis for creating our python API. It seems to import pixy.py and use that for things (which we can do too)

Basically, we would rewrite get_blocks_python_demo.py so that we can use it properly as an API

Also, we need to get the dependcies (still not sure on the name) on the actualy Pi we will be using, which will allow us to use the python code.

As far as I am aware, the only other things needed on the actualy pi that we are using is going to be those neccesary files in python_demos which I allready talked about (not the whole of github.com/charmedlabs/pixy2)

That's as far as I got

:)
