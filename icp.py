import numpy as np
from scipy.linalg import svd
from scipy.spatial import KDTree  # For efficient nearest neighbor search

def standard_icp(source_points: np.ndarray, reference_points: np.ndarray, max_iterations=10000, tolerance=1e-6):
    """
    Performs standard Iterative Closest Point (ICP) registration (rigid body).

    Args:
        source_points: A numpy array of shape (N, 3) representing the source point cloud.
        reference_points: A numpy array of shape (N, 3) representing the reference point cloud.
        max_iterations: The maximum number of iterations.
        tolerance: The convergence tolerance (change in rotation and translation).

    Returns:
        transform: A 4x4 numpy array representing the rigid transformation matrix (T_B_to_S).
        rotation: The 3x3 rotation matrix.
        translation: The 3-element translation vector.
    """

    # Check input
    if source_points.shape[0] != reference_points.shape[0] or source_points.shape[0] < 3:
        raise ValueError("Point sets must have the same size and at least 3 points.")

    num_points = source_points.shape[0]
    source_points = source_points.T  # Make them 3xN
    reference_points = reference_points.T

    # Build KDTree for reference points (for efficient nearest neighbor search)
    reference_tree = KDTree(reference_points.T)

    # Initialize transformation
    rotation = np.eye(3)
    translation = np.zeros((3, 1))
    transform = np.eye(4)

    source_points = rotation @ source_points + translation

    for iteration in range(max_iterations):
        # 1. Find Closest Points (using KDTree)
        distances, closest_indices = reference_tree.query(source_points.T) #query need (N,3)
        closest_indices: np.ndarray = closest_indices.tolist()

        # closest_reference_points = reference_points[closest_indices, :]
        closest_reference_points = np.array([reference_points[:, i] for i in closest_indices]).T

        # Debug: Print closest points
        # print(f"Iteration {iteration + 1}: Closest Reference Points:\n{closest_reference_points}")

        # 2. Calculate Centroids
        source_centroid = np.mean(source_points, axis=1, keepdims=True)
        closest_reference_centroid = np.mean(closest_reference_points, axis=1, keepdims=True)

        # Debug: Print centroids
        # print(f"Source Centroid:\n{source_centroid.T}")
        # print(f"Closest Reference Centroid:\n{closest_reference_centroid.T}")

        # 3. Calculate Covariance Matrix
        # covariance_matrix = (source_points - source_centroid).T @ (closest_reference_points - closest_reference_centroid)
        # covariance_matrix = np.cov((source_points - source_centroid), (closest_reference_points - closest_reference_centroid))

        cov = (source_points - source_centroid) @ (closest_reference_points - closest_reference_centroid).T
        # Debug: Print covariance matrix
        # print(f"Covariance Matrix:\n{covariance_matrix}")

        # 4. Singular Value Decomposition (SVD)
        U, S, Vt = svd(cov)

        # 5. Calculate Rotation
        V = Vt.T
        new_rotation = V @ U.T

        # Check for reflection
        if np.linalg.det(new_rotation) < 0:
            V[:, 2] *= -1
            new_rotation = V @ U.T

        # Debug: Print new rotation matrix
        # print(f"New Rotation Matrix:\n{new_rotation}")

        # 6. Calculate Translation
        new_translation = closest_reference_centroid - new_rotation @ source_centroid

        # Debug: Print new translation vector
        # print(f"New Translation Vector:\n{new_translation.T}")

        # Apply transformation to source points
        new_source_points = new_rotation @ source_points + new_translation

        mse_old = np.mean((reference_points - source_points)**2)
        mse_new = np.mean((reference_points - new_source_points)**2)

        mse_change = mse_old - mse_new

        print(f"\rIteration {iteration + 1}/{max_iterations}, Change of MSE: {mse_change:.10f}", end="")

        if (mse_change < tolerance):
            break
        
        rotation = new_rotation.T
        translation = new_translation
        transform[:3, :3] = rotation
        transform[:3, 3] = translation.flatten()
        source_points = new_source_points

    if iteration == max_iterations - 1:
        print("\n")
        print("ICP did not converge!")

    # Construct the 4x4 transformation matrix
    transform[:3, :3] = rotation
    transform[:3, 3] = translation.flatten()

    return transform, rotation, translation


