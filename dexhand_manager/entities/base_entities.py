import threading
import uuid

from ts.dexhand.v1.common_pb2 import ArmType, HandType, Side, Vector3
from . import DexHand
from models.mapping import LinearInterpModel
from repositories.error import RepositoryError, RepositoryAlreadyExistsError


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


class World(BaseEntity):
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

    _model: LinearInterpModel = LinearInterpModel()

    def __init__(self):
        self.name = f"Map[{self.id}]"
        super().__init__()

    def _validate(self):
        if self._model is None:
            self.is_set = False

    def set_vertex_targets(self, vertex_targets: list[list[float]]):
        for target in vertex_targets:
            if len(target) != self.joint_count:
                raise ValueError("Invalid vertex target.")

        self._validate()


class Session(BaseEntity):
    state = 0
    _lock = threading.RLock()

    world: World = World()
    dex_hands: dict[Side, DexHand] = {}

    def __init__(self):
        self.name = f"Session[{self.id}]"

        super().__init__()

    @staticmethod
    def create():
        return Session()

    def merge_from_dict(self, **kwargs):
        for key, item in kwargs.items():
            if key == "state":
                self.state = item

    def create_dex_hand(
        self, side: Side, arm_type: ArmType, hand_type: HandType
    ) -> DexHand:
        with self._lock:
            if side in self.dex_hands:
                raise RepositoryAlreadyExistsError(
                    f"DexHand already exists on the side: {Side.Name(side)}"
                )
            else:
                dex_hand = DexHand.create(side, arm_type, hand_type)

                self.dex_hands[dex_hand.side] = dex_hand

                return dex_hand

    def get_dex_hand(self, **kwargs) -> DexHand:
        if "side" in kwargs:
            dex_hand = self._get_dex_hand_by_side(kwargs["side"])
        elif "id" in kwargs:
            dex_hand = self._get_dex_hand_by_id(kwargs["id"])
        elif "name" in kwargs:
            dex_hand = self._get_dex_hand_by_name(kwargs["name"])
        else:
            raise RepositoryError("Invalid arguments.")

        if dex_hand is None:
            raise RepositoryError("DexHand does not exist.")
        else:
            return dex_hand

    def update_dex_hand(self, **kwargs):
        with self._lock:
            dex_hand = self.get_dex_hand(**kwargs)
            dex_hand.merge_from_dict(**kwargs)

    def _get_dex_hand_by_id(self, id: str):
        with self._lock:
            for dex_hand in self.dex_hands.values():
                if dex_hand.id == id:
                    return dex_hand
            return None

    def _get_dex_hand_by_name(self, name: str):
        with self._lock:
            for dex_hand in self.dex_hands.values():
                if dex_hand.name == name:
                    return dex_hand
            return None

    def _get_dex_hand_by_side(self, side: Side):
        with self._lock:
            return self.dex_hands.get(side, None)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            # "description": self.description,
            # "state": self.state,
            # "world": self.world.to_dict(),
            # "dex_hands": [dex_hand.to_dict() for dex_hand in self.dex_hands.values()],
        }
