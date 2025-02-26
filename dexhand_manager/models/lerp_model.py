import logging
from typing import Union

import numpy as np

LOG = logging.getLogger(__name__)


def hit_test(vertices: np.ndarray, point: np.ndarray) -> bool:
    l = to_barycentric(vertices, point)
    return all([0 <= l[i] <= 1 for i in range(4)])


def interpolate(
    vertices: np.ndarray, targets: np.ndarray, point: np.ndarray
) -> np.ndarray:
    LOG.info(
        f"Input vertices: {vertices.shape}, targets: {targets.shape}, point: {point.shape}"
    )

    l = to_barycentric(vertices, point).flatten()
    LOG.info(f"Interpolating: {l}")
    LOG.info(f"Targets: {targets.shape}")
    return np.array(
        l[0] * targets[0] + l[1] * targets[1] + l[2] * targets[2] + l[3] * targets[3]
    ).flatten()


def to_barycentric(vertices: np.ndarray, point: np.ndarray) -> np.ndarray:
    LOG.info(f"Vertices: {vertices.shape}, Point: {point.shape}")
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


class Simplex:
    vertex_indices: list[int]

    def __init__(self, indices: list[int]):
        self.vertex_indices = indices


class Vertex:
    values: np.ndarray  # 1x3
    target_group: np.ndarray  # 1xN

    def __init__(self, x, y, z):
        self.values = np.array([[x, y, z]])
        self.target_group = np.zeros((1,))


class LinearInterpModel:
    is_set: bool = False

    # simplex_vertices: np.ndarray

    vertices: list[Vertex]
    # targets: np.ndarray
    simplices: list[Simplex]

    name = ""
    can_interpolate = False
    target_dim: int = 0

    def __init__(self):
        self.vertices = [
            Vertex(-1, 1, 1),
            Vertex(1, 1, 1),
            Vertex(1, 1, -1),
            Vertex(-1, 1, -1),
            Vertex(-1, -1, 1),
            Vertex(1, -1, 1),
            Vertex(1, -1, -1),
            Vertex(-1, -1, -1),
        ]

        self.simplex_vertex_idxs = [
            [0, 1, 2, 5],
            [0, 2, 5, 7],
            [0, 4, 5, 7],
            [0, 2, 3, 7],
            [2, 5, 6, 7],
        ]

        self.simplices = [
            Simplex([0, 1, 2, 5]),
            Simplex([0, 2, 5, 7]),
            Simplex([0, 4, 5, 7]),
            Simplex([0, 2, 3, 7]),
            Simplex([2, 5, 6, 7]),
        ]

        # self.targets = np.zeros((8, 6))
        # self.target_dim = 6

        # self.simplices = []
        # for idx_array in self.simplex_vertex_idxs:
        #     simplex = Simplex()
        #     LOG.info(f"Simplex vertices: {simplex.vertices.shape}")
        #     simplex.vertices = np.array([self.vertices[idx] for idx in idx_array])
        #     self.simplices.append(simplex)

        # self.simplex_vertices = np.array(simplex_vertices)
        # LOG.info(f"Simplex vertices: {self.simplex_vertices.shape}")

    def set_targets(self, targets: np.ndarray):
        if not (targets.shape[0] != 8):

            raise ValueError("Targets must be a 8xN array.")

        self.targets = targets
        self.target_dim = targets.shape[1]
        self.can_interpolate = True

    def set_target(self, vertex_idx: int, targets: np.ndarray):
        LOG.info(f"Setting target into Vertex {vertex_idx}, {targets}, {targets.shape}")
        if not (targets.shape[0] == 1):
            raise ValueError("Targets must be a 1xN array.")

        self.vertices[vertex_idx].target_group = targets

        if all([v.target_group.size > 0 for v in self.vertices]):
            # self.targets = np.array([v.targets for v in self.vertices])
            self.can_interpolate = True
            LOG.info(f"All targets set.")

    # def hit_test(self, point: np.ndarray):
    #     for vertices in self.simplex_vertices:
    #         if hit_test(vertices, point):
    #             return True
    #     return False

    def interpolate(self, point: np.ndarray):
        if not self.can_interpolate:
            raise ValueError("Targets must be set before interpolation.")

        for simplex in self.simplices:
            # LOG.info(f"Idx: {idx}, Vertices: {vertices}, Targets: {self.targets[idx]}")
            vertices = np.array(
                [self.vertices[idx].values.flatten() for idx in simplex.vertex_indices]
            )
            target_groups = np.array(
                [
                    self.vertices[idx].target_group.flatten()
                    for idx in simplex.vertex_indices
                ]
            )

            LOG.info(f"Vertices: {vertices}, Target Groups: {target_groups}")
            if hit_test(vertices, point):
                return interpolate(vertices, target_groups, point)

        raise ValueError("Point is not within the convex hull of the vertices.")