def estimate_scale(source_points, reference_points, transformation_matrix):
    """
    Estimates the scale factor after applying a rigid transformation.

    Args:
        source_points:  The original source points (N, 3).
        reference_points: The original reference points (N, 3).
        transformation_matrix: The 4x4 rigid transformation matrix from standard ICP.

    Returns:
        scale: The estimated scale factor.
    """
    rotation = transformation_matrix[:3, :3]
    translation = transformation_matrix[:3, 3]

    transformed_reference_points = (rotation @ reference_points.T + translation.reshape(3,1)).T

    # Calculate distances from centroids for both point clouds
    source_centroid = np.mean(source_points, axis=0)
    reference_centroid = np.mean(transformed_reference_points, axis=0)


    source_distances = np.linalg.norm(source_points - source_centroid, axis=1)
    reference_distances = np.linalg.norm(transformed_reference_points - reference_centroid, axis=1)

    # Estimate scale (average ratio of distances)
    # Avoid division by zero and handle potential outliers by using a robust estimator (median)
    ratios = source_distances / (reference_distances + 1e-8)  # Add small epsilon to avoid division by zero
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
    reference_points = np.array([
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
        [1, 1, 1],
        [0, 0, 0]
    ], dtype=float)

    # Test Case 1: Rotate 45 degrees around Z-axis and translate by (1, 1, 0)
    angle = np.pi / 4  # 45 degrees
    rotation_matrix = np.array([
        [np.cos(angle), -np.sin(angle), 0],
        [np.sin(angle), np.cos(angle), 0],
        [0, 0, 1]
    ])
    source_points_1 = (rotation_matrix @ reference_points.T).T + np.array([1, 1, 0])

    # Test Case 2: Rotate 90 degrees around Z-axis and translate by (2, 2, 0)
    angle = np.pi / 2  # 90 degrees
    rotation_matrix = np.array([
        [np.cos(angle), -np.sin(angle), 0],
        [np.sin(angle), np.cos(angle), 0],
        [0, 0, 1]
    ])
    source_points_2 = (rotation_matrix @ reference_points.T).T + np.array([2, 2, 0])

    # Test Case 3: Rotate 30 degrees around Z-axis and translate by (0, 0, 1)
    angle = np.pi / 6  # 30 degrees
    rotation_matrix = np.array([
        [np.cos(angle), -np.sin(angle), 0],
        [np.sin(angle), np.cos(angle), 0],
        [0, 0, 1]
    ])
    source_points_3 = (rotation_matrix @ reference_points.T).T + np.array([0, 0, 1])

    # Test Case 4: Rotate 60 degrees around Z-axis and translate by (-1, -1, 0)
    angle = np.pi / 3  # 60 degrees
    rotation_matrix = np.array([
        [np.cos(angle), -np.sin(angle), 0],
        [np.sin(angle), np.cos(angle), 0],
        [0, 0, 1]
    ])
    source_points_4 = (rotation_matrix @ reference_points.T).T + np.array([-1, -1, 0])

    # # Test Case 1: Target points are scaled, rotated, and translated
    # source_points_1 = np.array([
    #     [4, 2, 0],  # Shifted by (2,2,0), rotated, and scaled by 2
    #     [2, 4, 0],
    #     [2, 2, 2],
    #     [4, 4, 2]
    # ], dtype=float)

    # # Test Case 2: Target points are only translated
    # source_points_2 = np.array([
    #     [3, 1, -1],  # Shifted by (2,1,-1)
    #     [1, 3, -1],
    #     [1, 1, 1],
    #     [3, 3, 1]
    # ], dtype=float)

    # # Test Case 3: Target points are only scaled
    # source_points_3 = np.array([
    #     [2, 0, 0],  # Scaled by 2
    #     [0, 2, 0],
    #     [0, 0, 2],
    #     [2, 2, 2]
    # ], dtype=float)

    # # Test Case 4: Target points are rotated and translated
    # angle = np.pi / 4  # 45 degrees
    # rotation_matrix = np.array([
    #     [np.cos(angle), -np.sin(angle), 0],
    #     [np.sin(angle), np.cos(angle), 0],
    #     [0, 0, 1]
    # ])
    # source_points_4 = (rotation_matrix @ reference_points.T).T + np.array([1, 1, 0])

    test_cases = [source_points_1, source_points_2, source_points_3, source_points_4]

    for i, source_points in enumerate(test_cases):
        print(f"\nTest Case {i+1}:")

        transform, rotation, translation = standard_icp(source_points, reference_points)
        # scale = estimate_scale(source_points, reference_points, transform)
        print("\n")
        print("Transformation Matrix:")
        print(transform)
        print("\nRotation Matrix:")
        print(rotation)
        print("\nTranslation Vector:")
        print(translation)
        # print("\nScale Factor:")
        # print(scale)

        # Apply the transformation to the source points
        transformed_source_points = (rotation @ source_points.T + translation).T
        print("Reference Points:")
        print(reference_points)
        print("\nTransformed Source Points:")
        print(transformed_source_points)

        # Apply the transformation to the reference points
        # transformed_points = apply_transformation(reference_points, transform)
        # print("\nTransformed Target Points:")
        # print(transformed_points)

        # Calculate RMSE
        # rmse = np.sqrt(np.mean((transformed_source_points - reference_points)**2))
        # print(f"\nRMSE: {rmse}")

        # Construct Full Similarity Transformation Matrix
        final_transform = np.copy(transform)  # start with rigid transform
        # final_transform[:3, :3] *= scale

        print("\nFinal Transformation Matrix (with Scale):")
        print(final_transform)