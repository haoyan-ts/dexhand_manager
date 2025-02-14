import numpy as np
from scipy.linalg import svd
import matplotlib.pyplot as plt


def calculate_rigid_transform(source_points, target_points):
    """
    Calculates the rigid transformation (rotation and translation) between two sets of 3D points.

    Args:
        source_points: The source points (3xN).
        target_points: The target points (3xN).

    Returns:
        rotation: The 3x3 rotation matrix.
        translation: The 3-element translation vector.
    """
    # Calculate centroids
    source_centroid = np.mean(source_points, axis=1, keepdims=True)
    target_centroid = np.mean(target_points, axis=1, keepdims=True)

    # Center the points
    centered_source = source_points - source_centroid
    centered_target = target_points - target_centroid

    # Calculate covariance matrix
    covariance_matrix = centered_source @ centered_target.T

    # Singular Value Decomposition (SVD)
    U, S, Vt = svd(covariance_matrix)

    # Calculate rotation
    rotation = Vt.T @ U.T

    # Check for reflection
    if np.linalg.det(rotation) < 0:
        Vt[:, 2] *= -1
        rotation = Vt.T @ U.T

    # Calculate translation
    translation = target_centroid - rotation @ source_centroid
    transformed_source = rotation @ source_points + translation

    # plot source and target points in each iteration
    # fig = plt.figure()
    # ax = fig.add_subplot(111, projection='3d')
    # ax.scatter(source_points[0], source_points[1], source_points[2], c='g', marker='x', label='Source')
    # ax.scatter(transformed_source[0], transformed_source[1], transformed_source[2], c='r', marker='o', label='TSource')
    # ax.scatter(target_points[0], target_points[1], target_points[2], c='b', marker='^', label='Target')
    # # ax.set_title(f'Iteration {iteration+1}')
    # ax.legend()
    # ax.set_xlim([-2, 2])
    # ax.set_ylim([-2, 2])
    # ax.set_zlim([-2, 2])
    # plt.show()

    return rotation, translation
