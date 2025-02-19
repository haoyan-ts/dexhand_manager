import logging
import threading
import uuid
from typing import Optional, Union

from models.mapping import LinearInterpModel
from models.arm_control import PiperArm
from models.inspire_hand import InspireHand
from ts.dexhand.v1.common_pb2 import ArmType, HandType, Side
from ts.dexhand.v1.dexhand_service_pb2 import DexHand as DexHandProto

LOG = logging.getLogger(__name__)


class DexHandController:
    _lock: threading.RLock = threading.RLock()

    id: str
    name: str = ""
    side: Side = Side.SIDE_UNSPECIFIED
    arm_type: ArmType = ArmType.ARM_TYPE_UNSPECIFIED
    hand_type: HandType = HandType.HAND_TYPE_UNSPECIFIED

    _arm: Union[PiperArm, None]
    _hand: Union[InspireHand, None]

    _use_ik: bool = False
    _lerp: Optional[LinearInterpModel]
    _ik: Optional[None]

    def __init__(
        self, side: Side, arm_type: ArmType, hand_type: HandType, use_ik=False
    ):
        self.side = side
        self.arm_type = arm_type
        self.hand_type = hand_type
        self._use_ik = use_ik

        self.id = str(uuid.uuid4())
        self.name = (
            f"{Side.Name(side)}_{ArmType.Name(arm_type)}_{HandType.Name(hand_type)}"
        )

        self._setup_arm()
        self._setup_hand()

        if not self._use_ik:
            self._lerp = LinearInterpModel()
        else:
            self._ik = None

    def _setup_arm(self):
        if self.arm_type == ArmType.ARM_TYPE_PIPER:
            self._arm = PiperArm()
        elif self.arm_type == ArmType.ARM_TYPE_NOVA:
            raise NotImplementedError("Nova arm is not implemented yet.")
        else:
            raise ValueError(f"Invalid arm type: {self.arm_type}")

    def _setup_hand(self):
        if self.hand_type == HandType.HAND_TYPE_INSPIRE:
            self._hand = InspireHand()
        elif self.hand_type == HandType.HAND_TYPE_DH:
            raise NotImplementedError("DH hand is not implemented yet.")
        else:
            raise ValueError(f"Invalid hand type: {self.hand_type}")

    def connect(self):
        with self._lock:
            self.__validate_instances()

            assert self._arm is not None
            assert self._hand is not None

            try:
                self._arm.connect()
                # self.hand.connect()
            except Exception as e:
                raise Exception(f"Failed to connect to devices: {e}")

    def disconnect(self):
        with self._lock:
            self.__validate_instances()

            assert self._arm is not None
            assert self._hand is not None

            try:
                self._arm.disconnect()
                # self.hand.connect()
            except Exception as e:
                raise Exception(f"Failed to disconnect to devices: {e}")

    def enable(self):
        with self._lock:
            self.__validate_instances()

            assert self._arm is not None
            assert self._hand is not None

            try:
                self._arm.enable()
                # self.hand.connect()
            except Exception as e:
                raise Exception(f"Failed to enable devices: {e}")

    def disable(self):
        with self._lock:
            self.__validate_instances()

            assert self._arm is not None
            assert self._hand is not None

            try:
                self._arm.disable()
                # self.hand.connect()
            except Exception as e:
                raise Exception(f"Failed to disable devices: {e}")

    def move_j(self, joints: list[float]):
        with self._lock:
            self.__validate_instances()

            assert self._arm is not None
            assert self._hand is not None

            try:
                # move to joints
                self._arm.move_j(joints)
            except Exception as e:
                raise Exception(f"Failed to move to joints: {e}")

    def move_p(self, pose: list[float]):
        with self._lock:
            if self._use_ik:
                self.move_p_ik(pose)
            else:
                self._move_p_lerp(pose)

    def move_p_ik(self, pose: list[float]):
        with self._lock:
            self.__validate_instances()

            assert self._arm is not None
            assert self._hand is not None

            try:
                # move to pose
                # self._arm.move_p(pose)s
                if self._use_ik:
                    # self._arm.move_p_ik(pose)
                    pass
                else:
                    pass
            except Exception as e:
                raise Exception(f"Failed to move to pose: {e}")

    def _move_p_lerp(self, pose: list[float]):
        with self._lock:
            self.__validate_instances()

            assert self._arm is not None
            assert self._hand is not None

            try:
                # move to pose
                # self._arm.move_p(pose)s
                if self._use_ik:
                    # self._arm.move_p_ik(pose)
                    pass
                else:
                    pass
            except Exception as e:
                raise Exception(f"Failed to move to pose: {e}")

    def get_status(self):
        with self._lock:
            self.__validate_instances()

            assert self._arm is not None
            assert self._hand is not None

            try:
                # get status
                return {"arm": "dummy"}
                # return self._arm.get_status()
            except Exception as e:
                raise Exception(f"Failed to get status: {e}")

    def __validate_instances(self):
        if self._arm is None:
            raise Exception("Arm is not set.")
        if self._hand is None:
            raise Exception("Hand is not set.")

    def to_proto(self):
        with self._lock:
            return DexHandProto(
                id=self.id,
                name=self.name,
                side=self.side,
                arm_type=self.arm_type,
                hand_type=self.hand_type,
            )
