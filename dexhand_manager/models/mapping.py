from typing import Union

import numpy as np


class Vertex:
    array = np.atleast_2d([0, 0, 0])
    name = ""
    x: float
    y: float
    z: float
    target: Union[np.ndarray, None] = None
    has_target = False

    def __init__(self, x, y, z, name=""):
        self.array = np.atleast_2d([x, y, z])

        self.x = x
        self.y = y
        self.z = z

    def set_target(self, target):
        self.target = np.atleast_2d(target)
        self.has_target = True

    def reset_target(self):
        self.has_target = False
        self.target = None

    def __str__(self):
        return f"({self.x}, {self.y}, {self.z})"


class Simplex:
    vertices: list[Vertex] = []
    name = ""

    def __init__(self, vertices):
        self.vertices = vertices

    def __str__(self):
        return f"{self.vertices}"

    def to_barycentric(self, point: np.ndarray):
        """
        Converts a given point in 3D space to its barycentric coordinates with respect to the tetrahedron
        formed by the vertices of the object.
        Parameters:
        point (np.ndarray): A 3D point represented as a numpy array of shape (3,).
        Returns:
        np.ndarray: A numpy array of shape (4,) representing the barycentric coordinates of the point.

        x = l1 * a[0] + l2 * b[0] + l3 * c[0] + l4 * d[0]
        y = l1 * a[1] + l2 * b[1] + l3 * c[1] + l4 * d[1]
        z = l1 * a[2] + l2 * b[2] + l3 * c[2] + l4 * d[2]
        1 = l1 + l2 + l3 + l4
        lambda = [l1, l2, l3, l4]
        p = [x, y, z, 1]

        """

        a = self.vertices[0].array
        b = self.vertices[1].array
        c = self.vertices[2].array
        d = self.vertices[3].array

        p = np.array([point[0], point[1], point[2], 1])

        A = np.array(
            [
                [a[0], b[0], c[0], d[0]],
                [a[1], b[1], c[1], d[1]],
                [a[2], b[2], c[2], d[2]],
                [1, 1, 1, 1],
            ]
        )

        l = np.linalg.solve(A, p)

        return l

    def hit_test(self, point: np.ndarray):
        l = self.to_barycentric(point)
        return all([0 <= l[i] <= 1 for i in range(4)])


class LinearInterpModel:
    is_set: bool = False
    simplices: list[Simplex] = []
    vertices: list[Vertex] = []
    name = ""
    can_interpolate = False

    @staticmethod
    def CreateDefaultComplex():
        vertices = [
            Vertex(-1, 1, 1),
            Vertex(1, 1, 1),
            Vertex(1, 1, -1),
            Vertex(-1, 1, -1),
            Vertex(-1, -1, 1),
            Vertex(1, -1, 1),
            Vertex(1, -1, -1),
            Vertex(-1, -1, -1),
        ]

        simplices = [
            Simplex([vertices[0], vertices[2], vertices[5], vertices[1]]),
            Simplex([vertices[0], vertices[2], vertices[5], vertices[3]]),
            Simplex([vertices[0], vertices[5], vertices[7], vertices[4]]),
            Simplex([vertices[2], vertices[5], vertices[7], vertices[6]]),
            Simplex([vertices[0], vertices[2], vertices[5], vertices[7]]),
        ]

        return LinearInterpModel().config(vertices, simplices)

    def config(self, vertices, simplices):
        self.vertices = vertices
        self.simplices = simplices

        return self

    def _validate(self):
        for simplex in self.simplices:
            for vertex in simplex.vertices:
                if not vertex.has_target:
                    self.can_interpolate = False
                    return

        self.can_interpolate = True

    def hit_test(self, point: np.ndarray):
        for simplex in self.simplices:
            if simplex.hit_test(point):
                return True
        return False

    def interpolate(self, point: np.ndarray):
        if not self.can_interpolate:
            return None

        for simplex in self.simplices:
            if simplex.hit_test(point):
                return simplex.to_barycentric(point)

        return None

    def set_targets(self, targets: list[list[float]]):
        for v, tgt in zip(self.vertices, targets):
            v.set_target(tgt)

        self.can_interpolate = True
