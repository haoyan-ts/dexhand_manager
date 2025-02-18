import uuid

from arm_control import PiperArm
from inspire_hand import InspireHand

from ts.dexhand.v1.dexhand_service_pb2 import DexHandConfig, DexHand
from ts.dexhand.v1.common_pb2 import Side, ArmType, HandType


class DexHandEntity:
    id = ""
    name = ""
    side = Side.SIDE_UNSPECIFIED
    arm_type = ArmType.ARM_TYPE_UNSPECIFIED
    hand_type = HandType.HAND_TYPE_UNSPECIFIED

    arm = None
    hand = None

    def __init__(self):
        self.id = str(uuid.uuid4())

    def create(self, config: DexHandConfig):
        kwargs = {
            "side": config.side,
            "arm_type": config.arm_type,
            "hand_type": config.hand_type,
        }
        self._update_from_dict(**kwargs)

        self._create_arm()
        self._create_hand()

    def update(self, dex_hand: DexHand):
        kwargs = {
            "side": dex_hand.side,
            "arm_type": dex_hand.arm_type,
            "hand_type": dex_hand.hand_type,
        }

        self._update_from_dict(**kwargs)

    def _update_from_dict(self, **kwargs):
        for key, item in kwargs.items():
            if key == "side":
                self._update_side(item)
            elif key == "arm_type":
                self._update_arm_type(item)
            elif key == "hand_type":
                self._update_hand_type(item)

        self.name = (
            ArmType.Name(self.arm_type)
            + "_"
            + HandType.Name(self.hand_type)
            + "_"
            + Side.Name(self.side)
        )

    def _update_side(self, side: Side):
        if side == Side.SIDE_UNSPECIFIED:
            raise ValueError("Side cannot be unspecified.")
        else:
            self.side = side

    def _update_arm_type(self, arm_type: ArmType):
        if arm_type == ArmType.ARM_TYPE_UNSPECIFIED:
            raise ValueError("Arm type cannot be unspecified.")
        else:
            self.arm_type = arm_type

    def _update_hand_type(self, hand_type: HandType):
        if hand_type == HandType.HAND_TYPE_UNSPECIFIED:
            raise ValueError("Hand type cannot be unspecified.")
        else:
            self.hand_type = hand_type

    def _create_arm(self):
        if self.arm_type == ArmType.ARM_TYPE_PIPER:
            self.arm = PiperArm()
            # self.arm.connect()
        else:
            raise ValueError(f"Invalid arm type: {self.arm_type}")

    def _create_hand(self):
        if self.hand_type == HandType.HAND_TYPE_INSPIRE:
            self.hand = InspireHand()
        else:
            raise ValueError(f"Invalid hand type: {self.hand_type}")

    def __str__(self):
        return f"id: {self.id}, side: {self.side}, arm_type: {self.arm_type}, hand_type: {self.hand_type}"

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "side": self.side,
            "arm_type": self.arm_type,
            "hand_type": self.hand_type,
        }
