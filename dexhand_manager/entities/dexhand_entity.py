import logging
from typing import Union
import uuid

from repositories.error import RepositoryError
from models.arm_control import PiperArm
from models.inspire_hand import InspireHand
from ts.dexhand.v1.common_pb2 import ArmType, HandType, Side

LOG = logging.getLogger(__name__)


class DexHand:
    id = ""
    name = ""
    side = Side.SIDE_UNSPECIFIED
    arm_type = ArmType.ARM_TYPE_UNSPECIFIED
    hand_type = HandType.HAND_TYPE_UNSPECIFIED

    arm: Union[PiperArm, None]
    hand: Union[InspireHand, None]

    def __init__(self):
        self.id = str(uuid.uuid4())

    @staticmethod
    def create(side, arm_type, hand_type):
        dexhand = DexHand()
        dexhand.merge_from_dict(side=side, arm_type=arm_type, hand_type=hand_type)
        dexhand.setup()
        return dexhand

    def connect(self):
        if self.arm is None:
            raise RepositoryError("Arm is not set.")
        if self.hand is None:
            raise RepositoryError("Hand is not set.")

        try:
            self.arm.connect()
            # self.hand.connect()
        except Exception as e:
            raise RepositoryError(f"Failed to connect to devices: {e}")

    def setup(self):
        self._setup_arm()
        self._setup_hand()

    def merge_from_dict(self, **kwargs):
        for key, item in kwargs.items():
            if key == "side":
                self._update_side(item)
            elif key == "arm_type":
                self._update_arm_type(item)
            elif key == "hand_type":
                self._update_hand_type(item)

        self._validate_name()

    def _validate_name(self):
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
            if self.arm_type != arm_type:
                self.arm_type = arm_type
                self._setup_arm()
                LOG.info(f"Arm type updated to {ArmType.Name(self.arm_type)}.")

    def _update_hand_type(self, hand_type: HandType):
        if hand_type == HandType.HAND_TYPE_UNSPECIFIED:
            raise ValueError("Hand type cannot be unspecified.")
        else:
            if self.hand_type != hand_type:
                self.hand_type = hand_type
                self._setup_hand()
                LOG.info(f"Hand type updated to {HandType.Name(self.hand_type)}.")

    def _setup_arm(self):
        if self.arm_type == ArmType.ARM_TYPE_PIPER:
            self.arm = PiperArm()
        elif self.arm_type == ArmType.ARM_TYPE_NOVA:
            raise NotImplementedError("Nova arm is not implemented yet.")
        else:
            raise ValueError(f"Invalid arm type: {self.arm_type}")

    def _setup_hand(self):
        if self.hand_type == HandType.HAND_TYPE_INSPIRE:
            self.hand = InspireHand()
        elif self.hand_type == HandType.HAND_TYPE_DH:
            raise NotImplementedError("DH hand is not implemented yet.")
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
