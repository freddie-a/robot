"""
Goal: To interpret the BlockArray() returned from
pixy.ccc_get_blocks().
Date: 31.1.20
"""

import numpy as np
import pixy

COLOUR_SIGNATURES = {       # TODO determine actual ones.
    "red": 1,
    "green": 2,
    "blue": 3,
    "yellow": 4
}

def get_block_arrays(block_array, colours=None, max_blocks=100):
    """Return a list of blocks for each coloru in for *colours*.
    They are returned as a len(colours) array of arrays in
    the order specified. If colours is None, all signatures
    are returned.
    If no blocks are found, None is returned.
    Each item in each array takes the form:
        [x, y, width, height, index, age]

    Parameters:
        - block_array
            This is the BlockArray() needed to collect the blocks.
        - colours
            A list of all colour signatures needed.
        - max_blocks
            The maximum number of blocks fetched.
    WARNING: Not yet tested.
    """
    # Build signature mask.
    if colours is None:
        sig_mask = [True] * 10
    else:
        sig_mask = [False] * 10
        for colour in colours:
            sig_mask[colour] = True
    # Now proceed to collect data.
    no_blocks = pixy.ccc_get_blocks(max_blocks, block_array)
    if no_blocks == 0:
        return None
    # Set up lists.
    block_lists = [[]] * 10
    some_of_interest = False
    for i in range(no_blocks):
        sig = block_array[i].m_signature
        if sig_mask[sig]:
            some_of_interest = True
            block_lists[sig].append([
                    block_array[i].m_x,
                    block_array[i].m_y,
                    block_array[i].m_width,
                    block_array[i].m_height,
                    block_array[i].m_index,
                    block_array[i].m_age
                ]
            )
    if not some_of_interest:
        # Nothing of interest found.
        return None
    to_return = []
    for colour in colours:
        to_return.append(block_lists[colour])
    return to_return

def find_largest_block(array):
    """Return the largest block in the array of blocks."""
    print(array)
    best_size = 0
    best_index = 0
    for i in range(len(array)):
        size = array[i][2] * array[i][3]
        if size > best_size:
            best_size = size
            best_index = i
    return array[best_index]
