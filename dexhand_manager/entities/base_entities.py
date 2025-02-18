import uuid

from ts.dexhand.v1.common_pb2 import Vector3
from entities.dexhand_entity import DexHandEntity


class BaseEntity(object):
    id = ""
    name = ""
    description = ""

    def __init__(self):
        self.id = str(uuid.uuid4())

    def __str__(self):
        return f"id: {self.id}, name: {self.name}, description: {self.description}"

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {"id": self.id, "name": self.name, "description": self.description}


class WorldEntity(BaseEntity):
    is_set: bool = False
    coordinates: dict[str, Vector3] = {}

    def __init__(self):
        self.name = f"World[{self.id}]"
        super().__init__()

    def set_coordinates(self, coordinates: dict[str, Vector3]):
        if coordinates.keys() != ["x", "y", "z"]:
            raise ValueError("Invalid input coordinates.")
        else:
            self.coordinates = coordinates
            self.is_set = True


class MapEntity(BaseEntity):
    is_set: bool = False
    joint_count: int = 0

    _mapping = None

    def __init__(self):
        self.name = f"Map[{self.id}]"
        super().__init__()

    def _validate(self):
        if self._mapping is None:
            self.is_set = False

    def set_vertex_targets(self, vertex_targets: list[list[float]]):
        for target in vertex_targets:
            if len(target) != self.joint_count:
                raise ValueError("Invalid vertex target.")

        self._validate()


class SessionEntity(BaseEntity):
    state = 0

    world: WorldEntity
    map: MapEntity
    dex_hand: DexHandEntity

    def __init__(self):
        self.name = f"Session[{self.id}]"

        super().__init__()

        self.world = WorldEntity()
        self.map = MapEntity()
        self.dex_hand = DexHandEntity()
