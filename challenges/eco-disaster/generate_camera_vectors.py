#!/usr/bin/env python3
"""
Goal: To generate an array of camera vectors, where each
vector represents the direction of one pixel in the in the
camera's image.

Date: 22.1.20.
"""

import math

import numpy as np

# GENERAL SUBROUTINES

def make_unit_2d(vectors):
    """Make each vector in the array a unit vector (inplace).

    Works on 3D arrays of 3D vectors.
    """
    for i in range(vectors.shape[0]):
        for j in range(vectors.shape[1]):
            # Divide by magnitude.
            vectors[i][j] /= (vectors[i][j][0]**2
                              + vectors[i][j][1]**2
                              + vectors[i][j][2]**2) ** 0.5

# CREATING VECTORS

def get_camera_vectors(fov, resolution):
    """Return the vectors of each pixel in the camera's view.

    Returns the vector, relative to the camera where the y-axis
    points directly away from the camera, that describes the way
    each pixel in the camera's vision points.
    """
    vector_array = np.empty(shape=(resolution[0], resolution[1], 3),
                            dtype=np.float64)
    # Work out appropriate *distance_from_cam* to ensure fov.
    half_width = resolution[0] / 2
    distance_from_cam = half_width / math.tan(math.pi * fov / 360)
    # Fill with values.
    for i in range(resolution[0]):
        for j in range(resolution[1]):
            vector_array[i][j][0] = i
            vector_array[i][j][1] = distance_from_cam
            vector_array[i][j][2] = -j
    # Centre the vectors around the point (0, distance_from_cam, 0).
    vector_array += np.array([-resolution[0]/2, 0, resolution[1]/2], dtype=np.float64)
    make_unit_2d(vector_array)
    return vector_array

def main():
    """Main function; generate and save array."""
    fov = int(input("What is the horizontal fov of the camera? (degrees): "))
    res_width = int(input("What is its horizontal resolution?: "))
    res_height = int(input("What is its vertical resolution?: "))
    resolution = np.array([res_width, res_height], dtype=np.int64)
    vector_array = get_camera_vectors(fov, resolution)
    print("Vectors generated; saving array as camera_vectors.npy")
    np.save("camera_vectors", vector_array)
    print("Array saved.")

if __name__ == "__main__":
    main()
