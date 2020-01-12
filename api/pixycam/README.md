#Pixy Cam shenanigans

I (Max) have tried (mostly succesfully) to connect a pixy cam to a rasberry pi. Here are my findings:

2 useful tutorials:

1. <https://docs.pixycam.com/wiki/doku.php?id=wiki:v2:building_libpixyusb_as_a_python_module_on_linux> tells you all about how to use python with the pixy cam
2. <https://docs.pixycam.com/wiki/doku.php?id=wiki:v2:hooking_up_pixy_to_a_raspberry_pi> is much the same thing, but on a more broad basis (doens't talk about python much)

These are both tell you everything that I have learned pretty much, but here it is anyway (mostly for my purposes):

* Clone the github library <https://github.com/charmedlabs/pixy2> to get started. It has most of what you need (you need to install git first to do this)
* You will also need various other things (I think that they are called dependencies?) which you get using `apt-get install`. These are:
..* libusb-1.0-0-dev
..* g++
..* build_essential
* Now, you can build the python thingymabob...
