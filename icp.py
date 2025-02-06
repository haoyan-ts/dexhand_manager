import numpy as np
from scipy.linalg import svd
from scipy.spatial import KDTree  # For efficient nearest neighbor search

def standard_icp(source_points, target_points, max_iterations=100, tolerance=1e-6):
    """
    Performs standard Iterative Closest Point (ICP) registration (rigid body).

    Args:
        source_points: A numpy array of shape (N, 3) representing the source point cloud.
        target_points: A numpy array of shape (N, 3) representing the target point cloud.
        max_iterations: The maximum number of iterations.
        tolerance: The convergence tolerance (change in rotation and translation).

    Returns:
        transform: A 4x4 numpy array representing the rigid transformation matrix (T_B_to_S).
        rotation: The 3x3 rotation matrix.
        translation: The 3-element translation vector.
    """

    # Check input
    if source_points.shape[0] != target_points.shape[0] or source_points.shape[0] < 3:
        raise ValueError("Point sets must have the same size and at least 3 points.")

    num_points = source_points.shape[0]
    source_points = source_points.T  # Make them 3xN
    target_points = target_points.T

    # Build KDTree for target points (for efficient nearest neighbor search)
    target_tree = KDTree(target_points.T)

    # Initialize transformation
    rotation = np.eye(3)
    translation = np.zeros((3, 1))
    transform = np.eye(4)

    for iteration in range(max_iterations):
        # 1. Find Closest Points (using KDTree)
        transformed_target = rotation @ target_points + translation
        distances, closest_indices = target_tree.query(transformed_target.T) #query need (N,3)
        closest_indices = closest_indices.tolist()


        # 2. Calculate Centroids
        source_centroid = np.mean(source_points, axis=1, keepdims=True)
        target_centroid = np.mean(target_points[:, closest_indices], axis=1, keepdims=True)

        # 3. Calculate Covariance Matrix
        covariance_matrix = (source_points - source_centroid) @ (target_points[:, closest_indices] - target_centroid).T

        # 4. Singular Value Decomposition (SVD)
        U, S, Vt = svd(covariance_matrix)

        # 5. Calculate Rotation
        V = Vt.T
        new_rotation = V @ U.T

        # Check for reflection
        if np.linalg.det(new_rotation) < 0:
            V[:, 2] *= -1
            new_rotation = V @ U.T

        # 6. Calculate Translation
        new_translation = source_centroid - new_rotation @ target_centroid

        # Check for convergence
        rotation_change = np.linalg.norm(new_rotation - rotation)
        translation_change = np.linalg.norm(new_translation - translation)

        rotation = new_rotation
        translation = new_translation

        if rotation_change < tolerance and translation_change < tolerance:
            break

    # Construct the 4x4 transformation matrix
    transform[:3, :3] = rotation
    transform[:3, 3] = translation.flatten()

    return transform, rotation, translation


def estimate_scale(source_points, target_points, transformation_matrix):
    """
    Estimates the scale factor after applying a rigid transformation.

    Args:
        source_points:  The original source points (N, 3).
        target_points: The original target points (N, 3).
        transformation_matrix: The 4x4 rigid transformation matrix from standard ICP.

    Returns:
        scale: The estimated scale factor.
    """
    rotation = transformation_matrix[:3, :3]
    translation = transformation_matrix[:3, 3]

    transformed_target_points = (rotation @ target_points.T + translation.reshape(3,1)).T

    # Calculate distances from centroids for both point clouds
    source_centroid = np.mean(source_points, axis=0)
    target_centroid = np.mean(transformed_target_points, axis=0)


    source_distances = np.linalg.norm(source_points - source_centroid, axis=1)
    target_distances = np.linalg.norm(transformed_target_points - target_centroid, axis=1)

    # Estimate scale (average ratio of distances)
    # Avoid division by zero and handle potential outliers by using a robust estimator (median)
    ratios = source_distances / (target_distances + 1e-8)  # Add small epsilon to avoid division by zero
    scale = np.median(ratios) # robust than mean

    return scale
def apply_transformation(points, transform):
    """Applies a 4x4 transformation matrix to a set of 3D points."""
    homogeneous_points = np.hstack([points, np.ones((points.shape[0], 1))])
    transformed_points = (transform @ homogeneous_points.T).T
    return transformed_points[:, :3]

if __name__ == '__main__':
    # Example Usage:
    # Create some sample point clouds (replace with your actual data)
    target_points = np.array([
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
        [1, 1, 1]
    ], dtype=float)

    # Target points are scaled, rotated, and translated
    source_points = np.array([
        [4.1, 2.1, 0.1],  # Shifted, rotated, and scaled
        [2.1, 4.1, 0.1],
        [2.1, 2.1, 2.1],
        [4.1, 4.1, 2.1]
    ], dtype=float)

    # 1. Perform Standard ICP (Rigid Body)
    transform, rotation, translation = standard_icp(source_points, target_points)

    # 2. Estimate Scale
    scale = estimate_scale(source_points, target_points, transform)
    print("Transformation Matrix (Rigid):")
    print(transform)
    print("\nRotation Matrix:")
    print(rotation)
    print("\nTranslation Vector:")
    print(translation)
    print("\nEstimated Scale Factor:")
    print(scale)

    # 3. Apply combined transformation

    scaled_rotation = rotation * scale
    transform_with_scale = np.eye(4)
    transform_with_scale[:3,:3] = scaled_rotation
    transform_with_scale[:3,3] = translation.flatten()


    transformed_points = apply_transformation(target_points, transform_with_scale)
    print("\nTransformed target Points:")
    print(transformed_points)

    # Calculate RMSE
    rmse = np.sqrt(np.mean((transformed_points - source_points)**2))
    print(f"\nRMSE: {rmse}")
    # 4. (Optional) Construct Full Similarity Transformation Matrix

    final_transform = np.copy(transform) # start with rigid transform
    final_transform[:3,:3] *= scale

    print("\nFinal Transformation Matrix (with Scale):")
    print(final_transform)