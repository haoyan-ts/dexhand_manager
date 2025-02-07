import open3d as o3d
import numpy as np

def icp_calibration(points_B, points_S):
    """
    Performs ICP registration to find the transformation from the sensor frame (S) to the robot base frame (B).

    Args:
        points_B: A numpy array of shape (N, 3) representing the points in the robot's base frame.
        points_S: A numpy array of shape (N, 3) representing the points in the sensor's frame.

    Returns:
        T_B_to_S: A 4x4 numpy array representing the transformation matrix.
    """

    # Convert to Open3D point clouds
    pcd_B = o3d.geometry.PointCloud()
    pcd_B.points = o3d.utility.Vector3dVector(points_B)
    pcd_S = o3d.geometry.PointCloud()
    pcd_S.points = o3d.utility.Vector3dVector(points_S)

    # Initial guess (identity matrix - can be improved if you have a rough estimate)
    init_transform = np.eye(4)

    # ICP parameters (tune these for your setup)
    threshold = 0.02  # Distance threshold for point correspondence
    max_iteration = 100  # Maximum number of iterations

    # Perform ICP registration
    reg_p2p = o3d.pipelines.registration.registration_icp(
        pcd_S, pcd_B, threshold, init_transform,
        o3d.pipelines.registration.TransformationEstimationPointToPoint(),
        o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=max_iteration))

    # Get the transformation matrix
    T_B_to_S = reg_p2p.transformation

    return T_B_to_S


if __name__ == '__main__':
    # Example Usage (replace with your actual data)
    source_points = np.array([
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
        [1, 1, 1]
    ], dtype=float)

    # Test Case 1: Target points are scaled, rotated, and translated
    target_points_1 = np.array([
        [4, 2, 0],  # Shifted by (2,2,0), rotated, and scaled by 2
        [2, 4, 0],
        [2, 2, 2],
        [4, 4, 2]
    ], dtype=float)
    # points_B = np.array([[...], [...], ...]) # Your robot base frame points
    # points_S = np.array([[...], [...], ...]) # Your sensor frame points, calculated by multiplying a "zero position" by quaternion

    T_B_to_S = icp_calibration(source_points, target_points_1)
    print(T_B_to_S)

