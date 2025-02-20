from typing import Union

import numpy as np


def hit_test(vertices: np.ndarray, point: np.ndarray) -> bool:
    l = to_barycentric(vertices, point)
    return all([0 <= l[i] <= 1 for i in range(4)])


def interpolate(vertices: np.ndarray, point: np.ndarray) -> np.ndarray:
    l = to_barycentric(vertices, point)
    return (
        l[0] * vertices[0].target
        + l[1] * vertices[1].target
        + l[2] * vertices[2].target
        + l[3] * vertices[3].target
    )


def to_barycentric(vertices: np.ndarray, point: np.ndarray) -> np.ndarray:
    if not vertices.shape == (4, 3):
        raise ValueError("Vertices must be a 4x3 array.")
    if not point.shape == (3,):
        raise ValueError("Point must be a 3D point.")

    a = np.array([vertices[0, 0], vertices[0, 1], vertices[0, 2]])
    b = np.array([vertices[1, 0], vertices[1, 1], vertices[1, 2]])
    c = np.array([vertices[2, 0], vertices[2, 1], vertices[2, 2]])
    d = np.array([vertices[3, 0], vertices[3, 1], vertices[3, 2]])

    p = np.array([point[0], point[1], point[2], 1])

    A = np.array(
        [
            [a[0], b[0], c[0], d[0]],
            [a[1], b[1], c[1], d[1]],
            [a[2], b[2], c[2], d[2]],
            [1, 1, 1, 1],
        ]
    )

    return np.linalg.solve(A, p)


class LinearInterpModel:
    is_set: bool = False

    simplex_vertices: np.ndarray

    vertices: np.ndarray
    targets: np.ndarray

    name = ""
    can_interpolate = False
    target_dim: int = 0

    def __init__(self):
        self.vertices = np.array(
            [
                [-1, 1, 1],
                [1, 1, 1],
                [1, 1, -1],
                [-1, 1, -1],
                [-1, -1, 1],
                [1, -1, 1],
                [1, -1, -1],
                [-1, -1, -1],
            ]
        )
        self.simplex_vertex_idxs = [
            [0, 1, 2, 5],
            [0, 2, 5, 7],
            [0, 4, 5, 7],
            [0, 2, 3, 7],
            [2, 5, 6, 7],
        ]

        self.targets = np.array([])

        simplex_vertices = []
        for idx_array in self.simplex_vertex_idxs:
            for idx in idx_array:
                simplex_vertices.append(self.vertices[idx])
        self.simplex_vertices = np.array(simplex_vertices)

    def set_targets(self, targets: np.ndarray):
        if not (targets.shape[0] == 8 and targets.shape.count == 2):
            raise ValueError("Targets must be a 8xN array.")

        self.targets = targets
        self.target_dim = targets.shape[1]
        self.can_interpolate = True

    def hit_test(self, point: np.ndarray):
        for vertices in self.simplex_vertices:
            if hit_test(vertices, point):
                return True
        return False

    def interpolate(self, point: np.ndarray):
        if not self.can_interpolate:
            raise ValueError("Targets must be set before interpolation.")

        for vertices in self.simplex_vertices:
            if hit_test(vertices, point):
                return interpolate(vertices, point)

        raise ValueError("Point is not within the convex hull of the vertices.")
