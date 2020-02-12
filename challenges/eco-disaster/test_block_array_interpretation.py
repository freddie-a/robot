"""
Goal: To test block-fetching and angle prediction.

Date: 1.2.20.
"""

import pixy

import block_array_interpretation

def format_zeros(integer):
    """Make the integer width three by padding with 0s."""
    if integer < 10:
        return "0" * 2 + str(integer)
    elif integer < 100:
        return "0" + str(integer)
    else:
        return str(integer)

def print_largest(signature, blocks):
    """Collect and print the data for the largest block."""
    block_array = block_array_interpretation.get_block_arrays(
        blocks, colours=[signature,]
    )
    if block_array is not None:
        largest = block_array_interpretation.find_largest_block(block_array[0])
        x, y = largest[0], largest[1]
        width, height = largest[2], largest[3]
        print("Largest block:")
        print("\tx, y          : ")
        print(format_zeros(x), format_zeros(y))
        print("\twidth, height : ")
        print(format_zeros(width), format_zeros(height))

def main():
    """Run the test."""
    pixy.init()
    pixy.change_prog("color_connected_components")
    requested_signature = int(
        input("What colour signature do you want to use?: ")
    )
    blocks = pixy.BlockArray(100)
    while True:
        print_largest(requested_signature, blocks)
