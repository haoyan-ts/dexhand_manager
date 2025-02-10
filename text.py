import numpy as np
from scipy.linalg import svd
from scipy.spatial import KDTree  # For efficient nearest neighbor search
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
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(source_points[0], source_points[1], source_points[2], c='g', marker='x', label='Source')
    ax.scatter(transformed_source[0], transformed_source[1], transformed_source[2], c='r', marker='o', label='TSource')
    ax.scatter(target_points[0], target_points[1], target_points[2], c='b', marker='^', label='Target')
    # ax.set_title(f'Iteration {iteration+1}')
    ax.legend()
    ax.set_xlim([-2, 2])
    ax.set_ylim([-2, 2])
    ax.set_zlim([-2, 2])
    plt.show()

    return rotation, translation


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
    t = np.zeros((3, 1))
    transform = np.eye(4)
    err = np.inf

    # source_points = source_points - rotation @ source_points + translation



    mse_old = np.inf

    for iteration in range(max_iterations):
        # 1. Find Closest Points (using KDTree)
        transformed_source = rotation @ source_points + translation
        # distances, closest_indices = target_tree.query(transformed_source.T) #query need (N,3)
        closest_indices = [0, 1, 2, 3]
        # closest_indices = closest_indices.tolist()

        C = target_points[:, closest_indices]

        new_rotation, new_translation = calculate_rigid_transform(transformed_source, C)

        # Check for convergence
        mse_new = np.mean((C - (new_rotation @ transformed_source + new_translation)) ** 2)
        err = mse_old - mse_new

        print(f"Iteration {iteration+1}: Error = {err:.6f}")


        if err < 0 or err < tolerance:
            break

        rotation = rotation @ new_rotation
        translation += new_translation
        t += translation
        mse_old = mse_new


    print(f"Converged after {iteration+1} iterations with error {err:.6f}")

    # Construct the 4x4 transformation matrix
    rotation = transform[:3, :3]
    translation = transform[:3, 3]

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
        [0, 0, 0]
    ], dtype=float)

    target_points_clone = np.copy(target_points)

    # Create 4 sets of test data, including noise, rotation, and translation
    # np.random.seed(0)
    # noise = 0.1 * np.random.randn(*target_points_clone.shape)
    # target_points_clone += noise

    # Define rotation matrices
    rotations = [
        np.eye(3),
        np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]]),
        np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]]),
        np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]])
    ]

    # Define translation vectors
    translations = [
        np.array([-2, 0, 0]),
        np.array([1, 1, 1]),
        np.array([2, 2, 2]),
        np.array([3, 3, 3])
    ]

    # Apply transformations to create test data
    test_data = []
    for i in range(2):
        rotated_points = target_points_clone @ rotations[i].T
        translated_points = rotated_points + translations[i]
        test_data.append(translated_points)

    # Choose one of the test data sets as the source points
    for i in range(2):
        source_points = test_data[i]

        print(f"\nTest Data Set {i+1}:")

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
        # print("\nEstimated Scale Factor:")
        # print(scale)

        # 3. Apply combined transformation

        transformed_source_points = source_points @ rotation.T + translation
        print("\nTarget Points:")
        print(target_points)
        print("\nTransformed Source Points:")
        print(transformed_source_points)

        # scaled_rotation = rotation * scale
        # transform_with_scale = np.eye(4)
        # transform_with_scale[:3,:3] = scaled_rotation
        # transform_with_scale[:3,3] = translation.flatten()


        # transformed_points = apply_transformation(target_points, transform_with_scale)
        # print("\nTransformed target Points:")
        # print(transformed_points)

        # Calculate RMSE
        # rmse = np.sqrt(np.mean((transformed_points - source_points)**2))
        # print(f"\nRMSE: {rmse}")
        # 4. (Optional) Construct Full Similarity Transformation Matrix

        # final_transform = np.copy(transform) # start with rigid transform
        # final_transform[:3,:3] *= scale

        # print("\nFinal Transformation Matrix (with Scale):")
        # print(final_transform)
